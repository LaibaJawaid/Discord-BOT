import json
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer

# -------- LOAD MODEL (MPNet 768 dim) ----------
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

# -------- LOAD CHUNKS ----------
with open("final_Chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

# -------- EMBED TEXTS ----------
texts = [c["content"] for c in chunks]
emb_matrix = model.encode(texts, convert_to_numpy=True)  # shape = (N, 768)

# -------- SAVE EMBEDDINGS AS .joblib ----------
joblib.dump(emb_matrix, "embeddings.joblib")

# -------- ADD EMBEDDINGS INTO EACH JSON OBJECT ----------
final_chunks = []
for idx, c in enumerate(chunks):
    obj = {
        "wife_name": c["wife_name"],
        "content": c["content"],
        "embedding": emb_matrix[idx].tolist()  # convert numpy → list for JSON
    }
    final_chunks.append(obj)

# -------- SAVE TOKEN/TOON STYLE JSON ----------
with open("chunks_with_embeds_v2.json", "w", encoding="utf-8") as f:
    json.dump(final_chunks, f, indent=2, ensure_ascii=False)

print("Saved: embeddings_v2.joblib + chunks_with_embeds_v2.json")