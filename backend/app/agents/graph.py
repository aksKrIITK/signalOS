from typing import Any, Dict, Literal
from langgraph.graph import StateGraph, END, START
from app.agents.state import SDRState
from app.agents.nodes.planner_node import planner_node
from app.agents.nodes.company_discovery_node import company_discovery_node
from app.agents.nodes.research_node import research_node
from app.agents.nodes.contact_discovery_node import contact_discovery_node
from app.agents.nodes.enrichment_node import enrichment_node
from app.agents.nodes.signal_detection_node import signal_detection_node
from app.agents.nodes.rag_retrieval_node import rag_retrieval_node
from app.agents.nodes.scoring_node import scoring_node
from app.agents.nodes.personalization_node import personalization_node
from app.agents.nodes.critic_node import critic_node
from app.agents.nodes.approval_node import approval_node
from app.agents.nodes.execution_node import execution_node


def route_critic(state: SDRState) -> Literal["research", "approval"]:
    if not state.get("critic_passed", True) and state.get("research_iterations", 0) < 2:
        return "research"
    return "approval"


def route_approval(state: SDRState) -> Literal["execution", "end"]:
    if state.get("approved", False):
        return "execution"
    return "end"


def build_sdr_graph():
    builder = StateGraph(SDRState)

    # Register Nodes
    builder.add_node("planner", planner_node)
    builder.add_node("company_discovery", company_discovery_node)
    builder.add_node("research", research_node)
    builder.add_node("contact_discovery", contact_discovery_node)
    builder.add_node("enrichment", enrichment_node)
    builder.add_node("signal_detection", signal_detection_node)
    builder.add_node("rag_retrieval", rag_retrieval_node)
    builder.add_node("scoring", scoring_node)
    builder.add_node("personalization", personalization_node)
    builder.add_node("critic", critic_node)
    builder.add_node("approval", approval_node)
    builder.add_node("execution", execution_node)

    # Edges
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "company_discovery")
    builder.add_edge("company_discovery", "research")
    builder.add_edge("research", "contact_discovery")
    builder.add_edge("contact_discovery", "enrichment")
    builder.add_edge("enrichment", "signal_detection")
    builder.add_edge("signal_detection", "rag_retrieval")
    builder.add_edge("rag_retrieval", "scoring")
    builder.add_edge("scoring", "personalization")
    builder.add_edge("personalization", "critic")

    # Conditional Critic routing
    builder.add_conditional_edges(
        "critic",
        route_critic,
        {
            "research": "research",
            "approval": "approval",
        },
    )

    # Conditional Approval routing
    builder.add_conditional_edges(
        "approval",
        route_approval,
        {
            "execution": "execution",
            "end": END,
        },
    )

    builder.add_edge("execution", END)

    return builder.compile()


sdr_graph = build_sdr_graph()
