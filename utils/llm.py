
import os
import time
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", module="urllib3")
warnings.filterwarnings("ignore", message=".*OpenSSL.*")
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from anthropic import Anthropic, NotFoundError
except ImportError:
    Anthropic = None
    NotFoundError = Exception

from dotenv import load_dotenv
from utils.llm_offline import query_offline_llm

load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Import Memory System
from utils.memory import MemorySystem
# Initialize Memory System
memory_system = MemorySystem()

# Initialize Clients
if GEMINI_API_KEY and genai is not None:
    genai.configure(api_key=GEMINI_API_KEY)

groq_client = Groq(api_key=GROQ_API_KEY, timeout=60.0, max_retries=0) if GROQ_API_KEY and Groq is not None else None
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY, timeout=60.0, max_retries=0) if ANTHROPIC_API_KEY and Anthropic is not None else None

# --- Internal Callers ---

def _call_gemini(prompt):
    if not GEMINI_API_KEY or genai is None:
        raise ValueError("GEMINI_API_KEY not found or google.generativeai not installed.")
    
    # Switched back to stable model to avoid 400 Bad Request / Deprecation issues
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Simple retry logic for ResourceExhausted or other transient errors
    # Reduced retries for faster failover to other models/offline
    max_retries = 3 
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            if not response.text:
                raise ValueError("Gemini returned empty response.")
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg:
                print(f"  [Gemini] 400 Bad Request (Invalid Argument/Model). Switching strategies...")
                raise e # Propagate so execute_strategies picks next one
                
            # Check if it's a quota error (429/ResourceExhausted)
            if "429" in error_msg or "ResourceExhausted" in error_msg or "QuotaExceeded" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)  # Exponential backoff: 5s, 10s, 20s
                    print(f"  [Gemini] Rate limit hit. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            raise e  # smooth failover to next model if retries exhausted or other error

def _call_groq(prompt):
    if not groq_client:
        raise ValueError("GROQ_API_KEY not found or client init failed.")
    
    # Updated to llama-3.1-8b-instant (higher free-tier TPM limits)
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        if "429" in str(e): # Rate limit
             # For Groq free tier, limits can be long (minutes). 
             # Better to failover immediately unless it's very short, 
             # but we can try a short sleep just in case.
             time.sleep(2) 
        raise e

def _call_anthropic(prompt):
    if not anthropic_client:
        raise ValueError("ANTHROPIC_API_KEY not found or client init failed.")
    
    # Updated: Haiku is most widely available and very fast for research
    model_id = "claude-3-haiku-20240307" 
    
    try:
        message = anthropic_client.messages.create(
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            model=model_id, 
        )
        return message.content[0].text
    except NotFoundError:
        # Fallback to Haiku which is usually available to all tiers
        try:
            message = anthropic_client.messages.create(
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-haiku-20240307", 
            )
            return message.content[0].text
        except Exception as e:
            raise e

# --- Main Logic ---

# --- Stage Configuration ---

# Format: "stage_name": ["model_id_1", "model_id_2"]
# Model IDs can be: 'groq', 'anthropic', 'gemini', or 'ollama:model_name'
STAGE_CONFIG = {
    "default": ["groq", "anthropic", "gemini", "ollama:deepseek-r1", "ollama:qwen2.5", "ollama:llama3.2", "ollama:mistral", "ollama:phi3"],
    
    # Fast, Logic Heavy
    "topic": ["groq", "gemini", "anthropic", "ollama:deepseek-r1", "ollama:qwen2.5", "ollama:llama3.2", "ollama:mistral"],
    
    # Search filtering (High volume, needs speed)
    "discovery": ["groq", "gemini", "anthropic", "ollama:qwen2.5", "ollama:llama3.2", "ollama:mistral", "ollama:phi3"], 
    
    # Analysis (Heavy Context, Reasoning)
    "analysis": [
        "groq",
        "anthropic",
        "gemini",
        "ollama:deepseek-r1",
        "ollama:qwen2.5",
        "ollama:llama3.2",
        "ollama:gemma2",
        "ollama:mistral"
    ],
    
    # Scoring (FAST, strict formatting)
    "scoring": ["groq", "gemini", "anthropic", "ollama:qwen2.5", "ollama:llama3.2", "ollama:mistral", "ollama:phi3"],
    
    # Synthesis & Generation (Creative, high quality)
    "synthesis": ["anthropic", "groq", "gemini", "ollama:deepseek-r1", "ollama:qwen2.5", "ollama:llama3.2", "ollama:gemma2", "ollama:mistral"],
    "generation": ["anthropic", "groq", "gemini", "ollama:deepseek-r1", "ollama:qwen2.5", "ollama:llama3.2", "ollama:gemma2", "ollama:mistral"],
    "review": ["anthropic", "groq", "gemini", "ollama:deepseek-r1", "ollama:qwen2.5", "ollama:llama3.2", "ollama:gemma2", "ollama:mistral"]
}

def _resolve_strategy(model_id):
    """
    Returns a callable (function) for a given model_id string.
    """
    if model_id == 'groq':
        return lambda p: _call_groq(p)
    elif model_id == 'anthropic':
        return lambda p: _call_anthropic(p)
    elif model_id == 'gemini':
         return lambda p: _call_gemini(p)
    elif model_id.startswith('ollama:'):
        # Specific offline/cloud model
        model_name = model_id.split(':', 1)[1]
        return lambda p: query_offline_llm(p, model_name=model_name)
    else:
        # Default to offline if unknown
        return lambda p: query_offline_llm(p, model_name='llama3.2')

def execute_strategies(strategies, prompt):
    """
    Executes a list of strategy functions in order.
    """
    errors = []
    
    # Try strategies in order
    for i, func in enumerate(strategies):
        try:
             # print(f"  [Strategy {i+1}] Executing...") 
             return func(prompt)
        except Exception as e:
            from termcolor import colored
            error_msg = str(e)
            
            if "429" in error_msg or "Rate limit" in error_msg or "ResourceExhausted" in error_msg or "rate_limit_exceeded" in error_msg:
                print(colored(f"  [Limit] Strategy {i+1} rate limited. Switching...", "yellow"))
            elif "not found" in error_msg.lower() or "connection" in error_msg.lower():
                 print(colored(f"  [Config] Strategy {i+1} Key/Model missing or offline. Switching...", "yellow"))
            else:
                print(colored(f"  [Error] Strategy {i+1} failed: {error_msg[:200]}...", "red"))
            
            errors.append(error_msg)
            continue
            
    # Fallback to generic offline if enabled and not already tried
    enable_offline = os.getenv("ENABLE_OFFLINE_FALLBACK", "True").lower() == "true"
    if enable_offline:
        try:
            return query_offline_llm(prompt, model_name='llama3.2')
        except Exception as e:
            errors.append(f"Offline Default: {e}")
            
    raise Exception(f"All strategies failed. Errors: {errors}")

def query_stage(stage, prompt, skip_memory=False):
    """
    Primary Entry Point for Stage-based LLM routing.
    """
    # Get config for stage, or default
    model_chain = STAGE_CONFIG.get(stage, STAGE_CONFIG['default'])
    
    # Resolve to functions
    strategies = [_resolve_strategy(m) for m in model_chain]
    
    final_prompt = prompt

    if not skip_memory:
        # --- Memory Integration ---
        # 1. Retrieve Context
        context_str = memory_system.retrieve_context(prompt)
        
        if context_str:
            # Append context to prompt in a clearly separated way
            final_prompt = f"{prompt}\n\n[SYSTEM: The following are relevant past interactions to help with context]\n{context_str}\n[End Context]"
    
    # 2. Execute
    response = execute_strategies(strategies, final_prompt)
    
    # 3. Save Memory
    # We save the *original* prompt, not the one with context, to avoid recursive context bloat
    if response and not skip_memory:
        import threading
        threading.Thread(
            target=memory_system.add_memory, 
            args=(prompt, response, {"stage": stage}), 
            daemon=True
        ).start()
        
    return response

# --- Deprecated / Compatibility ---

def query_llm_robust(prompt, primary_preference=None, use_heavy_fallback=True):
    """
    Legacy wrapper. Maps to 'default' stage effectively.
    """
    return query_stage("default", prompt)

def query_gemini(prompt, retries=1, delay=0, fallback_to_others=False):
    # Map legacy calls to appropriate stages based on fallback flag
    # If fallback_to_others is False (usually analysis), use 'analysis' stage
    if not fallback_to_others:
        return query_stage("analysis", prompt)
    return query_stage("default", prompt)

def query_groq(prompt, json_mode=False, fallback_to_others=True):
    return query_stage("scoring", prompt)
