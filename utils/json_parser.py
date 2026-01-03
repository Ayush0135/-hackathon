
import json
import re

def extract_json_from_text(text):
    """
    Robustly extracts and parses JSON content from a string that may contain 
    Markdown formatting, conversational text, or other noise.
    """
    if not text:
        return None
        
    try:
        # 1. Try to find content within ```json ... ``` blocks
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
             json_str = match.group(1)
             return _safe_load(json_str)

        # 2. Try to find content within [...] blocks (for lists)
        list_block_pattern = r'```(?:json)?\s*(\[.*?\])\s*```'
        match = re.search(list_block_pattern, text, re.DOTALL)
        if match:
             json_str = match.group(1)
             return _safe_load(json_str)

        # 3. Fallback: Regex search for the outermost {} or [] pair
        # This is improving on simple .find() by handling nested structures strictly
        
        # Search for object
        # We catch the first { and attempt to match it to a closing }
        # Note: Balancing braces with regex is hard, so we use a non-greedy dot approach 
        # combined with a recursive-like attempt or just finding the largest valid block.
        
        # Simple approach: Find first { and last }
        start_obj = text.find('{')
        end_obj = text.rfind('}')
        if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
            json_str = text[start_obj:end_obj+1]
            try: 
                return _safe_load(json_str)
            except:
                pass # Try list next
        
        # Search for list
        start_arr = text.find('[')
        end_arr = text.rfind(']')
        if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
            json_str = text[start_arr:end_arr+1]
            try:
                return _safe_load(json_str)
            except:
                pass

        # 4. Last Resort: Try cleaning commonly problematic characters
        cleaned = text.strip()
        if cleaned.startswith("```") and cleaned.endswith("```"):
             cleaned = cleaned[3:-3].strip()
             if cleaned.startswith("json"):
                 cleaned = cleaned[4:].strip()
             return _safe_load(cleaned)
             
        return None
        
    except Exception as e:
        print(f"[JSON Parser] Parsing failed: {e}")
        return None

def _safe_load(json_str):
    # Cleans trailing commas which are common LLM errors
    # json_str = re.sub(r',\s*\}', '}', json_str)
    # json_str = re.sub(r',\s*\]', ']', json_str)
    # The above regex is risky if comma is inside a string. relying on strict=False 
    return json.loads(json_str, strict=False)
