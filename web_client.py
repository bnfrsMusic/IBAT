from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import sys
import io

# Add the parent directory to the Python path to allow importing from other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import IBAT

# --- Initialization ---
print("Initializing IBAT...")
ibat_instance = IBAT(voice=False)  # Initialize with voice=False for web use
print("IBAT Initialized.")

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# --- API Routes ---
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_prompt = data.get('message')
    size = data.get('size', 'light')

    if not user_prompt:
        return jsonify({"error": "No message provided"}), 400

    # Set model weight
    ibat_instance.weight = size

    response_text = ibat_instance.run(user_prompt)
    
    return jsonify({"response": response_text})

@app.route('/api/tts', methods=['POST'])
def tts():
    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    audio_fp = io.BytesIO()
    ibat_instance.engine.save_to_file(text, audio_fp)
    ibat_instance.engine.runAndWait()
    audio_fp.seek(0)

    return Response(audio_fp, mimetype='audio/wav')

# --- Frontend Serving ---
@app.route('/')
def index():
    return send_from_directory('frontend', 'main.html')

@app.route('/<path:path>')
def serve_frontend(path):
    # This is to serve static files like CSS, JS
    return send_from_directory('frontend', path)

# --- Main Execution ---
if __name__ == '__main__':
    print("Starting web server...")
    app.run(port=5000, debug=True)
