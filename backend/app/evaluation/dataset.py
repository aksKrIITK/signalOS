from typing import List
from app.schemas.evaluation import EvalCase

EVALUATION_DATASET: List[EvalCase] = [
    EvalCase(
        id="case-001-india-saas",
        name="Indian B2B SaaS Series A - CTO Outreach",
        input={
            "company": {"name": "Finflow Systems", "domain": "finflow.io", "industry": "B2B SaaS", "country": "India"},
            "contact": {"first_name": "Vikram", "last_name": "Sharma", "job_title": "VP Engineering"},
            "icp": {
                "industry": "B2B SaaS",
                "location": "India",
                "min_employees": 50,
                "max_employees": 500,
                "target_personas": ["CTO", "VP Engineering"],
            },
        },
        expected_tools=["web_search", "fetch_page", "retrieve_knowledge"],
        expected_signals=["recent funding", "hiring engineers"],
        min_expected_score=75.0,
        max_expected_score=100.0,
    ),
    EvalCase(
        id="case-002-us-fintech",
        name="US FinTech Scaleup - Head of Platform",
        input={
            "company": {"name": "NovaPay Inc", "domain": "novapay.com", "industry": "FinTech", "country": "United States", "employee_count": 220},
            "contact": {"first_name": "Sarah", "last_name": "Jenkins", "job_title": "Head of Platform Engineering"},
            "icp": {
                "industry": "FinTech",
                "location": "United States",
                "min_employees": 100,
                "max_employees": 1000,
                "target_personas": ["Head of Platform", "VP Engineering"],
            },
        },
        expected_tools=["web_search", "fetch_page", "retrieve_knowledge"],
        expected_signals=["recent funding", "technology migration"],
        min_expected_score=70.0,
        max_expected_score=95.0,
    ),
    EvalCase(
        id="case-003-out-of-icp",
        name="Consumer Mobile App 5 Employees - Disqualification Test",
        input={
            "company": {"name": "TinyApp Studio", "domain": "tinyapp.test", "industry": "Consumer Mobile", "country": "UK", "employee_count": 5},
            "contact": {"first_name": "Dave", "last_name": "Miller", "job_title": "Game Designer"},
            "icp": {
                "industry": "B2B SaaS",
                "location": "India",
                "min_employees": 50,
                "max_employees": 500,
                "target_personas": ["CTO"],
            },
        },
        expected_tools=["web_search"],
        expected_signals=[],
        min_expected_score=0.0,
        max_expected_score=45.0,
    ),
]
