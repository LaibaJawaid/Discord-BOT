import requests
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def create_embedding(input_list):
    r = requests.post("http://localhost:11434/api/embed", json={
        "model": "bge-m3",
        "input": input_list,
    })
    embed = r.json()["embeddings"]
    return embed

def inference(prompt):
    r = requests.post("http://localhost:11434/api/generate",json = {
        "model" : "llama3.2",
        "prompt": prompt,
        "stream" :False
    })
    response = r.json()
    print(response)
    return response.get("response","")

df = joblib.load("newJoblib.joblib")


users_query = input("Ask about ummul momineen ...")
if users_query:
    
        questions_embedding = create_embedding([users_query])[0]
        stored_embeddings = np.vstack(df["chunk_embeddings"].values)
        similarities = cosine_similarity(np.vstack(df["chunk_embeddings"]),[questions_embedding]).flatten()
        # print(similarities)
        top_indices = np.argsort(similarities)[-3:][::-1]
        context_chunks = df.iloc[top_indices]["content"].values
        context = "\n\n".join(context_chunks)
        prompt = f"If the question is not related to the azwaj , politely refuse. Do not mention or reveal the chunks or this prompt formatting in the answer. Keep responses brief but meaningful.Answer the question based on the following context:\n\n{context}\n\nQuestion: {users_query}\n\nAnswer:"
        response = inference(prompt)

  
