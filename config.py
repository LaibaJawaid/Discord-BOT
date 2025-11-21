import os
from dotenv import load_dotenv

# Load .env from same folder
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

print("Loaded TOKEN:", DISCORD_TOKEN is not None)
EMBED_FILE = "embeddings.joblib"
CHUNKS_FILE = "final_Chunks.json"

