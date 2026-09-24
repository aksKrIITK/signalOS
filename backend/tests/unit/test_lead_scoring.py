import pytest
from app.services.scoring_service import scoring_engine


def test_perfect_fit_lead_scoring():
    company = {
        "name": "Finflow Systems",
        "domain": "finflow.io",
        "industry": "B2B SaaS",
        "employee_count": 180,
        "country": "India",
    }
    contact = {
        "first_name": "Vikram",
        "last_name": "Sharma",
        "job_title": "VP Engineering",
        "email": "vikram@finflow.io",
        "linkedin_url": "https://linkedin.com/in/vikram",
    }
    signals = [
        {"name": "recent funding"},
        {"name": "hiring engineers"},
        {"name": "technology migration"},
    ]
    icp = {
        "industry": "B2B SaaS",
        "location": "India",
        "min_employees": 50,
        "max_employees": 500,
        "target_personas": ["CTO", "VP Engineering"],
    }

    result = scoring_engine.calculate_score(company, contact, signals, icp)

    assert result.score >= 80.0
    assert result.confidence >= 0.90
    assert "Company size (180 employees) matches ICP (50-500)" in result.reasons
    assert "Detected buying signal: 'Recent Funding'" in result.reasons


def test_disqualified_lead_scoring():
    company = {
        "name": "Micro App",
        "domain": "micro.test",
        "industry": "Consumer Mobile",
        "employee_count": 5,
        "country": "UK",
    }
    contact = {
        "first_name": "Dave",
        "job_title": "Graphic Designer",
    }
    signals = []
    icp = {
        "industry": "B2B SaaS",
        "location": "India",
        "min_employees": 50,
        "max_employees": 500,
        "target_personas": ["CTO"],
    }

    result = scoring_engine.calculate_score(company, contact, signals, icp)
    assert result.score < 50.0
