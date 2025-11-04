import requests
import json

# Load the input JSON
with open("input_writing.json", "r", encoding="utf-8") as f:
    writings = json.load(f)

# Load the API key
with open("api_key.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Load the prompt data
with open("prompt.json", "r", encoding="utf-8") as f:
    prompt_data = json.load(f)

# Pair each character with its corresponding tone
character_tone_pairs = list(zip(prompt_data["character"], prompt_data["tone"]))

feedback = {}

for key, text in writings.items():
    feedback[key] = {}
    for character, tone in character_tone_pairs:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {data['api_key']}",
                "Content-Type": "application/json",
                "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional
                "X-Title": "<YOUR_SITE_NAME>",      # Optional
            },
            data=json.dumps({
                "model": "tngtech/deepseek-r1t-chimera:free",
                "messages": [
                    {
                        "role": "user",
                        "content": f"You are {character}. Please provide feedback on this writing (be {tone}): {text}"
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

        feedback[key][character.split(":")[0]] = reply  # Use character name as key

# Save the feedback JSON
with open("reponse_feedback.json", "w", encoding="utf-8") as f:
    json.dump(feedback, f, indent=2, ensure_ascii=False)

print("Feedback written to reponse_feedback.json")