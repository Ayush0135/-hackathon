import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Enable high-performance download for HuggingFace
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

# Model Configuration
# Using Qwen2.5-0.5B-Instruct as it is very small (~1GB) and capable
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

def setup_offline_model():
    print(f"Starting download for offline model: {MODEL_ID}")
    print("This may take a few minutes depending on your internet connection.")
    
    try:
        # Download Tokenizer
        print("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
        
        # Download Model
        print("Downloading model weights...")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16 if torch.cuda.is_available() or torch.backends.mps.is_available() else torch.float32,
            trust_remote_code=True
        )
        
        print(f"\nSuccessfully downloaded and verified {MODEL_ID}!")
        print("You can now run the research agent with offline capabilities.")
        
    except Exception as e:
        print(f"\nError during download: {str(e)}")
        print("Please check your internet connection or disk space.")

if __name__ == "__main__":
    setup_offline_model()
