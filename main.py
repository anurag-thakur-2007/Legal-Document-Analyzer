import os
import json
from dotenv import load_dotenv

from src.parser import load_contract
from src.embeddings import get_embedding
from src.vector_store import add_contract_to_pinecone
from src.langgraph_workflow import build_workflow
from src.analyzer.clause_extractor import extract_clauses

# 🔧 Development flag (Optimization 4)
DEV_MODE = True


def main():
    load_dotenv()

    print("\n📄 Loading Contract...")
    text = load_contract("assets/service_agreement_sample.pdf")

    print("🧩 Extracting Clauses...")
    clause_data = extract_clauses(text)

    if not DEV_MODE:
        print("🔍 Generating Embeddings...")
        embedding = get_embedding(text)

        print("🧠 Storing in Pinecone...")
        add_contract_to_pinecone("contract_1", embedding)
    else:
        print("⚡ DEV MODE: Skipping embeddings & Pinecone")

    print("\n🔗 Running LangGraph Workflow...")
    graph = build_workflow()

    final_state = graph.invoke({"contract_text": text})

    print("\n===== FINAL REPORT =====")
    print(json.dumps(final_state["final_report"], indent=2))

    print("\n✅ Workflow Completed!")


if __name__ == "__main__":
    main()
