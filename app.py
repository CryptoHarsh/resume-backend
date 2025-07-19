import os
import requests
from flask import Flask, request, jsonify

# Setup Flask App
app = Flask(__name__)

# --- Manually add the permission headers after each request ---
@app.after_request
def after_request(response):
    # THIS IS THE FIX: The URL now correctly points to your frontend service.
    response.headers.add('Access-Control-Allow-Origin', 'https://resume-frontend-k6zm.onrender.com')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# --- Health Check Endpoint to keep Render "Live" ---
@app.route('/')
def health_check():
    return jsonify({"status": "healthy"}), 200

# --- The REAL AI Formatting Endpoint ---
@app.route('/format-resume-ai', methods=['POST', 'OPTIONS'])
def format_resume_with_ai():
    # The browser sends an 'OPTIONS' request first to check permissions.
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # If it's not an OPTIONS request, it's the real 'POST' request with the data.
    try:
        data = request.get_json()
        if not data or 'cleanedText' not in data:
            return jsonify({"error": "Missing cleanedText in request"}), 400
            
        cleaned_text = data['cleanedText']

        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return jsonify({"error": "API key is not configured on the server."}), 500

        prompt = f"""
You are an expert-level resume parser and formatter. Your task is to take pre-cleaned text and produce a clean, ATS-friendly, single-column resume. You must follow a strict, multi-step process.

**Step 1: Analyze and Reconstruct**
First, analyze the text. It may be jumbled from a multi-column layout. Identify all the logical sections (Name, Contact, Summary, Experience, Skills, Education, etc.) and reconstruct them into a single, ordered column. Your highest priority is correctly grouping all content under its proper heading.

**Step 2: Apply Section-Specific Bullet Point Rules**
After reconstructing the content, you MUST apply these specific rules for creating bullet points. This is the most critical step.

* **Rule A: For the "PROFESSIONAL EXPERIENCE" section:**
    * If a job description contains lines that explicitly start with a bullet character ('•', '*', '-'), EACH of those lines MUST become a separate bullet point ('•') in the output.
    * If a job description contains multiple distinct paragraphs that do NOT start with a bullet character, EACH of those paragraphs MUST also become a separate bullet point ('•').
    * Merge any wrapped lines that belong to the same paragraph or bullet point.

* **Rule B: For the "TECHNICAL SKILLS" or "SKILLS" section:**
    * This section has a different format. If you see sub-categories (e.g., "OPERATING SYSTEMS"), these sub-categories are headings.
    * The list of skills that follows a sub-category (e.g., "Linux, Windows") should be a **single line of plain text**.
    * **You MUST NOT add a '•' bullet point to the sub-category heading OR to the list of skills in this section.**

* **Rule C: For all other sections:**
    * Only create a bullet point if the line explicitly started with a bullet character in the original text. Otherwise, treat it as a normal paragraph.

**Step 3: Final Formatting**
Finally, apply these overall formatting rules to the structured text from Step 2.

* **Headers:** All main section headers (PROFESSIONAL EXPERIENCE, TECHNICAL SKILLS, etc.) must be in ALL CAPS.
* **Contact Info:** The line directly under the candidate's name should contain all contact details, separated by " | ".
* **Cleanup:** Preserve all URLs. All other junk symbols should already have been removed.

**OUTPUT REQUIREMENTS:**
* Produce ONLY the final, clean, formatted resume text.
* Do not include any explanations, notes, or apologies.
* The output must begin directly with the candidate's name.

[START OF CLEANED RESUME TEXT]
{cleaned_text}
[END OF CLEANED RESUME TEXT]
"""
        
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
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
