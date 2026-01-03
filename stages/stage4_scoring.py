from utils.llm import query_stage
import json
import re

def stage4_academic_scoring(analyzed_documents, topic):
    print("\n--- STAGE 4: ACADEMIC SCORING (Groq) ---")
    scored_documents = []
    
    # process in parallel
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def score_single_doc(doc):
        analysis = doc.get('analysis', {})
        if not analysis: return None
        
        print(f"Scoring: {doc['title'][:50]}...")
        
        prompt = f"""
        Role: Research Relevance Evaluator.
        Target Research Topic: "{topic}"
        
        Document Title: {doc['title']}
        Analysis Summary:
        - Problem: {analysis.get('research_problem')}
        - Method: {analysis.get('methodology')}
        - Findings: {analysis.get('key_findings')}
        - Novelty: {analysis.get('novelty_assessment')}
        
        Evaluate based on:
        1. Relevance to the research topic (Most Important)
        2. Information value
        3. Clarity
        4. Methodological rigor (Optional but good)
        5. Usefulness for a synthesis paper
        
        Return *only* the JSON object below. Do not add any text before or after.
        {{
          "score": 5, 
          "strengths": "Short summary",
          "weaknesses": "Short summary"
        }}
        """
        
        try:
            response = query_stage("scoring", prompt)
            from utils.json_parser import extract_json_from_text
            score_data = extract_json_from_text(response)
            
            if score_data:
                doc['scoring'] = score_data
                print(f"  Score: {score_data.get('score')} - {doc['title'][:30]}")
                return doc
        except Exception as e:
            print(f"Error scoring {doc['title'][:10]}: {e}")
            
        # Fallback for ANY failure (LLM or Parser): Default to 3 to keep pipeline moving
        print(f"  Score: 3 (Defaulted/Failed) - {doc['title'][:30]}")
        doc['scoring'] = {
            "score": 3,
            "strengths": "Defaulted due to scoring error/LLM limit",
            "weaknesses": "Could not verify"
        }
        return doc

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(score_single_doc, doc): doc for doc in analyzed_documents}
        
        for future in as_completed(futures):
            res = future.result()
            if res:
                scored_documents.append(res)
            
    return scored_documents
