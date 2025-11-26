# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration Constants ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_GENERATE_URL = os.getenv("OLLAMA_URL") 
OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
JOB_LIB_PATH = "newJoblib.joblib"
EMBEDDING_MODEL = "bge-m3"
LLM_MODEL = "llama3.2"

# Ensure URLs are correctly configured
if not OLLAMA_GENERATE_URL or not OLLAMA_GENERATE_URL.endswith("/api/generate"):
    print("Warning: OLLAMA_URL in .env may be incorrect. Using default localhost.")
    # Fallback to ensure the URL is correct if OLLAMA_URL only contains the base address
    if OLLAMA_GENERATE_URL and not OLLAMA_GENERATE_URL.endswith("/api/generate"):
        OLLAMA_GENERATE_URL = f"{OLLAMA_GENERATE_URL.rstrip('/')}/api/generate"
    elif not OLLAMA_GENERATE_URL:
        OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
