"""
CrewAI Proof-of-Concept Workflow
Demonstrates a multi-agent approach with specialized role-based agents.
"""

from typing import Any, Dict


class MockCrewAgent:
    def __init__(self, role: str, goal: str, backstory: str):
        self.role = role
        self.goal = goal
        self.backstory = backstory

    def execute_task(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "agent_role": self.role,
            "task": task_description,
            "output": f"Completed {self.role} analysis successfully.",
        }


class CrewGTMWorkflow:
    def __init__(self):
        self.researcher = MockCrewAgent(
            role="GTM Account Researcher",
            goal="Identify growth signals, engineering hiring, and funding news",
            backstory="Veteran market intelligence analyst specializing in high-growth B2B SaaS.",
        )
        self.enricher = MockCrewAgent(
            role="Contact & Persona Enricher",
            goal="Locate decision makers and verified contact details",
            backstory="Expert lead researcher with deep knowledge of org hierarchies and tech leaders.",
        )
        self.scorer = MockCrewAgent(
            role="ICP & Fit Evaluator",
            goal="Calculate account qualification score against target parameters",
            backstory="Revenue operations specialist optimizing pipeline conversion rates.",
        )
        self.writer = MockCrewAgent(
            role="Executive Outreach Copywriter",
            goal="Draft high-converting personalized email messages backed by evidence",
            backstory="Award-winning B2B copywriter focused on brevity, relevance, and value.",
        )

    def run_workflow(self, company_name: str, icp_criteria: Dict[str, Any]) -> Dict[str, Any]:
        context = {"company_name": company_name, "icp": icp_criteria}

        r1 = self.researcher.execute_task(f"Research funding and hiring for {company_name}", context)
        r2 = self.enricher.execute_task(f"Find CTO and VP Eng for {company_name}", context)
        r3 = self.scorer.execute_task(f"Score {company_name} against ICP", context)
        r4 = self.writer.execute_task(f"Draft cold outreach email for {company_name}", context)

        return {
            "workflow": "CrewAI GTM Sequential Pipeline",
            "stages": [r1, r2, r3, r4],
            "status": "COMPLETED",
        }


crew_gtm_pipeline = CrewGTMWorkflow()
