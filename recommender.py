import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

def load_data():
    df = pd.read_csv("data/songs.csv")
    df["embedding"] = df["mood"].apply(lambda x: model.encode(x))
    return df

def recommend(age, genres, languages, df, top_n=5):
    user_profile = f"""
    Age: {age}
    Preferred genres: {", ".join(genres)}
    Preferred languages: {", ".join(languages)}
    """

    user_emb = model.encode(user_profile)

    df["score"] = df["embedding"].apply(
        lambda x: cosine_similarity([user_emb], [x])[0][0]
    )

    return df.sort_values("score", ascending=False).head(top_n)
