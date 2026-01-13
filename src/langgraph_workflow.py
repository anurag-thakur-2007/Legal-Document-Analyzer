# src/langgraph_workflow.py

from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from typing import Dict, Any

from src.planner import PlanningModule


# ----------------------------
# 1. Define State Schema
# ----------------------------
class ContractState(BaseModel):
    contract_text: str
    classification: Dict[str, Any] | None = None
    selected_agents: list | None = None
    agent_outputs: Dict[str, Any] | None = None
    final_report: Dict[str, Any] | None = None


planner = PlanningModule()


# ----------------------------
# 2. Graph Nodes
# ----------------------------
def classify_node(state: ContractState):
    state.classification = planner.classify_contract(state.contract_text)
    return state


def select_agents_node(state: ContractState):
    state.selected_agents = planner.select_agents(state.classification)
    return state


def run_agents_node(state: ContractState):
    outputs = {}
    for agent in state.selected_agents:
        outputs[agent] = planner.run_agent(agent, state.contract_text)
    state.agent_outputs = outputs
    return state


def build_report_node(state: ContractState):
    state.final_report = {
        "contract_classification": state.classification,
        "selected_agents": state.selected_agents,
        "analysis": state.agent_outputs
    }
    return state


# ----------------------------
# 3. Build LangGraph Workflow
# ----------------------------
def build_workflow():

    graph = StateGraph(ContractState)

    graph.add_node("classify", classify_node)
    graph.add_node("select_agents", select_agents_node)
    graph.add_node("run_agents", run_agents_node)
    graph.add_node("build_report", build_report_node)

    graph.set_entry_point("classify")

    graph.add_edge("classify", "select_agents")
    graph.add_edge("select_agents", "run_agents")
    graph.add_edge("run_agents", "build_report")
    graph.add_edge("build_report", END)

    return graph.compile()
