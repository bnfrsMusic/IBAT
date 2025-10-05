
import requests
from typing import Optional, List


class OllamaClient:
    """
    Ollama Client Module
    Handles communication with Ollama LLM server
    """

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url.rstrip('/')
        self.session = requests.Session()
    
    def send_prompt(self, model_name: str, prompt: str, **options) -> Optional[str]:
        """Send prompt to Ollama"""
        try:
            url = f"{self.ollama_url}/api/generate"
            
            # Default options
            default_options = {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048,
                "stop": ["Human:", "User:"]
            }
            
            # merge with provided options
            merged_options = {**default_options, **options}
            
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": merged_options
            }
            
            print("Generating response...")
            response = self.session.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "No response from model")
            
        except requests.exceptions.Timeout:
            print("Ollama request timed out")
            return None
        except requests.exceptions.ConnectionError:
            print("Could not connect to Ollama server")
            return None
        except Exception as e:
            print(f"Ollama error: {e}")
            return None
    
    def check_connection(self, model_name: str) -> bool:
        """Check Ollama and model is available."""
        try:
            response = self.session.get(f"{self.ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            if not any(model_name in name for name in model_names):
                print(f"Model '{model_name}' not found.")
                print(f"Available: {', '.join(model_names)}")
                return False
            
            print(f"Ollama connected - Model: {model_name}")
            return True
            
        except requests.exceptions.ConnectionError:
            print(f"Ollama connection failed: Could not connect to {self.ollama_url}")
            return False
        except requests.exceptions.Timeout:
            print(f"Ollama connection failed: Timeout")
            return False
        except Exception as e:
            print(f"Ollama connection failed: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """Get list of available models."""
        try:
            response = self.session.get(f"{self.ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            models = response.json().get("models", [])
            return [model["name"] for model in models]
            
        except Exception:
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull model from Ollama"""
        try:
            url = f"{self.ollama_url}/api/pull"
            payload = {"name": model_name}
            
            print(f"Pulling model: {model_name}...")
            response = self.session.post(url, json=payload, timeout=300)  # 5 minute timeout
            response.raise_for_status()
            
            print(f"Model {model_name} pulled successfully")
            return True
            
        except Exception as e:
            print(f"Failed to pull model {model_name}: {e}")
            return False