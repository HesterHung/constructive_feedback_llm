import requests
import json

# Load the input JSON
with open("input_writing.json", "r", encoding="utf-8") as f:
    writings = json.load(f)

# Load the API key
with open("api_key.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Load the tone options
with open("prompt.json", "r", encoding="utf-8") as f:
    prompt_data = json.load(f)

# Show tone options to user
print("Choose a tone:")
for i, tone in enumerate(prompt_data["tone"], start=1):
    print(f"{i}. {tone}")

choice = int(input("Enter 1 or 2: ").strip())

# Validate choice
if choice < 1 or choice > len(prompt_data["tone"]):
    raise ValueError("Invalid choice")

selected_tone = prompt_data["tone"][choice - 1]
print(f"Using tone: {selected_tone}")

feedback = {}

for key, text in writings.items():
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {data['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional
            "X-Title": "<YOUR_SITE_NAME>",      # Optional
        },
        data=json.dumps({
            "model": "tngtech/deepseek-r1t2-chimera:free",
            "messages": [
                {
                    "role": "user",
                    "content": f"Please provide feedback on this writing (be {selected_tone}): {text}"
                }
            ],
        })
    )

    result = response.json()

    # Extract assistant reply safely
    try:
        reply = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        reply = "Error: no feedback returned."

    feedback[key] = reply

# Save the feedback JSON
with open("reponse_feedback.json", "w", encoding="utf-8") as f:
    json.dump(feedback, f, indent=2, ensure_ascii=False)

print("Feedback written to reponse_feedback.json")