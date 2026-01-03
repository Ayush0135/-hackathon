from utils.search import google_search, download_and_parse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_search_item(item):
    """
    Helper function to process a single search result:
    - Filters domains
    - Downloads and parses content
    """
    url = item.get('link')
    title = item.get('title')
    snippet = item.get('snippet')
    
    # Filter trivial non-academic URLs (heuristic)
    # USER REQUEST: REMOVE AUTHENTIC FEATURE/FILTER - Fetch ALL
    # skip_domains = ['youtube.com', 'news.google.com', 'wikipedia.org']
    # if any(x in url for x in skip_domains):
    #     # Silent skip or log if needed
    #     return None


    # Efficiency: Relevance Check - REMOVED strictly to avoid zero results
    # We trust the search engine and Stage 3 analysis more than a snippet check
    # subtopic_name = item.get('subtopic', '')
    # if subtopic_name:
    #     keywords = [k.lower() for k in subtopic_name.split() if len(k) > 3]
    #     text_to_check = (title + " " + snippet).lower()
    #     if keywords and not any(k in text_to_check for k in keywords):
    #          return None

    try:
        raw_text = download_and_parse(url)
        if len(raw_text) < 500: # Too short to be a paper
            return None
        
        return {
            "title": title,
            "url": url,
            "snippet": snippet,
            "raw_text": raw_text
        }
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None

def stage2_document_discovery(decomposition_data):
    print("\n--- STAGE 2: DOCUMENT DISCOVERY ---")
    
    all_documents = []
    seen_urls = set()
    search_candidates = []
    
    if not decomposition_data or 'subtopics' not in decomposition_data:
        print("Invalid input for Stage 2")
        return []

    # 1. Gather all candidates concurrently
    def execute_search_query(subtopic, query):
        results = []
        # Enforce academic constraints in query - REMOVED
        # USER REQUEST: Fetch ALL documents, no authentic filtering
        academic_query = query 
        print(f"  [Search] Querying: {academic_query}")
        
        try:
            # Small random delay to stagger requests slightly
            time.sleep(0.1) 
            search_res = google_search(academic_query, num_results=6) # Reduced from 8 to 6 for speed
            for item in search_res:
                item['subtopic'] = subtopic['name']
                results.append(item)
        except Exception as e:
            print(f"    Error querying Google for '{query}': {e}")
        return results

    # Flatten all queries
    all_queries = []
    for subtopic in decomposition_data['subtopics']:
        for query in subtopic['search_queries']:
            all_queries.append((subtopic, query))

    print(f"Executing {len(all_queries)} search queries sequentially...")
    
    # Execute sequentially to avoid 429 Rate Limits on Google Custom Search API
    for subtopic, query in all_queries:
        results = execute_search_query(subtopic, query)
        for item in results:
            url = item.get('link')
            if url in seen_urls:
                continue
            seen_urls.add(url)
            search_candidates.append(item)
        
        # Respect API Rate Limits
        time.sleep(2)

    # Limit to top 20 candidates total (User Constraint)
    if len(search_candidates) > 20:
        print(f"Limiting candidates from {len(search_candidates)} to top 20.")
        search_candidates = search_candidates[:20]

    print(f"\nDownloading and parsing {len(search_candidates)} candidates in parallel...")

    # 2. Process downloads in parallel
    # max_workers=5 is a safe number to not overwhelm network or get IP blocked
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_item = {executor.submit(process_search_item, item): item for item in search_candidates}
        
        for future in as_completed(future_to_item):
            result = future.result()
            if result:
                all_documents.append(result)
                print(f"    + Downloaded: {result['title'][:40]}...")
            else:
                # Optional: indicate skip/failure
                pass
    
    print(f"Total documents retrieved: {len(all_documents)}")
    return all_documents
