from utils.llm import query_gemini
import json
import re

def extract_json(text):
    """
     robustly extract JSON from text using regex 
    """
    try:
        # Try finding the first { and last }
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            # Remove trailing commas before closing braces/brackets
            json_str = re.sub(r',\s*\}', '}', json_str)
            json_str = re.sub(r',\s*\]', ']', json_str)
            return json.loads(json_str)
        return None
    except:
        return None

def stage3_document_analysis(documents):
    print("\n--- STAGE 3: DOCUMENT ANALYSIS")
    analyzed_documents = []
    
    for doc in documents:
        print(f"Analyzing: {doc['title'][:50]}...")
        
        # Truncate text to fit context window if necessary
        text_content = doc['raw_text'][:20000] 
        
        prompt = f"""
        Analyze the following research document content.
        
        Document Title: {doc['title']}
        Document Content (Excerpt):
        {text_content}
        
        Task:
        1. Extract the research problem.
        2. Identify methodology and experimental setup.
        3. Summarize key findings.
        4. Identify limitations and weaknesses.
        5. Detect explicit or implicit research gaps.
        6. Assess novelty.
        
        Constraint:
        - All output must be paraphrased. Do NOT copy text verbatim.
        
        Output Format (JSON strictly):
        {{
            "research_problem": "string",
            "methodology": "string",
            "key_findings": "string",
            "limitations": "string",
            "research_gaps": "string",
            "novelty_assessment": "string"
        }}
        """
        
        # Heavy analysis: Try Gemini, then fail directly to offline (saves Groq for scoring)
        response = query_gemini(prompt, fallback_to_others=False)
        try:
            # Try robust extraction first
            analysis = extract_json(response)
            
            # If that fails, try the clean-up method
            if not analysis:
                cleaned_response = response.replace("```json", "").replace("```", "")
                analysis = json.loads(cleaned_response)
            
            doc['analysis'] = analysis
            analyzed_documents.append(doc)
        except Exception as e:
            print(f"  Error analyzing document: {e}")
            # Keep doc but mark as unanalyzed or skip? Skipping is safer for downstream quality.
            continue
            
    return analyzed_documents
