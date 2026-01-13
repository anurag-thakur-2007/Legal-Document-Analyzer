import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from src.embeddings import get_embedding

# =====================================================
# ENVIRONMENT SETUP
# =====================================================
load_dotenv()

# =====================================================
# PINECONE INITIALIZATION
# =====================================================
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

INDEX_NAME = "contracts-index"

# HuggingFace MiniLM embedding dimension
EMBEDDING_DIM = 384

# =====================================================
# CREATE INDEX (IF NOT EXISTS)
# =====================================================
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=EMBEDDING_DIM,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=os.getenv("PINECONE_ENVIRONMENT")
        )
    )

# =====================================================
# CONNECT TO INDEX
# =====================================================
index = pc.Index(INDEX_NAME)

# =====================================================
# CONTRACT-LEVEL STORAGE
# =====================================================
def add_contract_to_pinecone(contract_id: str, embedding: list):
    """
    Store full contract embedding in Pinecone
    """
    index.upsert(vectors=[
        {
            "id": contract_id,
            "values": embedding,
            "metadata": {
                "type": "contract"
            }
        }
    ])

# =====================================================
# CLAUSE-LEVEL STORAGE
# =====================================================
def add_clauses_to_pinecone(contract_id: str, clauses: list):
    """
    Store clause-level embeddings in Pinecone
    """
    vectors = []

    for i, clause in enumerate(clauses):
        text = clause.get("text", "")
        if not text.strip():
            continue

        embedding = get_embedding(text)

        vectors.append({
            "id": f"{contract_id}_clause_{i}",
            "values": embedding,
            "metadata": {
                "contract_id": contract_id,
                "type": "clause",
                "clause_index": i,
                "text": text
            }
        })

    if vectors:
        index.upsert(vectors=vectors)

# =====================================================
# AGENT RESULT STORAGE
# =====================================================
def store_agent_result(contract_id: str, agent_name: str, agent_output: dict):
    """
    Store intermediate agent result in Pinecone
    """
    text = json.dumps(agent_output, ensure_ascii=False)
    embedding = get_embedding(text)

    vector_id = f"{contract_id}_{agent_name}"

    index.upsert(vectors=[
        {
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "contract_id": contract_id,
                "type": "agent_result",
                "agent": agent_name
            }
        }
    ])

# =====================================================
# SIMILARITY SEARCH
# =====================================================
def search_similar_contracts(query_embedding: list, top_k: int = 5):
    """
    Perform similarity search over stored contracts
    """
    return index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
