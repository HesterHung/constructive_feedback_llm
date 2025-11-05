import requests
import json
import os 

# --- Configuration ---
MODEL = "tngtech/deepseek-r1t-chimera:free" 
SITE_URL = "<YOUR_SITE_URL>" 
SITE_NAME = "<YOUR_SITE_NAME>"
TODO_LIST_FILE = "output/list_todo_feedback.json" 
R1_INPUT_DOC = "inputs/input_r1_original.json" # <-- MODIFIED: Added this
R2_INPUT_DOC = "inputs/my_r2_submission.json" 
R2_VERIFICATION_FILE = "output/round_2_verification.json" 
PROMPT_DIR = "prompts" # <-- MODIFIED
API_KEY_FILE = "api_key.json"
OUTPUT_DIR = "output" 
# PROMPT_FILE = "prompt.json" # <-- REMOVED

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
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("--- 1. LOADING R2 FILES ---")
    try:
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            API_KEY = json.load(f)['api_key']
        
        # --- MODIFIED BLOCK: Load all prompts and original doc ---
        with open(os.path.join(PROMPT_DIR, "round_2_verify.txt"), "r", encoding="utf-8") as f:
            verify_prompt_template = f.read()
        with open(os.path.join(PROMPT_DIR, "round_2_no_changes.txt"), "r", encoding="utf-8") as f:
            no_changes_prompt_template = f.read()
        
        with open(TODO_LIST_FILE, "r", encoding="utf-8") as f:
            current_todo_list = json.load(f)
            
        with open(R1_INPUT_DOC, "r", encoding="utf-8") as f:
            doc_r1_original = json.load(f)['project_proposal']
        
        with open(R2_INPUT_DOC, "r", encoding="utf-8") as f:
            doc_r2_submission = json.load(f)['project_proposal']
        # --- END MODIFIED BLOCK ---
            
    except FileNotFoundError as e:
        print(f"Error: Missing file! {e.filename} not found.")
        print(f"Did you run 'run_round_1.py' first and create '{R2_INPUT_DOC}'?")
        print("Make sure your 'prompts' folder has 'round_2_verify.txt' and 'round_2_no_changes.txt'.")
        return

    print("\n--- 2. VERIFYING YOUR SUBMISSION ---")
    
    # --- MODIFIED BLOCK: Check for changes and select prompt ---
    # We strip whitespace to make sure only meaningful text changes are caught
    player_made_no_changes = (doc_r1_original.strip() == doc_r2_submission.strip())
    
    if player_made_no_changes:
        print("Detected no changes in submission. Using 'no_changes' prompt...")
        prompt_template = no_changes_prompt_template
    else:
        print("Detected changes in submission. Using 'verify' prompt...")
        prompt_template = verify_prompt_template
    
    r2_content = prompt_template.format(
        current_todo_list=json.dumps(current_todo_list, indent=2),
        revised_document=doc_r2_submission
    )
    # --- END MODIFIED BLOCK ---
    
    r2_messages = [{"role": "user", "content": r2_content}]
    
    round_2_response_str = call_openrouter(r2_messages, MODEL, API_KEY)
    
    if round_2_response_str.startswith("Error:"):
        print(f"R2 failed: {round_2_response_str}")
        return

    print("R2 verification received, parsing complex JSON...")

    try:
        start_index = round_2_response_str.find('{')
        end_index = round_2_response_str.rfind('}')
        if start_index == -1 or end_index == -1:
            raise json.JSONDecodeError("Could not find '{' or '}' in LLM output.", round_2_response_str, 0)
        
        json_text = round_2_response_str[start_index : end_index + 1]
        verification_data = json.loads(json_text)
        
        # --- 3. PROCESS THE LLM'S RESPONSE ---
        
        summary = verification_data.get("verification_summary", "Error: No summary provided by AI.")
        with open(R2_VERIFICATION_FILE, "w", encoding="utf-8") as f:
            json.dump({"verification_feedback": summary}, f, indent=2, ensure_ascii=False)
        
        updated_tasks = verification_data.get("updated_task_list", current_todo_list)
        new_task_strings = verification_data.get("new_tasks_to_add", [])
        
        # Check if any tasks are still unresolved
        all_tasks_resolved = True
        for task in updated_tasks:
            task_status = task.get("status", "Pending").lower()
            if task_status not in ["implemented", "abandoned"]:
                all_tasks_resolved = False
                break
        
        if all_tasks_resolved:
            print("All tasks resolved! Adding new tasks from AI.")
            max_id = 0
            if updated_tasks:
                max_id = max(item.get('id', 0) for item in updated_tasks)
            
            for new_task_text in new_task_strings:
                max_id += 1
                updated_tasks.append({
                    "id": max_id,
                    "task": new_task_text,
                    "status": "Pending"
                })
        elif new_task_strings: 
            print("Pending tasks remain. New tasks from AI will be held until all current tasks are resolved.")

        # OVERWRITE the master to-do list with the updated version
        with open(TODO_LIST_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_tasks, f, indent=2, ensure_ascii=False)

        print(f"\n--- 4. SUCCESS! ---")
        print(f"Your verification summary is saved in '{R2_VERIFICATION_FILE}'.")
        print(f"Your master to-do list '{TODO_LIST_FILE}' has been updated!")
        print("\n--- YOUR TURN (AGAIN) ---")
        print("1. Open both output files to see your results.")
        print("2. Make more changes to 'inputs/my_r2_submission.json'.")
        print(f"3. When ready, just run 'run_round_2.py' again!")

    except json.JSONDecodeError as e:
        print(f"Error: LLM did not return valid JSON for R2. {e.msg}")
        print(f"--- Raw LLM Output (for debugging) ---")
        print(round_2_response_str)
        print("------------------------------------------")

if __name__ == "__main__":
    run_round_2()