import json
import shutil
import subprocess
import sys
from typing import Optional

from whisper_vad import WhisperVoiceActivityDetector


# ----------------------------- Requirements -----------------------------
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
except subprocess.CalledProcessError as e:
    print("Failed to install required Python packages:", e)
    sys.exit(1)


if shutil.which("ollama") is None:
    print("Ollama not found. Please install Ollama first: https://ollama.com/download")
    sys.exit(1)

# ----------------------------- Main Program -----------------------------

from ollama_client import OllamaClient
from rag_processor import RAGProcessor
from data.sync_csv import save_dat_csv
import pyttsx3
import speech_recognition as sr


class IBAT:
    def __init__(self, voice: bool = False, energy_threshold: int = 300, pause_threshold: float = 0.8):

        print("Initializing IBAT...")

        print("Syncing CSV data...")
        save_dat_csv()

        print("Setting up RAG Processor...")
        self.rag_processor = RAGProcessor()
        print("RAG Processor set up.")

        print("Setting up Ollama Client...")
        self.ollama_client = OllamaClient()
        print("Ollama Client set up.")

        # Initialize Whisper VAD and Speech 
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.voice = voice

        self.vad = WhisperVoiceActivityDetector(
            recognizer=self.recognizer, 
            microphone=self.microphone,
            whisper_model="tiny",
            energy_threshold=energy_threshold,
            pause_threshold=pause_threshold 
        )
        self.vad.calibrate()
        
        self.engine = pyttsx3.init()     
    # def listen_for_speech(self) -> Optional[str]:
    #     return self.vad.listen_for_speech_vad(timeout=self.speech_timeout)
    
    def listen_for_speech(self) -> Optional[str]:
        return self.vad.listen_for_speech_vad(timeout=10)

    def run(self):

        print("Running main program...")

        if self.voice:
            print("Please speak your research question after the prompt.")
            user_prompt = None
            
            while not user_prompt:
                user_prompt = self.listen_for_speech()
                if not user_prompt:
                    print("No valid speech input detected. Please try again.")

            print(f"Transcribed Question: {user_prompt}")
        else:
            user_prompt = input("Enter your research question: ")

        print("Connecting to Ollama model...")

        model_name = "qwen3:0.6b"

        if self.weight == "light":      #light
            model_name = "qwen3:0.6b"
        elif self.weight == "medium":   #medium
            model_name = "llama3.2:3b"
        else:                           #heavy
            model_name = ""

        self.ollama_client.pull_model(model_name)

        print("Processing RAG...")
        prompt = self.rag_processor.search(user_prompt)
        print(prompt)

        print("Sending prompt to Ollama...")
        


        response = self.ollama_client.send_prompt(model_name=model_name, prompt=prompt)
        
        print(response)
        self.engine.say(response)
        self.engine.runAndWait()

if __name__ == "__main__":
    ibat = IBAT(voice=True)
    ibat.weight = "medium"  # Options: "light", "medium", "heavy"
    ibat.run()


