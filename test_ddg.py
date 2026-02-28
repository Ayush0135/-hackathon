from duckduckgo_search import DDGS
try:
    with DDGS() as ddgs:
        print("Using DDGS with context manager")
        results = list(ddgs.text("microplastics", max_results=2))
        print("results:", results)
except Exception as e:
    import traceback
    traceback.print_exc()

import utils.search as search
print(search.google_search("impact of microplastics", num_results=2))
