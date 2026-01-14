import os
import streamlit as st
from huggingface_hub import InferenceClient
from functools import lru_cache

# =====================================================
# Hugging Face Inference Client (API-based)
# =====================================================

HF_API_TOKEN = os.getenv("HF_API_TOKEN") or st.secrets.get("HF_API_TOKEN")

if not HF_API_TOKEN:
    raise ValueError("HF_API_TOKEN not found in environment variables or Streamlit secrets")

MODEL_NAME = "google/gemma-2b-it"

@lru_cache(maxsize=1)
def get_client():
    """
    Cached Hugging Face inference client
    """
    return InferenceClient(
        model=MODEL_NAME,
        token=HF_API_TOKEN
    )

# =====================================================
# LLM CALL (USED BY ALL AGENTS)
# =====================================================

def ask_llm(prompt: str) -> str:
    """
    Send prompt to Hugging Face Inference API and return response text
    """
    client = get_client()

    response = client.text_generation(
        prompt=prompt,
        max_new_tokens=300,
        temperature=0.2,
        top_p=0.95,
        do_sample=True
    )

    return response.strip()
