import json
from src.agents.llm_helper import ask_llm

CLAUSE_CATEGORIES = [
    "payment", "termination", "confidentiality", 
    "intellectual_property", "governing_law", 
    "liability", "data_protection"
]

def extract_clauses(contract_text: str) -> dict:
    """
    Extracts important clauses from contract text using an LLM.
    """
    prompt = f"""
You are a legal document analyzer.
Extract the relevant text for each of the following clause categories from the contract:
{', '.join(CLAUSE_CATEGORIES)}

If a category is not found, set its value to null.
Respond ONLY with a valid JSON object where keys are the category names and values are the extracted text.

CONTRACT TEXT:
{contract_text[:8000]}
"""
    
    response = ask_llm(prompt)
    clauses = {cat: None for cat in CLAUSE_CATEGORIES}
    
    try:
        # Attempt to parse the JSON response
        parsed = json.loads(response)
        for k in CLAUSE_CATEGORIES:
            if k in parsed:
                clauses[k] = parsed[k]
    except Exception:
        pass
        
    missing_clauses = [name for name, text in clauses.items() if not text]

    return {
        "clauses": clauses,
        "missing_clauses": missing_clauses
    }
