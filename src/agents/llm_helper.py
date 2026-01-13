from transformers import pipeline
import threading

_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

_pipeline = None
_lock = threading.Lock()


def get_pipeline():
    global _pipeline
    with _lock:
        if _pipeline is None:
            _pipeline = pipeline(
                task="text-generation",
                model=_MODEL_NAME,
                max_new_tokens=40,       
                temperature=0.0,          
                do_sample=False,          
                device_map="auto"
            )
    return _pipeline


def ask_llm(prompt: str) -> str:
    pipe = get_pipeline()
    response = pipe(prompt)

    full_text = response[0]["generated_text"]

    # 🔧 Remove echoed prompt from output
    cleaned_text = full_text.replace(prompt, "").strip()

    return cleaned_text
