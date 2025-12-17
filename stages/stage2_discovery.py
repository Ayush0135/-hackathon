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
    skip_domains = ['youtube.com', 'news.google.com', 'wikipedia.org']
    if any(x in url for x in skip_domains):
        # Silent skip or log if needed
        return None

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

    # 1. Gather all candidates first
    for subtopic in decomposition_data['subtopics']:
        print(f"Searching for subtopic: {subtopic['name']}")
        for query in subtopic['search_queries']:
            # Enforce academic constraints in query
            academic_query = f"{query} filetype:pdf OR site:.edu OR site:.org \"research paper\""
            print(f"  Querying: {academic_query}")
            
            try:
                # Small delay to respect Google API rate limits
                time.sleep(0.5)
                results = google_search(academic_query, num_results=3)
                
                for item in results:
                    url = item.get('link')
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    
                    print(f"    Found candidate: {item.get('title')[:50]}... ({url})")
                    search_candidates.append(item)
            except Exception as e:
                print(f"    Error querying Google: {e}")

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
