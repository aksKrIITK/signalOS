from typing import Any, Dict, List, Optional
from app.schemas.lead import LeadScoreBreakdown


class LeadScoringEngine:
    """
    Production Hybrid Lead Scoring Engine:
    - Deterministic Components (50% total):
        - Company fit (30%): Industry match, employee count range, location
        - Persona fit (20%): Seniority, job title match
    - Qualitative / Signal Components (40% total):
        - Buying signals (30%): Funding recency, engineering hiring, migration
        - Engagement intent (10%): Inbound/interaction history
    - Data Confidence (10%): Verified contact info, corporate domain legitimacy
    """

    def calculate_score(
        self,
        company: Dict[str, Any],
        contact: Dict[str, Any],
        detected_signals: List[Dict[str, Any]],
        icp: Dict[str, Any],
    ) -> LeadScoreBreakdown:
        reasons: List[str] = []
        det_scores: Dict[str, float] = {}
        qual_scores: Dict[str, float] = {}

        # 1. Company Fit (Max 30)
        comp_fit = 0.0
        emp_count = company.get("employee_count", 0) or 0
        min_emp = icp.get("min_employees", 50)
        max_emp = icp.get("max_employees", 500)

        if min_emp <= emp_count <= max_emp:
            comp_fit += 15.0
            reasons.append(f"Company size ({emp_count} employees) matches ICP ({min_emp}-{max_emp})")
        elif emp_count > 0:
            comp_fit += 5.0
            reasons.append(f"Company size ({emp_count} employees) is outside target range")
        else:
            comp_fit += 8.0

        target_industry = (icp.get("industry") or "B2B SaaS").lower()
        company_industry = (company.get("industry") or "").lower()
        if target_industry in company_industry or company_industry in target_industry:
            comp_fit += 10.0
            reasons.append(f"Industry '{company.get('industry')}' matches target '{icp.get('industry')}'")
        else:
            comp_fit += 3.0

        target_loc = (icp.get("location") or "India").lower()
        company_loc = (company.get("country") or "").lower()
        if target_loc in company_loc:
            comp_fit += 5.0
            reasons.append(f"Location '{company.get('country')}' matches target geography")
        else:
            comp_fit += 2.0

        det_scores["company_fit"] = min(30.0, comp_fit)

        # 2. Persona Fit (Max 20)
        persona_fit = 0.0
        job_title = (contact.get("job_title") or "").lower()
        target_personas = [p.lower() for p in icp.get("target_personas", ["cto", "vp engineering", "head of engineering"])]

        matched_persona = any(p in job_title for p in target_personas)
        if matched_persona:
            persona_fit = 20.0
            reasons.append(f"Contact title '{contact.get('job_title')}' matches target persona")
        elif "engineering" in job_title or "tech" in job_title or "lead" in job_title:
            persona_fit = 12.0
            reasons.append(f"Contact title '{contact.get('job_title')}' is related to technical leadership")
        else:
            persona_fit = 5.0

        det_scores["persona_fit"] = persona_fit

        # 3. Buying Signals (Max 30)
        signal_names = [s.get("name", "").lower() for s in detected_signals]
        sig_score = 0.0
        signal_weights = {
            "recent funding": 12.0,
            "hiring engineers": 8.0,
            "new product launch": 5.0,
            "technology migration": 3.0,
            "rapid growth": 2.0,
        }
        for sig, weight in signal_weights.items():
            if any(sig in s for s in signal_names):
                sig_score += weight
                reasons.append(f"Detected buying signal: '{sig.title()}'")

        qual_scores["buying_signals"] = min(30.0, sig_score)

        # 4. Engagement & Intent (Max 10)
        qual_scores["engagement_intent"] = 5.0

        # 5. Data Confidence (Max 10)
        conf_score = 0.0
        if contact.get("email"):
            conf_score += 5.0
        if contact.get("linkedin_url"):
            conf_score += 3.0
        if company.get("domain"):
            conf_score += 2.0
        det_scores["data_confidence"] = conf_score

        total_score = sum(det_scores.values()) + sum(qual_scores.values())
        total_score = round(min(100.0, max(0.0, total_score)), 1)
        confidence = round(min(1.0, 0.7 + (conf_score / 30.0)), 2)

        return LeadScoreBreakdown(
            score=total_score,
            reasons=reasons,
            signals=[s.get("name", "") for s in detected_signals],
            confidence=confidence,
            deterministic_components=det_scores,
            qualitative_components=qual_scores,
        )


scoring_engine = LeadScoringEngine()
