import shutil
import subprocess
import sys



try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
except subprocess.CalledProcessError as e:
    print("Failed to install required Python packages:", e)
    sys.exit(1)


if shutil.which("ollama") is None:
    print("Ollama not found. Please install Ollama first: https://ollama.com/download")
    sys.exit(1)
