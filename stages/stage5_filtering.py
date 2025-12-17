def stage5_selection_filtering(scored_documents):
    print("\n--- STAGE 5: SELECTION & FILTERING ---")
    
    high_quality_docs = []
    seen_titles = set()
    
    for doc in scored_documents:
        score = doc.get('scoring', {}).get('score', 0)
        title = doc.get('title', '').lower()
        
        if score < 7:
            print(f"Discarding: {title[:30]}... (Score: {score})")
            continue
            
        if title in seen_titles:
            print(f"Discarding duplicate: {title[:30]}")
            continue
            
        seen_titles.add(title)
        high_quality_docs.append(doc)
        
    print(f"Retained {len(high_quality_docs)} high-quality documents.")
    
    # "Merge complementary insights into a unified knowledge base"
    # We will compile the analysis fields into a single context object for the next stage.
    knowledge_base = []
    for doc in high_quality_docs:
        entry = {
            "source_title": doc['title'],
            "url": doc['url'],
            "analysis": doc['analysis'],
            "strengths": doc['scoring'].get('strengths'),
            "weaknesses": doc['scoring'].get('weaknesses')
        }
        knowledge_base.append(entry)
        
    return knowledge_base
