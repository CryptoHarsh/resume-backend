import os
import requests
from flask import Flask, request, jsonify

# Setup Flask App
app = Flask(__name__)

# --- FINAL FIX: Manually add the permission headers after each request ---
@app.after_request
def after_request(response):
    # This line explicitly allows your frontend to make requests.
    response.headers.add('Access-Control-Allow-Origin', 'https://resume-frontend-k6zm.onrender.com')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# This is now the ONLY job of the backend
@app.route('/format-resume-ai', methods=['POST', 'OPTIONS'])
def format_resume_with_ai():
    # The browser sends an 'OPTIONS' request first to check permissions.
    # We need to respond to it with a success code (200).
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # If it's not an OPTIONS request, it's the real 'POST' request.
    try:
        data = request.get_json()
        if not data or 'cleanedText' not in data:
            return jsonify({"error": "Missing cleanedText in request"}), 400
            
        cleaned_text = data['cleanedText']

        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return jsonify({"error": "API key is not configured on the server."}), 500

        prompt = f"""
You are an expert-level resume parser and formatter... 
[Your full prompt here, it does not need to change]
[START OF CLEANED RESUME TEXT]
{cleaned_text}
[END OF CLEANED RESUME TEXT]
"""
        
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": { "temperature": 0.0, "topK": 1 }
        }
        
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        
        result = response.json()

        if result.get("candidates") and result["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text"):
            formatted_text = result["candidates"][0]["content"]["parts"][0]["text"]
            return jsonify({"formattedText": formatted_text})
        else:
            return jsonify({"error": "Failed to get valid response from AI model."}), 500

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500
