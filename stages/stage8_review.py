from utils.llm import query_stage
import json

def stage8_review_paper(paper_content, topic):
    print("\n--- STAGE 8: FINAL PAPER REVIEW (Multi-Model Judge) ---")
    
    prompt = f"""
    You are a strict Senior Editor at a Scopus-indexed journal.
    
    Research Topic: "{topic}"
    
    Review the following draft research paper content (Markdown):
    {paper_content[:25000]}  # Truncate to fit context if needed
    
    Task:
    Rate this paper on a scale of 1-10 (10 being perfect for publication).
    Provide structural critique and specific actionable feedback for improvement if score < 10.
    
    Evaluation Criteria:
    1. Novelty & Contribution (Does it add value?)
    2. Clarity & Structure (Is it well-organized?)
    3. Rigor (Is the methodology sound?)
    4. Compliance (Does it look like a real academic paper?)
    
    Output Format (JSON strictly):
    {{
        "score": number,
        "critique": "string"
    }}
    """
    
    response = query_stage("review", prompt)
    response = query_stage("review", prompt)
    
    from utils.json_parser import extract_json_from_text
    review = extract_json_from_text(response)
    
    if review:
        print(f"  Paper Score: {review.get('score')}/10")
        return review
    else:
        print(f"  Raw response: {response}")
        return {"score": 4, "critique": "JSON parsing failed. Automatic integrity penalty."}

        # Previously was returning 0 and "Error ...", which works too.
