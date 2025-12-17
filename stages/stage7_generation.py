from utils.llm import query_gemini
import json

def stage7_paper_generation(synthesis, knowledge_base, topic, feedback=""):
    print("\n--- STAGE 7: SCOPUS-STYLE PAPER GENERATION ---")
    
    if not synthesis:
        print("No synthesis provided.")
        return ""
    
    if feedback:
        print(f"  > Regenerating paper with feedback: {feedback}")
    
    references_list = []
    for entry in knowledge_base:
        references_list.append(f"{entry['source_title']} ({entry['url']})")
    
    ref_block = "\n".join(references_list)
    
    prompt = f"""
    You are an expert academic author. Write a complete Scopus-journal-quality research paper.
    
    Topic: {topic}
    
    CORE RESEARCH PLAN:
    Gap: {synthesis['research_gap']}
    Contribution: {synthesis['proposed_contribution']}
    Methodology: {synthesis['methodology_plan']}
    Results (Simulated): {synthesis['simulated_results_description']}
    
    PREVIOUS FEEDBACK (Must address this):
    {feedback if feedback else "None. First draft."}
    
    AVAILABLE REFERENCES (Use these as the primary citations):
    {ref_block}
    
    Structure Required:
    1. Abstract
    2. Keywords
    3. Introduction
    4. Literature Review (Use synthesis of related work)
    5. Research Gap & Objectives
    6. Methodology
    7. Results (clearly marked as simulated or conceptual)
    8. Discussion
    9. Conclusion & Future Work
    10. References (APA style, mapped to provided sources)
    
    Writing Constraints:
    - Formal academic tone only (Third-person).
    - No conversational language.
    - No plagiarism.
    - Logical structure and scholarly depth.
    - References must include the provided actual sources.
    
    OUTPUT:
    Return ONLY the completed research paper in Markdown format.
    """
    
    # Heavy content generation: Try Gemini, then fail directly to offline to save Groq limit
    paper = query_gemini(prompt, fallback_to_others=False)
    return paper
