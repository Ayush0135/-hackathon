from utils.llm import query_stage
import time
from utils.json_parser import extract_json_from_text
from concurrent.futures import ThreadPoolExecutor, as_completed

def chunk_text(text, chunk_size=15000, overlap=1000):
    """
    Splits text into overlapping chunks.
    """
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        # Move forward, but backtrack by overlap amount
        start += (chunk_size - overlap)
        
        # Avoid infinite loop if overlap >= chunk_size (shouldn't happen with these defaults)
        if start >= text_len:
            break
            
    return chunks

def analyze_single_document(doc):
    try:
        print(f"Analyzing: {doc['title'][:40]}...") # Log start
        full_text = doc['raw_text']
        
        # Strategy Decision: Chunk vs Whole
        # Reduced threshold to 7k chars to comfortably fit inside tight LLM context windows
        if len(full_text) > 7000:
            # print(f"  - Large Doc ({len(full_text)} chars). Chunking...")
            all_chunks = chunk_text(full_text, chunk_size=7000, overlap=500)
            
            # Smart Selection: Limit to max 3 chunks to prevent exploding final prompt tokens
            if len(all_chunks) > 3:
                # First, Middle, Last
                mid = len(all_chunks) // 2
                selected_chunks = [all_chunks[0], all_chunks[mid], all_chunks[-1]]
            else:
                selected_chunks = all_chunks
            
            chunk_summaries = []
            
            # Sequential Chunk Analysis to prevent overusing TPM limits
            for i, chunk in enumerate(selected_chunks):
                chunk_prompt = f"""
                Analyze this segment (Part {i+1}) of "{doc['title']}".
                Segment: {chunk[:7500]}
                Task: Extract Research Problem, Methodology, Findings, Limitations.
                Output: Concise bullet points.
                """
                try:
                    res = query_stage("analysis", chunk_prompt, skip_memory=True)
                    if res: chunk_summaries.append(res)
                    time.sleep(1) # Pace requests slightly
                except Exception as e:
                    print(f"    x Chunk analysis failed: {e}")
                    pass
            
            text_context = "\n".join(chunk_summaries)[:8000]
        else:
            text_content = full_text[:8000] 
            text_context = text_content

        prompt = f"""
        Analyze the following research document content (or extracted summaries of it).
        
        Document Title: {doc['title']}
        
        Content/Context:
        {text_context}
        
        Task:
        1. Extract the research problem (Be specific).
        2. Identify methodology (Include specific model names, algorithms, parameter counts, equations if described).
        3. Summarize key findings (Include quantitative metrics like accuracy, F1-score, latency, user study statistics where available).
        4. Identify limitations and weaknesses.
        5. Detect explicit or implicit research gaps.
        6. Assess novelty.
        7. Evaluate detailedness: Does it provide implementation details?
        
        Constraint:
        - All output must be paraphrased. Do NOT copy text verbatim.
        - Focus on extracting *knowledge*, not just describing the paper.
        
        Output Format:
        Return ONLY the JSON object below. Do not add markdown or conversational text.
        {{
            "research_problem": "string",
            "methodology": "string",
            "key_findings": "string",
            "limitations": "string",
            "research_gaps": "string",
            "novelty_assessment": "string",
            "technical_depth_score": 5, 
            "missing_entities": "string"
        }}
        """
        
        response = query_stage("analysis", prompt, skip_memory=True)
        
        # Robust Parsing
        analysis = extract_json_from_text(response)
        
        if not analysis:
            print(f"  ! Warning: Could not parse JSON for {doc['title'][:15]}. Using raw text fallback.")
            analysis = {
                "research_problem": "JSON Parsing Failed",
                "methodology": "See findings",
                "key_findings": response if response else "No content returned",
                "limitations": "N/A",
                "research_gaps": "N/A",
                "novelty_assessment": "N/A",
                "technical_depth_score": 0,
                "missing_entities": "Parsing Failed"
            }
        
        doc['analysis'] = analysis
        print(f"  + Analysis Complete: {doc['title'][:30]}...")
        return doc
        
    except Exception as e:
        print(f"  x Error analyzing {doc['title'][:20]}: {e}")
        return None

def stage3_document_analysis(documents):
    print("\n--- STAGE 3: DOCUMENT ANALYSIS (Sequential) ---")
    analyzed_documents = []
    
    # Process documents in parallel
    # Increased speed by using threading, relying on robust fallback for rate limits
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_doc = {executor.submit(analyze_single_document, doc): doc for doc in documents}
        
        for future in as_completed(future_to_doc):
            result = future.result()
            if result:
                analyzed_documents.append(result)
                
    return analyzed_documents
