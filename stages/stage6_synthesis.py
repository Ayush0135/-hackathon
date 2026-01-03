from utils.llm import query_stage
import json
import re

def stage6_research_synthesis(knowledge_base, topic):
    print("\n--- STAGE 6: ORIGINAL RESEARCH SYNTHESIS ")
    
    if not knowledge_base:
        print("No knowledge base available. Cannot synthesize.")
        return None
        
    kb_text = json.dumps(knowledge_base, indent=2)
    
    prompt = f"""
    You are an expert academic researcher (Author Model).
    Topic: "{topic}"
    
    Based on the following analysis of high-quality matching literature:
    {kb_text}
    
    Task:
    1. Identify a clear and defensible research gap that is NOT fully addressed by the knowledge base.
    2. Propose a specific ORIGINAL contribution (Algorithm, Framework, Model, or Survey Analysis) to fill this gap.
    3. Synthesize ideas across sources to support this contribution.
    4. Outline a methodology.
    5. DESIGN simulated/conceptual results that would validate this contribution (Do NOT fabricate real-world data, but describe what the results *would* show concepts or simulation).
    
    Constraint:
    - Avoid plagiarism entirely.
    - Clearly mark results as simulated/conceptual.
    
    Output Format (JSON):
    {{
        "research_gap": "string",
        "proposed_contribution": "string",
        "synthesis_of_related_work": "string",
        "methodology_plan": "string",
        "simulated_results_description": "string",
        "conclusion_plan": "string"
    }}
    """
    
    # Heavy synthesis using 'synthesis' stage strategy
    response = query_stage("synthesis", prompt)
    
    from utils.json_parser import extract_json_from_text
    synthesis = extract_json_from_text(response)
    # Fallback if parser returns None
    if not synthesis:
         print("Error regarding synthesis JSON extraction.")
         
    return synthesis
