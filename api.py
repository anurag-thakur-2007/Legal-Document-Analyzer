from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import tempfile
import os
import json
from src.parser import load_contract
from src.analyzer.clause_extractor import extract_clauses
from src.langgraph_workflow import build_workflow
from src.vector_store import add_contract_to_pinecone, add_clauses_to_pinecone, store_agent_result
from src.embeddings import get_embedding
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI(title="Contract Analysis API", description="FastAPI Backend for LLM Contract Analysis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    tone: str
    focus: List[str]
    risk_threshold: float

@app.post("/analyze")
async def analyze_contract(
    file: UploadFile = File(...),
    tone: str = Form(...),
    focus: str = Form(...),
    risk_threshold: float = Form(...),
    contract_id: str = Form(...)
):
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        # 1️⃣ Extract text from uploaded PDF
        contract_text = load_contract(tmp_path)
        os.remove(tmp_path)

        # 🚀 Store Full Contract in Pinecone
        try:
            full_embedding = get_embedding(contract_text[:8000]) # embed the text (limit size for safety)
            if full_embedding:
                add_contract_to_pinecone(contract_id, full_embedding)
        except Exception as e:
            print(f"Failed to store full contract embedding: {e}")

        # 2️⃣ Clause extraction
        clauses_data = extract_clauses(contract_text)
        clauses = clauses_data.get("clauses", {})

        # 🚀 Store Clauses in Pinecone
        try:
            if clauses:
                add_clauses_to_pinecone(contract_id, clauses)
        except Exception as e:
            print(f"Failed to store clauses in Pinecone: {e}")

        # 3️⃣ Run LangGraph workflow
        graph = build_workflow()

        focus_list = json.loads(focus)

        final_state = graph.invoke({
            "contract_text": contract_text,
            "clauses": clauses_data,
            "tone": tone,
            "focus": focus_list,
            "risk_threshold": risk_threshold
        })

        result = final_state.get("final_report", {})
        
        # 🚀 Store Agent Results in Pinecone
        try:
            agent_outputs = final_state.get("analysis", {})
            if isinstance(agent_outputs, dict):
                for agent_name, agent_out in agent_outputs.items():
                    store_agent_result(contract_id, agent_name, agent_out)
        except Exception as e:
            print(f"Failed to store agent results in Pinecone: {e}")

        normalized_result = {
            "summary": result.get("summary")
            or result.get("executive_summary")
            or result.get("overall_summary")
            or "Summary not generated",

            "confidence": result.get("confidence", 0.95),
            "risk_score": result.get("risk_score", 0.5),
            "domains": result.get("analysis", {})
        }

        return normalized_result

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
