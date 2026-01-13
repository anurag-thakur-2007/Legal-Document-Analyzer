import re

CLAUSE_KEYWORDS = {
    "payment": [
        "payment", "fees", "invoice", "pricing",
        "charges", "compensation", "billing"
    ],
    "termination": [
        "termination", "terminate", "notice period",
        "cancellation", "expiry"
    ],
    "confidentiality": [
        "confidential", "non-disclosure", "nda",
        "proprietary", "confidentiality"
    ],
    "intellectual_property": [
        "intellectual property", "ip", "ownership",
        "copyright", "patent", "trademark"
    ],
    "governing_law": [
        "governing law", "jurisdiction",
        "applicable law", "court"
    ],
    "liability": [
        "liability", "damages", "indemnity",
        "limitation of liability"
    ],
    "data_protection": [
        "gdpr", "data protection", "privacy",
        "personal data", "processing"
    ]
}

def extract_clauses(contract_text: str) -> dict:
    """
    Extracts important clauses from contract text using keyword matching.
    """

    clauses = {}
    lower_text = contract_text.lower()

    for clause_name, keywords in CLAUSE_KEYWORDS.items():
        pattern = "|".join(keywords)
        matches = re.finditer(pattern, lower_text)

        extracted_text = []

        for match in matches:
            start = max(match.start() - 200, 0)
            end = min(match.end() + 500, len(contract_text))
            extracted_text.append(contract_text[start:end])

        if extracted_text:
            clauses[clause_name] = "\n".join(set(extracted_text))
        else:
            clauses[clause_name] = None

    # Detect missing clauses
    missing_clauses = [
        name for name, text in clauses.items()
        if text is None
    ]

    return {
        "clauses": clauses,
        "missing_clauses": missing_clauses
    }
