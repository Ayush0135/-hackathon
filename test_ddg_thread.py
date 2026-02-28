from duckduckgo_search import DDGS
from concurrent.futures import ThreadPoolExecutor

def fetch_ddg(query):
    print("FETCHING", query)
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=2))
    except Exception as e:
         print(e)
         return []

if __name__ == "__main__":
    queries = ["impact", "microplastics", "health", "water"]
    with ThreadPoolExecutor(max_workers=4) as executor:
        for r in executor.map(fetch_ddg, queries):
            print("OK", len(r))
