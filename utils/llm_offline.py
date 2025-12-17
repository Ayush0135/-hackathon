import os
import time

# Enable high-performance download for HuggingFace
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
# details: imports moved to load_offline_model to avoid conflicts
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from dotenv import load_dotenv

load_dotenv()

# Configuration for offline Hugging Face model
# Using a smaller model like TinyLlama or similar to ensure it runs on typical consumer hardware without massive downloads.
# For better performance, the USER can switch to 'microsoft/Phi-3-mini-4k-instruct' or 'Mistral-7B' if they have GPU.
# Constants
HF_MODEL_NAME_SMALL = "Qwen/Qwen2.5-0.5B-Instruct"
HF_MODEL_NAME_LARGE = "Qwen/Qwen2.5-1.5B-Instruct" 

# Active model
HF_MODEL_NAME = HF_MODEL_NAME_SMALL

# Global variables for lazy loading
tokenizer = None
model = None
pipe = None

def load_offline_model():
    global tokenizer, model, pipe
    if pipe is not None:
        return

    print(f"Loading offline model: {HF_MODEL_NAME}...")
    print("This runs locally and may take time to download/load the first time.")
    
    try:
        # Lazy imports to avoid mutex/lock conflicts with other libraries (like google-generativeai gRPC)
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

        tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME, trust_remote_code=True)
        
        # Determine device and dtype
        device_name = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        device = torch.device(device_name)
        dtype = torch.float16 if device_name in ["cuda", "mps"] else torch.float32
        
        print(f"Using device: {device_name} with dtype: {dtype}")

        # Load model with manual device placement
        model = AutoModelForCausalLM.from_pretrained(
            HF_MODEL_NAME, 
            torch_dtype=dtype, 
            trust_remote_code=True
        ).to(device)
        
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=2048,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            device=device # Pass device to pipeline explicitly
        )
        print("Offline model loaded successfully.")
    except Exception as e:
        print(f"Error loading offline model: {e}")
        pipe = None

def query_offline_llm(prompt):
    """
    Queries the locally loaded Hugging Face model.
    Loads it strictly on-demand if it hasn't been loaded yet.
    """
    if pipe is None:
        load_offline_model()
        if pipe is None:
            return "Error: Offline model failed to load."

    # Format prompt for Qwen (ChatML-like)
    # <|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n
    messages = [
        {"role": "system", "content": "You are a helpful research assistant."},
        {"role": "user", "content": prompt}
    ]
    formatted_prompt = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    try:
        outputs = pipe(formatted_prompt)
        generated_text = outputs[0]['generated_text']
        
        # Extract assistant response for Qwen/ChatML format
        # Usually checking for <|im_start|>assistant
        if "<|im_start|>assistant" in generated_text:
            return generated_text.split("<|im_start|>assistant")[-1].strip()
        return generated_text.strip()
    except Exception as e:
        print(f"Error querying offline model: {e}")
        return ""

