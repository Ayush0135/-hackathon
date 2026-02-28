from stages.stage1_topic import stage1_topic_decomposition
from stages.stage2_discovery import stage2_document_discovery
import traceback
try:
    print("STARTING")
    res = stage1_topic_decomposition("impact of microplastics")
    docs = stage2_document_discovery(res)
    print(f"Found {len(docs)} docs")
except Exception as e:
    traceback.print_exc()
