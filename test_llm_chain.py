import sys
from utils.llm import query_stage
from utils.search import google_search

try:
    print("Testing topic stage...")
    res = query_stage("topic", "What are the impacts of quantum computing on cryptography?")
    print("TOPIC:", res[:100])
except Exception as e:
    print("TOPIC FAIL:", e)

try:
    print("Testing search fallback...")
    res_search = google_search("quantum computing cryptography impact")
    print("SEARCH ITEMS:", len(res_search))
except Exception as e:
    print("SEARCH FAIL:", e)
