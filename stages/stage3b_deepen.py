from utils.llm import query_stage
from utils.json_parser import extract_json_from_text
from stages.stage2_discovery import stage2_document_discovery
from stages.stage3_analysis import stage3_document_analysis
import json

def stage3b_deepen_research(analyzed_docs, topic):
    """
    Analyzes the initial research for gaps and performs a recursive deep dive.
    """
    print("\n--- STAGE 3b: DEEP KNOWLEDGE RECURSION ---")
    
    # 1. Assess current depth
    valid_docs = [d for d in analyzed_docs if 'analysis' in d]
    if not valid_docs:
        print("No valid documents to deepen.")
        return []

    # Collect gaps and missing entities
    gaps_context = ""
    for d in valid_docs:
        analysis = d['analysis']
        gaps_context += f"- Source: {d['title']}\n"
        gaps_context += f"  Missing: {analysis.get('missing_entities', 'N/A')}\n"
        gaps_context += f"  Gaps: {analysis.get('research_gaps', 'N/A')}\n"

    # 2. Generate Targeted Queries
    prompt = f"""
    The user wants "Deep Knowledge" on the topic: "{topic}".
    Here is the analysis of the first round of research papers:
    
    {gaps_context[:8000]}
    
    Task:
    Identify specific missing technical details, implementation specifics, or data points.
    Generate 3-5 HIGHLY SPECIFIC search queries to find this missing information.
    Focus on getting concrete numbers, algorithms, or comparison data.
    
    Output Format (JSON string list):
    ["query 1", "query 2", ...]
    """
    
    print("  Identifying knowledge gaps...")
    # Using 'analysis' stage config (Groq/Anthropic/Ollama)
    response = query_stage("analysis", prompt)
    
    new_queries_list = extract_json_from_text(response)
    
    if not new_queries_list or not isinstance(new_queries_list, list):
        print("  No further deep queries generated.")
        return []

    print(f"  Generated {len(new_queries_list)} deep-dive queries:")
    for q in new_queries_list:
        print(f"   > {q}")

    # 3. Construct a fake 'decomposition' structure for Stage 2
    # Stage 2 expects: {'subtopics': [{'name': 'Deep Dive', 'search_queries': [...]}]}
    deep_decomposition = {
        'subtopics': [
            {
                'name': 'Deep Dive Refinement',
                'search_queries': new_queries_list
            }
        ]
    }
    
    # 4. Run Stage 2 & 3 recursively
    print("  Executing Recursive Search...")
    new_raw_docs = stage2_document_discovery(deep_decomposition)
    
    if not new_raw_docs:
        print("  No new documents found in deep dive.")
        return []
        
    print("  Analyzing Deep Dive Documents...")
    new_analyzed_docs = stage3_document_analysis(new_raw_docs)
    
    return new_analyzed_docs
