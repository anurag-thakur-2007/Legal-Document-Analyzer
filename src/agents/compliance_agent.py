from src.agents.llm_helper import ask_llm


class ComplianceAgent:

    def analyze(self, contract_text: str):
        prompt = f"""
You are a Compliance Analysis Agent.

Check the contract for:
- Data protection clauses
- Privacy and GDPR compliance
- Regulatory or statutory obligations
- Confidentiality requirements

Return a concise compliance assessment.

CONTRACT:
{contract_text}
"""

        output = ask_llm(prompt)

        return {
            "agent": "Compliance",
            "result": {
                "analysis": output
            }
        }
