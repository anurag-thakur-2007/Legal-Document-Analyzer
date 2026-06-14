import os
import json
import time
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
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY)
else:
    pc = None

# Create a new index version to avoid dimension conflicts
INDEX_NAME = "contracts-index-v2"

# text-embedding-3-small dimension
EMBEDDING_DIM = 1536

# =====================================================
# CREATE INDEX (IF NOT EXISTS)
# =====================================================
if pc:
    try:
        if INDEX_NAME not in pc.list_indexes().names():
            pc.create_index(
                name=INDEX_NAME,
                dimension=EMBEDDING_DIM,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
                )
            )
            # Wait for index to be initialized
            time.sleep(5)
    except Exception as e:
        print(f"Error initializing Pinecone index: {e}")
        pc = None

# =====================================================
# CONNECT TO INDEX
# =====================================================
index = pc.Index(INDEX_NAME) if pc else None

# =====================================================
# CONTRACT-LEVEL STORAGE
# =====================================================
def add_contract_to_pinecone(contract_id: str, embedding: list):
    """
    Store full contract embedding in Pinecone
    """
    if not index or not embedding:
        return

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
def add_clauses_to_pinecone(contract_id: str, clauses: dict):
    """
    Store clause-level embeddings in Pinecone
    """
    if not index:
        return

    vectors = []

    for clause_name, text in clauses.items():
        if not text or not str(text).strip():
            continue

        embedding = get_embedding(str(text))
        if not embedding:
            continue

        vectors.append({
            "id": f"{contract_id}_clause_{clause_name}",
            "values": embedding,
            "metadata": {
                "contract_id": contract_id,
                "type": "clause",
                "clause_name": clause_name,
                "text": str(text)[:1000] # truncate metadata if too long
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
    if not index:
        return

    text = json.dumps(agent_output, ensure_ascii=False)
    embedding = get_embedding(text)
    if not embedding:
        return

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
    if not index:
        return []
        
    return index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
