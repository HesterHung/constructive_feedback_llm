import requests
import json
import os 

# --- Configuration ---
MODEL = "tngtech/deepseek-r1t-chimera:free" 
SITE_URL = "<YOUR_SITE_URL>" 
SITE_NAME = "<YOUR_SITE_NAME>"
R1_INPUT_DOC = "inputs/input_r1_original.json"
TODO_LIST_FILE = "output/list_todo_feedback.json" 
PROMPT_DIR = "prompts" # <-- MODIFIED
API_KEY_FILE = "api_key.json"
OUTPUT_DIR = "output" 
# PROMPT_FILE = "prompt.json" # <-- REMOVED

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
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("--- 1. LOADING R1 FILES ---")
    try:
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            API_KEY = json.load(f)['api_key']
        
        # --- MODIFIED BLOCK ---
        with open(os.path.join(PROMPT_DIR, "round_1.txt"), "r", encoding="utf-8") as f:
            prompt_template = f.read()
        # --- END MODIFIED BLOCK ---
            
        with open(R1_INPUT_DOC, "r", encoding="utf-8") as f:
            doc_r1_original = json.load(f)['project_proposal']
            
    except FileNotFoundError as e:
        print(f"Error: Missing file! {e.filename} not found.")
        print("Make sure you have an 'api_key.json' file, 'inputs/input_r1_original.json', and a 'prompts/round_1.txt' file.")
        return

    print("\n--- 2. GENERATING ROUND 1 FEEDBACK ---")
    
    r1_content = prompt_template.format(proposal=doc_r1_original) # <-- MODIFIED
    r1_messages = [{"role": "user", "content": r1_content}]
    
    round_1_feedback_str = call_openrouter(r1_messages, MODEL, API_KEY)
    
    if round_1_feedback_str.startswith("Error:"):
        print(f"R1 failed: {round_1_feedback_str}")
        return

    print("R1 feedback received, attempting to parse JSON...")
    
    try:
        start_index = round_1_feedback_str.find('[')
        end_index = round_1_feedback_str.rfind(']')
        
        if start_index == -1 or end_index == -1:
            raise json.JSONDecodeError("Could not find '[' or ']' in LLM output.", round_1_feedback_str, 0)
        
        json_text = round_1_feedback_str[start_index : end_index + 1]
        round_1_todo_list = json.loads(json_text)
        
        processed_list = []
        for item in round_1_todo_list:
            item['status'] = 'Pending' 
            processed_list.append(item)

        with open(TODO_LIST_FILE, "w", encoding="utf-8") as f:
            json.dump(processed_list, f, indent=2, ensure_ascii=False)
            
        print(f"\n--- 3. SUCCESS! ---")
        print(f"Your new to-do list has been saved to '{TODO_LIST_FILE}'.")
        print("\n--- YOUR TURN ---")
        print(f"1. Open '{TODO_LIST_FILE}' to see your feedback.")
        print(f"2. Create 'inputs/my_r2_submission.json'.")
        print(f"3. Make your changes in that file.")
        print(f"4. When ready, run 'run_round_2.py'.")
        
    except json.JSONDecodeError as e:
        print(f"Error: LLM did not return valid JSON for R1. {e.msg}")
        print(f"--- Raw LLM Output (for debugging) ---")
        print(round_1_feedback_str)
        print("------------------------------------------")

if __name__ == "__main__":
    run_round_1()