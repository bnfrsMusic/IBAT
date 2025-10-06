import json
import shutil
import subprocess
import sys
import os
from typing import Optional, List, Dict

from whisper_vad import WhisperVoiceActivityDetector


# ----------------------------- Requirements -----------------------------

# ----------------------------- Source Manager -----------------------------

class SourceManager:
    """Manages NCBI sources and directly updates the HTML report page"""
    
    def __init__(self, report_html_path: str = "report.html"):
        self.report_html_path = report_html_path
        self.known_sources = set()  # Track all sources we've seen
        
    def _read_html(self) -> str:
        """Read the current HTML file"""
        try:
            if os.path.exists(self.report_html_path):
                with open(self.report_html_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except IOError as e:
            print(f"[SourceManager] Error reading HTML: {e}")
        return ""
    
    def _write_html(self, html_content: str):
        """Write updated HTML file"""
        try:
            with open(self.report_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"[SourceManager] Updated HTML file")
        except IOError as e:
            print(f"[SourceManager] Error writing HTML: {e}")
    
    def _create_report_box_html(self, title: str, source_url: str) -> str:
        """Create HTML for a report box"""
        # Escape HTML special characters
        title_escaped = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        source_escaped = source_url.replace('&', '&amp;').replace('"', '&quot;')
        
        return f"""
    <div class="report_box">
        <div class="text">
            <h1>{title_escaped}</h1>
            <p>NCBI Research Paper</p>
        </div>
        <div class="source_button" onclick="window.open('{source_escaped}', '_blank')" style="cursor: pointer;">
            <p>Source</p>
        </div>
    </div>
"""
    
    def add_sources(self, new_sources: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Filter out duplicate sources and inject them directly into HTML
        
        Args:
            new_sources: List of dicts with 'title' and 'source' keys
            
        Returns:
            List of newly added sources
        """
        unique_new_sources = []
        
        for source in new_sources:
            source_link = source['source']
            if source_link not in self.known_sources:
                self.known_sources.add(source_link)
                unique_new_sources.append(source)
        
        if unique_new_sources:
            # Read current HTML
            html_content = self._read_html()
            
            if html_content:
                # Generate HTML for all new sources
                new_html = ""
                for source in unique_new_sources:
                    new_html += self._create_report_box_html(source['title'], source['source'])
                
                # Find the closing </body> tag and insert before it
                if "</body>" in html_content:
                    html_content = html_content.replace("</body>", new_html + "\n</body>")
                    self._write_html(html_content)
                    print(f"[SourceManager] Injected {len(unique_new_sources)} new source(s) into HTML")
                else:
                    print("[SourceManager] Could not find </body> tag in HTML")
            else:
                print("[SourceManager] HTML file not found or empty")
        
        return unique_new_sources
    
    def clear_sources(self):
        """Clear all known sources"""
        self.known_sources.clear()
        print("[SourceManager] Cleared source tracking")


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

        print("Setting up Source Manager...")
        self.source_manager = SourceManager()
        print("Source Manager set up.")

        self.weight = "light"
        self.engine = pyttsx3.init()

        # Initialize Whisper VAD and Speech components
        print("Setting up Speech Recognition...")
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        try:
            self.vad = WhisperVoiceActivityDetector(
                recognizer=self.recognizer, 
                microphone=self.microphone,
                whisper_model="tiny",
                energy_threshold=energy_threshold,
                pause_threshold=pause_threshold 
            )
            self.vad.calibrate()
            print("Speech Recognition set up.")
        except Exception as e:
            print(f"Could not initialize VAD: {e}. Voice input will be disabled.")
            self.vad = None

    def listen_for_speech(self) -> Optional[str]:
        if not self.vad:
            print("Voice Activity Detector not available.")
            return None
        return self.vad.listen_for_speech_vad(timeout=10)
    
    def run(self, user_prompt):

        print("Running main program...")

        print("Connecting to Ollama model...")

        model_name = "qwen3:1.7b"

        if self.weight == "light":      #light
            model_name = "qwen3:1.7b"
        elif self.weight == "medium":   #medium
            model_name = "llama3.2:3b"
        else:                           #heavy
            model_name = "deepseek-r1:8b"

        self.ollama_client.pull_model(model_name)

        print("Processing RAG...")
        prompt = self.rag_processor.search(user_prompt)
        print(prompt)

        # Get new sources from RAG processor BEFORE sending to model
        new_sources = self.rag_processor.get_ncbi_sources()
        
        # Filter and inject new sources directly into HTML
        unique_new_sources = self.source_manager.add_sources(new_sources)
        
        print(f"[IBAT] Injected {len(unique_new_sources)} unique new source(s) into Report page")

        print("Sending prompt to Ollama...")
        
        response = self.ollama_client.send_prompt(model_name=model_name, prompt=prompt)
        
        print(response)

        # Remove the first line from the response
        response_lines = response.split('\n', 1)
        if len(response_lines) > 1:
            response = response_lines[1]
        else:
            response = response_lines[0]

        return {
            "response": response,
            "sources": unique_new_sources
        }