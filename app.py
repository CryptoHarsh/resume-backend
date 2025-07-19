from flask import Flask, jsonify

app = Flask(__name__)

# This is the only endpoint. It's designed to always work.
@app.route('/format-resume-ai', methods=['POST', 'OPTIONS'])
def test_endpoint():
    # Manually create the success response
    response = jsonify({"message": "The new code is running!"})
    
    # Manually add the permission header
    response.headers.add('Access-Control-Allow-Origin', '*')
    
    return response
