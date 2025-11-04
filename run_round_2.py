import requests
import json
import os

# --- Configuration ---
MODEL = "tngtech/deepseek-r1t-chimera:free" 
SITE_URL = "<YOUR_SITE_URL>" 
SITE_NAME = "<YOUR_SITE_NAME>"
R1_FEEDBACK_FILE = "outputs/round_1_feedback.json" # R1 "memory"
R2_INPUT_DOC = "inputs/my_r2_submission.json" # Your new work
R2_OUTPUT_FILE = "outputs/round_2_verification.json"
PROMPT_FILE = "prompt.json"
API_KEY_FILE = "api_key.json"
OUTPUT_DIR = "outputs"

# --- API Helper Function (Same as R1) ---
def call_openrouter(messages, model, api_key):
    print(f"Calling API for model: {model}...")
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": SITE_URL,
                "X-Title": SITE_NAME,
            },
            data=json.dumps({"model": model, "messages": messages})
        )
        response.raise_for_status()
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        return reply
    except Exception as e:
        print(f"API Request Failed: {e}")
        return f"Error: API request failed. {e}"

# --- Main R2 Script ---
def run_round_2():
    print("--- 1. LOADING R2 FILES ---")
    try:
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            API_KEY = json.load(f)['api_key']
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            prompts = json.load(f)
        
        # Load the R1 to-do list (the AI's "memory")
        with open(R1_FEEDBACK_FILE, "r", encoding="utf-8") as f:
            round_1_todo_list = json.load(f)
            
        # Load your new R2 submission
        with open(R2_INPUT_DOC, "r", encoding="utf-8") as f:
            doc_r2_submission = json.load(f)['project_proposal']
            
    except FileNotFoundError as e:
        print(f"Error: Missing file! {e.filename} not found.")
        print(f"Did you run 'run_round_1.py' first and create '{R2_INPUT_DOC}'?")
        return

    print("\n--- 2. VERIFYING YOUR R2 SUBMISSION ---")
    
    r2_content = prompts["round_2_verify_prompt"].format(
        round_1_todo_list=json.dumps(round_1_todo_list, indent=2),
        revised_document=doc_r2_submission
    )
    
    r2_messages = [{"role": "user", "content": r2_content}]
    
    round_2_verification = call_openrouter(r2_messages, MODEL, API_KEY)
    
    if round_2_verification.startswith("Error:"):
        print(f"R2 failed: {round_2_verification}")
        return

    print("\n--- 3. SUCCESS! ---")
    print(f"Your Round 2 verification has been saved to '{R2_OUTPUT_FILE}'.")
    print("Open the file to see how you did!")
    
    # Save the verification feedback
    output_data = {"verification_feedback": round_2_verification}
    with open(R2_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    run_round_2()