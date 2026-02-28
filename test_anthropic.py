import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import os
from dotenv import load_dotenv
load_dotenv()
try:
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    res = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=100,
        messages=[{"role": "user", "content": "hello"}]
    )
    print("Success:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
