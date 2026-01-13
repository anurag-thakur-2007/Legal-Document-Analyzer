from sentence_transformers import SentenceTransformer

# Load a FREE HuggingFace embedding model
# This model generates 384-dimensional embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text: str):
    """
    Return embedding for a piece of text using HuggingFace model.
    """
    embedding = model.encode(text)
    return embedding.tolist()
