from src.agents.llm_helper import ask_llm


class OperationsAgent:

    def analyze(self, contract_text: str):
        prompt = f"""
You are an Operations Analysis Agent.

Identify:
- Deliverables or services
- Timelines and deadlines
- Responsibilities of each party
- Operational risks or dependencies

Return a concise operational analysis.

CONTRACT:
{contract_text}
"""

        output = ask_llm(prompt)

        return {
            "agent": "Operations",
            "result": {
                "analysis": output
            }
        }
