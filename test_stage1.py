from stages.stage1_topic import stage1_topic_decomposition
import traceback
try:
    print("STARTING")
    res = stage1_topic_decomposition("impact of microplastics")
    print("FINISHED:", res)
except Exception as e:
    traceback.print_exc()
