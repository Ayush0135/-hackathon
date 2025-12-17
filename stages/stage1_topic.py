from utils.llm import query_gemini
import json

def stage1_topic_decomposition(topic):
    print(f"\n--- STAGE 1: TOPIC DECOMPOSITION for '{topic}' ---")
    
    prompt = f"""
    You are an expert research planner.
    User Topic: "{topic}"
    
    Task:
    1. Identify the primary research domain.
    2. Generate 5-8 closely related subtopics.
    3. Expand each subtopic into advanced academic search keywords.
    4. Prepare structured search queries suitable for Google Programmable Search Engine API.
    
    Output Format (JSON strictly):
    {{
        "domain": "string",
        "subtopics": [
            {{
                "name": "string",
                "keywords": ["string", "string"],
                "search_queries": ["string", "string"]
            }}
        ]
    }}
    """
    
    # Logic task, so safe to fall back to Groq/Anthropic
    response = query_gemini(prompt, fallback_to_others=True)
    try:
        # Find the first { and last }
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = response[start_idx:end_idx+1]
        else:
            json_str = response

        data = json.loads(json_str)
        return data
    except Exception as e:
        print(f"Error parsing Stage 1 output: {e}")
        # print(f"Raw Response: {response}") # verbose
        return None
