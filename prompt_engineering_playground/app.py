import requests
import json
import os
import io # Used to handle the file stream
from PyPDF2 import PdfReader # Used to read PDF text
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Configuration ---
try:
    with open("api_key.json", "r", encoding="utf-8") as f:
        API_KEY = json.load(f)['api_key']
except FileNotFoundError:
    print("FATAL ERROR: api_key.json not found.")
    exit()

SITE_URL = "<YOUR_SITE_URL>" 
SITE_NAME = "<YOUR_SITE_NAME>"

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) 

# --- PDF Helper Function ---
def extract_text_from_pdf(pdf_file_stream):
    """
    Extracts text from a PDF file stream.
    """
    try:
        # Create a in-memory stream
        pdf_stream = io.BytesIO(pdf_file_stream.read())
        # Open the PDF
        reader = PdfReader(pdf_stream)
        text = ""
        # Loop through all pages and extract text
        for page in reader.pages:
            text += page.extract_text() or "" # Add page text, or empty string if it fails
        
        print(f"Successfully extracted {len(text)} characters from PDF.")
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return f"Error: Could not read PDF. {e}"


# --- API HelperFunction ---
def call_openrouter(messages, model):
    """
    Sends a request to the OpenRouter API and returns the raw content.
    """
    print(f"Calling model: {model} with {len(messages)} messages...")
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": model,
                "messages": messages,
            })
        )
        response.raise_for_status() 
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        return reply
    except Exception as e:
        print(f"API Request Failed: {e}")
        return f"Error: API request failed. {e}"

# --- The Main API Endpoint (UPGRADED FOR CHAT) ---
@app.route("/run-prompt", methods=["POST"])
def run_prompt():
    """
    This endpoint is now stateful.
    It accepts a 'messages' history and a 'new_user_message'.
    It returns the *complete, updated* message history.
    """
    # 1. Get data from the form
    model = request.form.get("model")
    
    # Get the message history (as a JSON string) and the new message
    messages_json = request.form.get("messages", "[]")
    new_user_message = request.form.get("new_user_message")
    
    pdf_file = request.files.get("pdf_file") # Get the PDF file

    if not new_user_message or not model:
        return jsonify({"error": "Missing 'new_user_message' or 'model'"}), 400

    try:
        # 2. Load the message history
        messages = json.loads(messages_json)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid 'messages' JSON provided."}), 400

    # 3. Extract PDF text if it exists
    pdf_text = ""
    if pdf_file:
        pdf_text = extract_text_from_pdf(pdf_file)
        if "Error:" in pdf_text:
            # If PDF extraction fails, inform the user
            messages.append({"role": "user", "content": new_user_message})
            messages.append({"role": "assistant", "content": f"I'm sorry, I couldn't read that PDF. {pdf_text}"})
            return jsonify({"messages": messages})

    # 4. Construct the final user message (with PDF content)
    final_user_content = new_user_message
    if pdf_text:
        # We prepend the PDF content to the user's prompt
        final_user_content = f"--- PDF CONTENT ---\n{pdf_text}\n\n--- USER PROMPT ---\n{new_user_message}"

    # 5. Append the new user message to the history
    messages.append({"role": "user", "content": final_user_content})

    # 6. Call the AI
    try:
        ai_response_content = call_openrouter(messages, model)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # 7. Append the AI's response to the history
    messages.append({"role": "assistant", "content": ai_response_content})

    # 8. Return the *complete* updated history
    return jsonify({"messages": messages})

# --- Run the Server ---
if __name__ == "__main__":
    print("Starting Flask server for prompt engineering (with PDF support)...")
    print("Visit http://127.0.0.1:5000 in your browser.")
    app.run(port=5000, debug=True)