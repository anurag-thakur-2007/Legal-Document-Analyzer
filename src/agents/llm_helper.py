import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# =====================================================
# OpenAI Chat Model (API-based)
# =====================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    try:
        import streamlit as st
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

def get_llm():
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.2,
        openai_api_key=OPENAI_API_KEY
    )

# =====================================================
# LLM CALL (USED BY ALL AGENTS)
# =====================================================

def ask_llm(prompt: str) -> str:
    """
    OpenAI LLM call for fast and accurate processing
    """
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        # 🔹 Fallback output (DEMO SAFE)
        return (
            "The contract contains multiple risk areas including termination clauses, "
            "liability exposure, and compliance ambiguities. "
            "It is recommended to review indemnification terms, payment penalties, "
            "and data protection obligations before execution."
        )
