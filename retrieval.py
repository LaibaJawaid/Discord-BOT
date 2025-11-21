# retrieval.py
import asyncio
import time
import json
import joblib
import numpy as np
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer
from config import EMBED_FILE, CHUNKS_FILE, OLLAMA_URL, OLLAMA_MODEL

# -----------------------------
# CONFIG
# -----------------------------
TOP_K = 3
SIMILARITY_THRESHOLD = 0.35
OLLAMA_TIMEOUT = 30
HTTP_RETRIES = 2

# -----------------------------
# LOAD RESOURCES
# -----------------------------
print("Loading embeddings and chunks...")
emb_matrix = joblib.load(EMBED_FILE)
emb_matrix = np.asarray(emb_matrix)

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded embeddings shape: {emb_matrix.shape}")
print(f"Loaded chunks: {len(chunks)}")

# Load MPNet model ONCE
executor = ThreadPoolExecutor(max_workers=2)
s2_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")


# -----------------------------
# UTILITIES
# -----------------------------
def cosine_sim(vec, matrix):
    """Cosine similarity between vector and matrix."""
    vec_norm = np.linalg.norm(vec)
    mat_norms = np.linalg.norm(matrix, axis=1)
    denom = mat_norms * vec_norm
    denom[denom == 0] = 1e-10
    return (matrix @ vec) / denom


async def embed_query_async(text: str):
    """Encode query asynchronously without blocking event loop."""
    loop = asyncio.get_running_loop()
    emb = await loop.run_in_executor(
        executor,
        lambda: s2_model.encode(text, convert_to_numpy=True)
    )
    return np.asarray(emb)


def retrieve_top_k(query_emb):
    sims = cosine_sim(query_emb, emb_matrix)
    top_idx = np.argsort(sims)[-TOP_K:][::-1]
    return [{"index": int(i), "score": float(sims[i]), "chunk": chunks[i]}
            for i in top_idx]


async def call_ollama(prompt: str):
    """Async call to Ollama with retries."""
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}

    for attempt in range(HTTP_RETRIES + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OLLAMA_URL,
                    json=payload,
                    timeout=OLLAMA_TIMEOUT
                ) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"Ollama HTTP {resp.status}")

                    data = await resp.json()

                    # Try standard response keys
                    return data.get("response") or data.get("text") or ""

        except Exception as e:
            print(f"Ollama error attempt {attempt+1}: {e}")
            if attempt == HTTP_RETRIES:
                raise
            await asyncio.sleep(0.5)

    raise RuntimeError("Ollama failed all retries.")


# -----------------------------
# MAIN RAG FUNCTION
# -----------------------------
async def generate_answer(query: str):
    """Embed → Retrieve → Call Ollama."""
    print(f"[RAG] Query: {query}")

    # Embed
    query_emb = await embed_query_async(query)

    # Retrieve
    top = retrieve_top_k(query_emb)
    best_score = top[0]["score"]
    print(f"[RAG] Best score: {best_score:.4f}")

    if best_score < SIMILARITY_THRESHOLD:
        return "The dataset does not mention this specifically."

    # Build context
    context = ""
    for t in top:
        chunk = t["chunk"]
        idx = t["index"]
        scr = t["score"]

        text = chunk["content"]
        if len(text) > 600:
            text = text[:600] + "..."

        context += f"[{idx} score={scr:.4f}] Wife: {chunk['wife_name']}\n{text}\n\n"

    # Prompt
    prompt = f"""
You are an Islamic knowledge assistant.
Answer ONLY using the context below.
If answer is missing, reply exactly: "The dataset does not mention this specifically."

CONTEXT:
{context}

QUESTION:
{query}

Provide a clear answer and include (source#INDEX).
"""

    # Generate
    reply = await call_ollama(prompt)

    # Ensure source tagging exists
    if "source#" not in reply.lower():
        src = ", ".join(str(t["index"]) for t in top)
        reply += f"\n\n(sources: {src})"

    return reply.strip()
