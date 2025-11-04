import requests
import json
import os

# --- Configuration ---
MODEL = "tngtech/deepseek-r1t-chimera:free" 
SITE_URL = "<YOUR_SITE_URL>" 
SITE_NAME = "<YOUR_SITE_NAME>"
R1_INPUT_DOC = "inputs/input_r1_original.json"
R1_OUTPUT_FILE = "outputs/round_1_feedback.json" # Your to-do list
PROMPT_FILE = "prompt.json"
API_KEY_FILE = "api_key.json"
OUTPUT_DIR = "outputs"

# --- API Helper Function ---
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

# --- Main R1 Script ---
def run_round_1():
    print("--- 1. LOADING R1 FILES ---")
    try:
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            API_KEY = json.load(f)['api_key']
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            prompts = json.load(f)
        with open(R1_INPUT_DOC, "r", encoding="utf-8") as f:
            doc_r1_original = json.load(f)['project_proposal']
    except FileNotFoundError as e:
        print(f"Error: Missing file! {e.filename} not found.")
        return

    print("\n--- 2. GENERATING ROUND 1 FEEDBACK ---")
    
    r1_content = prompts["round_1_prompt"].format(proposal=doc_r1_original)
    r1_messages = [{"role": "user", "content": r1_content}]
    
    round_1_feedback_str = call_openrouter(r1_messages, MODEL, API_KEY)
    
    if round_1_feedback_str.startswith("Error:"):
        print(f"R1 failed: {round_1_feedback_str}")
        return

    print("R1 feedback received, attempting to parse JSON...")
    
    try:
        # Clean up potential markdown code blocks from LLM
        if "```json" in round_1_feedback_str:
             round_1_feedback_str = round_1_feedback_str.split("```json", 1)[1].rsplit("```", 1)[0].strip()
        
        round_1_todo_list = json.loads(round_1_feedback_str)
        
        # Save the to-do list
        with open(R1_OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(round_1_todo_list, f, indent=2, ensure_ascii=False)
            
        print(f"\n--- 3. SUCCESS! ---")
        print(f"Your Round 1 to-do list has been saved to '{R1_OUTPUT_FILE}'.")
        print("\n--- YOUR TURN ---")
        print(f"1. Open '{R1_OUTPUT_FILE}' to see your feedback.")
        print(f"2. Create a *new file* named 'inputs/my_r2_submission.json' (you can copy the original).")
        print(f"3. Make your changes in 'inputs/my_r2_submission.json' to address the feedback.")
        print(f"4. When you are ready, run 'run_round_2.py' to get your next round of feedback.")
        
    except json.JSONDecodeError as e:
        print(f"Error: LLM did not return valid JSON for R1. {e}")
        print(f"Raw LLM Output: {round_1_feedback_str}")

if __name__ == "__main__":
    run_round_1()