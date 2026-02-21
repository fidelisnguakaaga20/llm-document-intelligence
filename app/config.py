import os
from dotenv import load_dotenv

load_dotenv()  # loads .env from project root

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")