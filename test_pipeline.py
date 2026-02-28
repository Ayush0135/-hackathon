import queue
import string
import threading
from server import run_research_pipeline

def consume(q):
    while True:
        try:
            msg = q.get(timeout=10)
            print("WS->", msg)
            if msg == "COMPLETE":
                break
        except Exception:
            print("Timeout reading from queue.")
            break

q = queue.Queue()
t = threading.Thread(target=run_research_pipeline, args=("impact of microplastics", q))
t.start()
consume(q)
