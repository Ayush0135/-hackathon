
import os
import time
import google.generativeai as genai
from groq import Groq
from anthropic import Anthropic, NotFoundError
from dotenv import load_dotenv
from utils.llm_offline import query_offline_llm

load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Initialize Clients
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# --- Internal Callers ---

def _call_gemini(prompt):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found.")
    
    # Updated to gemini-2.0-flash based on available models
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Simple retry logic for ResourceExhausted or other transient errors
    # Reduced retries for faster failover to other models/offline
    max_retries = 1 
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            if not response.text:
                raise ValueError("Gemini returned empty response.")
            return response.text
        except Exception as e:
            # Check if it's a quota error (429/ResourceExhausted)
            if "429" in str(e) or "ResourceExhausted" in str(e) or "QuotaExceeded" in str(e):
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)  # Exponential backoff: 5s, 10s, 20s
                    print(f"  [Gemini] Rate limit hit. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            raise e  # smooth failover to next model if retries exhausted or other error

def _call_groq(prompt):
    if not groq_client:
        raise ValueError("GROQ_API_KEY not found or client init failed.")
    
    # Updated to llama-3.3-70b-versatile
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
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
    
    # Updated: Try Claude 3.5 Sonnet (June version) then Haiku (most widely available)
    model_id = "claude-3-5-sonnet-20240620" 
    
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

def query_llm_robust(prompt, primary_preference='gemini', use_heavy_fallback=True):
    """
    Tries models in a specific order:
    1. Primary Preference (Gemini or Groq)
    2. The other of the top 2 (ONLY if use_heavy_fallback is True)
    3. Anthropic (Backup) (ONLY if use_heavy_fallback is True)
    4. Offline Model (Last Resort)
    """
    
    # Define availability map
    strategies = [
        ('gemini', _call_gemini),
        ('groq', _call_groq),
        ('anthropic', _call_anthropic)
    ]
    
    # Sort strategies: Primary first, then others
    if primary_preference == 'groq':
        # Move groq to front
        strategies.sort(key=lambda x: 0 if x[0] == 'groq' else 1)
    else:
        # Default gemini first
        strategies.sort(key=lambda x: 0 if x[0] == 'gemini' else 1)
        
    errors = []
    
    # 1. Try Online APIs
    for name, func in strategies:
        # If we are in 'light' mode (use_heavy_fallback=False), SKIP secondary online models
        # But ALWAYS try the primary one first.
        if not use_heavy_fallback and name != primary_preference:
             continue
             
        try:
            # print(f"  Attempting {name}...") 
            return func(prompt)
        except Exception as e:
            # print(f"  [Warning] {name} failed: {str(e)}")
            errors.append(f"{name}: {str(e)}")
            continue
            
    # 2. Fallback to Offline
    # Only print this message once to avoid spamming the console
    if not hasattr(query_llm_robust, "_has_warned_offline"):
        print(f"  [System] API(s) failed. Switching to Offline Model (Qwen/Qwen2.5-0.5B-Instruct).")
        query_llm_robust._has_warned_offline = True
        
    return query_offline_llm(prompt)


# --- Public Interface (backward compatibility) ---

def query_gemini(prompt, retries=1, delay=0, fallback_to_others=False):
    """
    Queries Gemini. 
    If fallback_to_others=False (default for heavy content), goes Gemini -> Offline.
    If fallback_to_others=True (for scoring/logic), goes Gemini -> Groq -> Anthropic -> Offline.
    """
    return query_llm_robust(prompt, primary_preference='gemini', use_heavy_fallback=fallback_to_others)

def query_groq(prompt, json_mode=False, fallback_to_others=True):
    """
    Queries Groq. Defaults to full fallback as it's usually used for scoring.
    """
    return query_llm_robust(prompt, primary_preference='groq', use_heavy_fallback=fallback_to_others)
