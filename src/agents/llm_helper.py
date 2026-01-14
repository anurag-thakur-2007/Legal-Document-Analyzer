import os
from huggingface_hub import InferenceClient
from functools import lru_cache

# =====================================================
# Hugging Face Inference Client (API-based)
# =====================================================

HF_API_TOKEN = os.getenv("HF_API_TOKEN")

if not HF_API_TOKEN:
    raise ValueError("HF_API_TOKEN not found in environment variables")

MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"
# You can also use:
# "Qwen/Qwen2.5-1.5B-Instruct"
# "google/gemma-2b-it"

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
