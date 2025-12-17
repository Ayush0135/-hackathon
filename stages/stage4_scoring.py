from utils.llm import query_groq
import json

def stage4_academic_scoring(analyzed_documents, topic):
    print("\n--- STAGE 4: ACADEMIC SCORING (Groq) ---")
    scored_documents = []
    
    for doc in analyzed_documents:
        analysis = doc.get('analysis', {})
        if not analysis:
            continue
            
        print(f"Scoring: {doc['title'][:50]}...")
        
        prompt = f"""
        Role: Strict Academic Reviewer.
        Target Research Topic: "{topic}"
        
        Document Title: {doc['title']}
        Analysis Summary:
        - Problem: {analysis.get('research_problem')}
        - Method: {analysis.get('methodology')}
        - Findings: {analysis.get('key_findings')}
        - Novelty: {analysis.get('novelty_assessment')}
        
        Evaluate based on:
        1. Novelty
        2. Methodological rigor
        3. Relevance to the research topic
        4. Academic clarity
        5. Suitability for Scopus-indexed journals
        
        Return ONLY valid JSON:
        {{
          "score": number (0-10),
          "strengths": "string",
          "weaknesses": "string"
        }}
        
        No explanations. No markdown.
        """
        
        response = query_groq(prompt, json_mode=True, fallback_to_others=True)
        try:
            # clean up potential markdown wrappers even if we asked for strict json
            cleaned = response.replace("```json", "").replace("```", "").strip()
            score_data = json.loads(cleaned)
            doc['scoring'] = score_data
            scored_documents.append(doc)
            print(f"  Score: {score_data.get('score')}")
        except Exception as e:
            print(f"  Error scoring document: {e}")
            continue
            
    return scored_documents
