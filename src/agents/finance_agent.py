from src.agents.llm_helper import ask_llm


class FinanceAgent:

    def analyze(self, contract_text: str):
        prompt = f"""
You are a Finance Analysis Agent.

Analyze the contract and extract:
- Payment terms
- Contract value
- Fees, penalties, or late charges
- Renewal or termination costs

Return a concise financial summary.

CONTRACT:
{contract_text}
"""

        output = ask_llm(prompt)

        return {
            "agent": "Finance",
            "result": {
                "analysis": output
            }
        }
