# test_groq.py
import os
from dotenv import load_dotenv
load_dotenv()  # charge .env si présent

print("Have GROQ_API_KEY:", bool(os.getenv("GROQ_API_KEY")))

try:
    from groq import Groq
    client = Groq()
    models = client.models.list().data
    print("Models available:", len(models))
    print("OK ✅")
except Exception as e:
    print("Error:", e)

