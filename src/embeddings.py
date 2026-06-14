import os
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Use industry-standard OpenAI embeddings
try:
    embeddings_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
except Exception as e:
    print(f"Failed to initialize OpenAI Embeddings: {e}")
    embeddings_model = None

def get_embedding(text: str):
    """
    Return embedding for a piece of text using OpenAI.
    """
    if not embeddings_model:
        return []
    
    # OpenAI embeddings handles text seamlessly
    return embeddings_model.embed_query(text)

