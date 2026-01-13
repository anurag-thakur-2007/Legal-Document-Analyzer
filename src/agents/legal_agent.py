from src.agents.llm_helper import ask_llm


class LegalAgent:

    def analyze(self, contract_text: str):
        prompt = f"""
You are a Legal Analysis Agent.

Analyze the following contract and identify:
- Governing law
- Termination clauses
- Liability risks
- Intellectual property ownership
- Dispute resolution mechanisms

Return a clear, concise legal analysis.

CONTRACT:
{contract_text}
"""

        output = ask_llm(prompt)

        return {
            "agent": "Legal",
            "result": {
                "analysis": output
            }
        }
