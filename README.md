# ⚖️ AI Legal Contract Analyzer  
### Multi-Agent Generative AI System for Contract Risk Assessment

---

## 📌 Overview

The **AI Legal Contract Analyzer** is a multi-agent Generative AI system designed to analyze legal contracts across multiple domains:

- ⚖️ Legal Risk  
- 💰 Financial Exposure  
- 📋 Compliance Gaps  
- ⚙️ Operational Feasibility  

The system leverages:

- Large Language Models (LLMs)  
- LangGraph multi-agent orchestration  
- Retrieval-Augmented Generation (RAG)  
- Vector embeddings with Pinecone  
- Streamlit Cloud deployment  

This project demonstrates a **real-world implementation** of:

- Multi-Agent AI Architecture  
- LLM Orchestration  
- RAG Pipelines  
- Vector Database Integration  
- Cloud Deployment  

---

## 🏗️ Architecture

```
User Upload → Contract Parsing → Clause Extraction → 
Planner Module → Multi-Agent Execution (LangGraph) → 
LLM Analysis → Postprocessing → Vector Storage → UI Display
```

---

## 🧠 Core Components

### 1️⃣ Contract Parsing Layer

- PDF ingestion  
- Text extraction using PyPDF2  
- Structured clause segmentation  

---

### 2️⃣ Planner Module

Defines and orchestrates AI agents:

- Legal Agent  
- Finance Agent  
- Compliance Agent  
- Operations Agent  

Responsibilities:

- Domain classification  
- Task routing  
- Agent coordination via LangGraph  

---

### 3️⃣ Multi-Agent System

Each agent:

- Receives contract text  
- Uses domain-specific LLM prompts  
- Produces structured findings  

Example:

```python
AGENT_ROLES = {
    "Legal": {
        "objective": "Assess legal enforceability and liability",
        "risk_type": "Legal Risk"
    },
    "Finance": {
        "objective": "Evaluate financial exposure and penalties",
        "risk_type": "Financial Risk"
    },
    "Compliance": {
        "objective": "Detect regulatory and compliance gaps",
        "risk_type": "Compliance Risk"
    },
    "Operations": {
        "objective": "Assess operational feasibility and constraints",
        "risk_type": "Operational Risk"
    }
}
```

---

### 4️⃣ LangGraph Workflow

LangGraph manages:

- Agent execution order  
- State propagation  
- Final report aggregation  

Ensures:

- Modular reasoning  
- Clear agent responsibility  
- Scalable architecture  

---

### 5️⃣ LLM Integration (HuggingFace API)

Uses:

```python
from huggingface_hub import InferenceClient
```

Model example:

```
google/gemma-2b-it
```

Features:

- API-based inference (no heavy local models)  
- Streamlit Cloud safe  
- Fallback logic for stability  

---

### 6️⃣ Embeddings & Pinecone Vector DB

- HuggingFace embeddings  
- Stored in Pinecone (cosine similarity)  

Enables:

- Similar contract retrieval  
- Agent result memory storage  
- RAG-style enhancement  

---

### 7️⃣ Database Layer (SQLite)

Tables:

- contracts  
- analyses  
- findings  
- feedback  

Used for:

- Historical tracking  
- Risk score analytics  
- Session persistence  

---

## 🎨 Frontend (Streamlit)

Features:

- Modern dark-themed UI  
- Configurable analysis parameters  
- Risk threshold slider  
- Domain filtering  
- Feedback submission  
- Historical analysis tracking  

---

## ⚙️ Tech Stack

| Category        | Tools                         |
|----------------|--------------------------------|
| Language        | Python                         |
| LLM API         | HuggingFace Inference API      |
| Orchestration   | LangGraph                      |
| LLM Framework   | LangChain ecosystem            |
| Vector DB       | Pinecone                       |
| Embeddings      | HuggingFace                    |
| UI              | Streamlit                      |
| Database        | SQLite                         |
| Deployment      | Streamlit Cloud                |

---

## 🚀 Installation (Local Setup)

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/Legal-Document-Analyzer.git
cd Legal-Document-Analyzer
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Create `.env` File

```
HF_API_TOKEN=your_huggingface_api_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_region
```

### 5️⃣ Run Application

```bash
streamlit run app.py
```

---

## ☁️ Streamlit Cloud Deployment

1. Push code to GitHub  
2. Connect repository to Streamlit Cloud  
3. Add Secrets:

```
HF_API_TOKEN="your_hf_token"
PINECONE_API_KEY="your_pinecone_key"
PINECONE_ENVIRONMENT="your_region"
```

4. Deploy 🚀  

---

## 📊 Example Output

```json
{
  "summary": "This contract presents moderate legal and financial risks...",
  "confidence": 0.87,
  "risk_score": 0.65,
  "domains": {
    "Legal": [...],
    "Finance": [...],
    "Compliance": [...]
  }
}
```

---

## 🧪 Key Features

- ✔ Multi-Agent AI Architecture  
- ✔ Retrieval-Augmented Generation (RAG)  
- ✔ Vector Embedding Storage  
- ✔ Parallel Agent Execution  
- ✔ LLM API Optimization  
- ✔ Production Deployment  
- ✔ Fallback Stability Mode  
- ✔ Risk Scoring & Confidence Metrics  

---

## 📚 Skills Demonstrated

- Generative AI System Design  
- Transformer-based LLM usage  
- Embeddings & Vector Search  
- RAG Architecture  
- Prompt Engineering  
- AI Agent Orchestration  
- Python Backend Development  
- Cloud Deployment  
- API Integration  
- Performance Optimization  

---

## 🔮 Future Improvements

- Fine-tuning small transformer models  
- Structured risk quantification  
- Multi-turn agent collaboration  
- Clause-level citation tracing  
- Compliance rule engine integration  
- Quantization optimization  
- Enterprise authentication layer  

---

## 📌 Project Status

- ✅ Multi-agent orchestration complete  
- ✅ Pinecone vector integration enabled  
- ✅ HuggingFace API integration stable  
- ✅ Cloud deployment working  
- 🔄 Continuous optimization ongoing  

---

## 👤 Author
Anurag Thakur 
atanuragthakurpro@gmail.com


Generative AI | Multi-Agent Systems | LLM Engineering
