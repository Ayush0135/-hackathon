import sys
import queue
from server import run_research_pipeline

q = queue.Queue()
run_research_pipeline("The impacts of microplastics on human biology", q)

messages = []
while not q.empty():
    messages.append(q.get())

for m in messages:
    print(m)
