


from ollama_client import OllamaClient
from rag_processor import RAGProcessor
from data.sync_csv import save_dat_csv

class MainProgram:
    def __init__(self):

        print("Initializing Main Program...")

        print("Syncing CSV data...")
        save_dat_csv()

        print("Setting up RAG Processor...")
        self.rag_processor = RAGProcessor()
        print("RAG Processor set up.")

        print("Setting up Ollama Client...")
        self.ollama_client = OllamaClient()
        print("Ollama Client set up.")


    def run(self):

        print("Running main program...")
        user_prompt = input("Enter your research question: ")
        print("Processing RAG...")
        prompt = self.rag_processor.search(user_prompt)

        print("Sending prompt to Ollama...")
        response = self.ollama_client.send_prompt(model_name="qwen3:0.6b", prompt=prompt)
        print(response)

if __name__ == "__main__":
    main_program = MainProgram()
    main_program.run()