from utils.llm import query_stage
import json
import re

def stage4_academic_scoring(analyzed_documents, topic):
    print("\n--- STAGE 4: ACADEMIC SCORING (Groq) ---")
    scored_documents = []
    
    for doc in analyzed_documents:
        analysis = doc.get('analysis', {})
        if not analysis:
            continue
            
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
        
        response = query_stage("scoring", prompt)
        
        from utils.json_parser import extract_json_from_text
        score_data = extract_json_from_text(response)
        
        if score_data:
            doc['scoring'] = score_data
            scored_documents.append(doc)
            print(f"  Score: {score_data.get('score')}")
        else:
            print(f"  Error parsing score for {doc['title'][:20]}")
            # print(f"  Raw: {response[:100]}...")
            
        import time
        time.sleep(2) # Avoid Rate Limits
            
    return scored_documents
