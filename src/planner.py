# src/planner.py

from transformers import pipeline
from src.agents.compliance_agent import ComplianceAgent
from src.agents.legal_agent import LegalAgent
from src.agents.finance_agent import FinanceAgent
from src.agents.operations_agent import OperationsAgent
from src.utils.parallel_executor import run_agents_in_parallel


AGENT_ROLES = {
    "compliance": {
        "objective": "Ensure regulatory and policy compliance",
        "focus": ["regulation", "audit", "gdpr", "iso", "policy"],
        "risk_type": "Compliance Risk"
    },
    "finance": {
        "objective": "Identify financial exposure and obligations",
        "focus": ["payment", "pricing", "penalty", "tax", "invoice"],
        "risk_type": "Financial Risk"
    },
    "legal": {
        "objective": "Assess legal enforceability and liability",
        "focus": ["liability", "indemnity", "termination", "jurisdiction"],
        "risk_type": "Legal Risk"
    },
    "operations": {
        "objective": "Validate operational feasibility and SLAs",
        "focus": ["sla", "uptime", "delivery", "support"],
        "risk_type": "Operational Risk"
    }
}


# Optimized, reused classifier
CLASSIFIER = pipeline(
    "zero-shot-classification",
    model="typeform/distilbert-base-uncased-mnli",
    device=-1
)


class PlanningModule:

    def __init__(self):
        self.classifier = CLASSIFIER

        self.compliance_agent = ComplianceAgent()
        self.legal_agent = LegalAgent()
        self.finance_agent = FinanceAgent()
        self.operations_agent = OperationsAgent()

    # ---------------------------------------------------------
    # 1️⃣ CONTRACT CLASSIFICATION
    # ---------------------------------------------------------
    def classify_contract(self, text):
        labels = [
            "Service Agreement",
            "Employment Contract",
            "NDA",
            "Vendor Agreement",
            "Partnership Agreement",
            "SAAS Agreement",
        ]

        result = self.classifier(text, candidate_labels=labels)

        return {
            "contract_type": result["labels"][0],
            "confidence": float(result["scores"][0])
        }

    # ---------------------------------------------------------
    # 2️⃣ AGENT SELECTION
    # ---------------------------------------------------------
    def select_agents(self, classification_result):
        return ["legal", "compliance", "finance"]

    # ---------------------------------------------------------
    # 3️⃣ RUN SPECIFIC AGENT
    # ---------------------------------------------------------
    def run_agent(self, agent_name, text):
        if agent_name == "legal":
            return self.legal_agent.analyze(text)

        if agent_name == "finance":
            return self.finance_agent.analyze(text)

        if agent_name == "operations":
            return self.operations_agent.analyze(text)

        if agent_name == "compliance":
            return self.compliance_agent.analyze(text)

        return {"error": f"Unknown agent '{agent_name}'"}

    # ---------------------------------------------------------
    # 4️⃣ MAIN PLANNING FUNCTION
    # ---------------------------------------------------------
    def plan_agents(self, text):
        classification = self.classify_contract(text)
        selected = self.select_agents(classification)

        agent_map = {
            "legal": self.legal_agent,
            "compliance": self.compliance_agent,
            "finance": self.finance_agent
        }

        agent_outputs = run_agents_in_parallel(
            {name: agent_map[name] for name in selected},
            text
        )

        return {
            "classification": classification,
            "selected_agents": selected,
            "agent_roles": {agent: AGENT_ROLES[agent] for agent in selected},
            "agent_outputs": agent_outputs
        }
