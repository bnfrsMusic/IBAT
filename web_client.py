from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import sys
import io
import re
import tempfile
import pyttsx3
import threading

# Add the parent directory to the Python path to allow importing from other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import IBAT

# --- Initialization ---
print("Initializing IBAT...")
ibat_instance = IBAT(voice=False)  # Initialize with voice=False for web use
print("IBAT Initialized.")

# Create a separate TTS engine for web use
tts_engine = None
tts_lock = threading.Lock()

def get_tts_engine():
    """Get or create TTS engine thread-safely"""
    global tts_engine
    with tts_lock:
        if tts_engine is None:
            tts_engine = pyttsx3.init()
        return tts_engine

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

def format_response_text(text):
    # Convert URLs into hyperlinks
    text = re.sub(r'(https?://\S+)', r'<a href="\1" target="_blank">\1</a>', text)
    # Convert bold text into <b> tags
    text = re.sub(r'\*(.*?)\*', r'<b>\1</b>', text)
    # Replace newlines with <br>
    text = text.replace('\n', '<br>')
    # Remove thinking blocks
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Remove leading <br> tags and whitespace
    text = re.sub(r'^(<br>\s*)+', '', text)
    text = text.lstrip()
    return text

# --- API Routes ---
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_prompt = data.get('message')
    size = data.get('size', 'medium')
    
    if not user_prompt:
        return jsonify({"error": "No message provided"}), 400
    
    print(f"Received user prompt: {user_prompt}")
    
    # Set model weight
    ibat_instance.weight = size
    
    try:
        response_data = ibat_instance.run(user_prompt)
        response_text = response_data.get("response", "")
        sources = response_data.get("sources", [])
        print(f"Generated response: {response_text}")
    except Exception as e:
        print(f"Error during processing: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
    formatted_response = format_response_text(response_text)
    

    # try:
    #     engine = get_tts_engine()
    #     engine.say(formatted_response)
    #     engine.runAndWait()
    # except Exception as e:
    #     print(f"TTS error: {e}")
    
    return jsonify({"response": formatted_response, "sources": sources})

@app.route('/api/listen', methods=['POST'])
def listen():
    print("Received request to listen for speech...")
    try:
        # Check if IBAT has listen_for_speech method
        if hasattr(ibat_instance, 'listen_for_speech'):
            transcribed_text = ibat_instance.listen_for_speech()
            if transcribed_text:
                return jsonify({"text": transcribed_text})
            else:
                return jsonify({"error": "No speech detected or understood"}), 400
        else:
            return jsonify({"error": "Speech recognition not available"}), 501
    except Exception as e:
        print(f"Error during speech recognition: {e}")
        return jsonify({"error": "Failed to process audio"}), 500

@app.route('/api/tts', methods=['POST'])
def tts():
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        # Clean text for TTS
        clean_text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
        clean_text = re.sub(r'<think>.*?</think>', '', clean_text, flags=re.DOTALL)
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_path = temp_audio.name
        
        # Generate audio
        engine = get_tts_engine()
        engine.save_to_file(clean_text, temp_path)
        engine.runAndWait()
        
        # Read audio file
        with open(temp_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return Response(audio_data, mimetype='audio/wav')
    except Exception as e:
        print(f"TTS error: {e}")
        return jsonify({"error": f"TTS failed: {str(e)}"}), 500

@app.route('/api/get-reports', methods=['GET'])
def get_reports():
    """Return the current NCBI and OSDR queries"""
    try:
        # Check if rag_processor exists
        if hasattr(ibat_instance, 'rag_processor'):
            return jsonify({
                'ncbi_queries': getattr(ibat_instance.rag_processor, 'ncbi_queries', []),
                'osdr_queries': getattr(ibat_instance.rag_processor, 'osdr_queries', [])
            })
        else:
            return jsonify({'ncbi_queries': [], 'osdr_queries': []})
    except Exception as e:
        print(f"Error getting reports: {e}")
        return jsonify({'ncbi_queries': [], 'osdr_queries': []}), 500

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