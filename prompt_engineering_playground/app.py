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


# --- API Helper Function ---
def call_openrouter(messages, model):
    """
    Sends a request to the OpenRouter API and returns the raw content.
    """
    print(f"Calling model: {model}...")
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

# --- The Main API Endpoint (UPGRADED) ---
@app.route("/run-prompt", methods=["POST"])
def run_prompt():
    """
    This endpoint now accepts multipart/form-data
    It looks for text fields and an optional file.
    """
    # We now read from request.form (for text) and request.files (for files)
    system_prompt = request.form.get("system_prompt", "")
    user_prompt = request.form.get("user_prompt")
    model = request.form.get("model")
    pdf_file = request.files.get("pdf_file") # Get the PDF file

    if not user_prompt or not model:
        return jsonify({"error": "Missing 'user_prompt' or 'model'"}), 400

    # 1. Extract PDF text if it exists
    pdf_text = ""
    if pdf_file:
        pdf_text = extract_text_from_pdf(pdf_file)

    # 2. Construct the final prompt
    final_user_prompt = user_prompt
    if pdf_text:
        # We prepend the PDF content to the user's prompt
        final_user_prompt = f"--- PDF CONTENT ---\n{pdf_text}\n\n--- USER PROMPT ---\n{user_prompt}"

    # 3. Construct the messages list
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": final_user_prompt})

    # 4. Call the AI
    ai_response = call_openrouter(messages, model)

    return jsonify({"response": ai_response})

# --- Run the Server ---
if __name__ == "__main__":
    print("Starting Flask server for prompt engineering (with PDF support)...")
    print("Visit http://127.0.0.1:5000 in your browser.")
    app.run(port=5000, debug=True)