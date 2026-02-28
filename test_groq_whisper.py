import os
import asyncio
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

print("Groq Client initialized.")
