from utils.llm import execute_strategies, _resolve_strategy, STAGE_CONFIG
import traceback
import sys

sys.stdout.write("Testing execute_strategies with topic config...\n")
try:
    strategies = [_resolve_strategy(m) for m in STAGE_CONFIG['topic']]
    sys.stdout.write(f"Resolved strategies: {len(strategies)}\n")
    res = execute_strategies(strategies, "hello world. Please reply with strictly: {'hello': 'world'} and format as a JSON object.")
    sys.stdout.write(f"FINISHED: {res}\n")
except Exception as e:
    traceback.print_exc()
