import os
import ollama
from ollama import Client
from dotenv import load_dotenv

load_dotenv()

# Configuration for Ollama
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
# Default to localhost if not set, typical for local runs.
# Only use https://ollama.com/api if actually intended (which requires keys usually).
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

def get_client():
    if OLLAMA_API_KEY:
        # If we have an API key, we use the Client with headers
        return Client(
            host=OLLAMA_HOST,
            headers={
                'Authorization': f'Bearer {OLLAMA_API_KEY}'
            }
        )
    return None # Use default ollama.chat

def query_offline_llm(prompt, model_name=None):
    """
    Queries Ollama (Cloud if API Key present, else local).
    """
    client = get_client()
    target_model = model_name if model_name else OLLAMA_MODEL
    
    try:
        messages = [
            {'role': 'system', 'content': 'You are a helpful research assistant.'},
            {'role': 'user', 'content': prompt}
        ]
        
        if client:
            response = client.chat(
                model=target_model, 
                messages=messages, 
                options={'num_ctx': 8192}, # Increased context window for research
                format='json' if 'json' in prompt.lower() else ''
            )
        else:
            response = ollama.chat(
                model=target_model, 
                messages=messages, 
                options={'num_ctx': 8192}, # Increased context window for research
                format='json' if 'json' in prompt.lower() else ''
            )
            
        return response['message']['content']
    except Exception as e:
        error_str = str(e).lower()
        if "not found" in error_str:
            raise ValueError(f"Ollama model '{target_model}' not found.")
        if "401" in error_str or "unauthorized" in error_str:
             raise PermissionError("Ollama Cloud API Key is invalid or unauthorized.")
        print(f"Error querying Ollama: {e}")
        raise e

if __name__ == "__main__":
    # Test Ollama
    mode = "Cloud" if OLLAMA_API_KEY else "Local"
    print(f"Testing Ollama ({mode}) with model: {OLLAMA_MODEL}")
    test_response = query_offline_llm("Say hello!")
    print(f"Response: {test_response}")
