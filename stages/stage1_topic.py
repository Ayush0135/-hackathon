from utils.llm import query_stage
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
    response = query_stage("topic", prompt)
    
    from utils.json_parser import extract_json_from_text
    data = extract_json_from_text(response)
    
    if data:
        return data
    else:
        print(f"Error parsing Stage 1 output")
        return None
