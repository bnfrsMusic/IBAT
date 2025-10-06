# IBAT (Intelligent Biological Assistive Tool).
This is our submission for the Build a Space Biology Knowledge Engine challenge for NASA's Space Apps Hackathon 2025.
**Authors of this software**: Ayush Sahoo, Samhita Saragadam, Kalp Patel, Jordi Riera Shephard  

## Pre-Requisites:
- **Python 3.11.9**: [Download Python 3.11.9](https://www.python.org/downloads/release/python-3119/)
- **Ollama**: [Visit Ollama](https://ollama.com/)

Please note that this was made by 4 undergraduate students in 48 hours, so there may be bugs!

## Getting Started
To start the program, run the ```start.bat``` if on Windows. If on Linux, run the ```start.sh```.

If you are on Linux and your sound is not working, you may have to run the following commands to fix it:
```bash
sudo apt update && sudo apt install espeak-ng libespeak1
```

You should be able to access your web app at [localhost:5000](http://localhost:5000)

### Models:
- **Light**: qwen3:1.7b _(would advise against, unless you are utilizing a low power computer)_
- **Medium**: llama3.2:3b 
- **Heavy**: deepseek-r1:8b

The Medium and Heavy are the recommended models due to them having much fewer hallucinations and a higher context length.

If you are running a model for the first time, you may have to give some time for the model to download. Furthermore, if you want to know what the program is currently attempting to do, the terminal where you are running it will have in-depth logs of current actions.
