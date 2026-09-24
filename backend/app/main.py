import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging, logger
from app.core.security import get_password_hash
from app.db.database import AsyncSessionLocal, Base, engine
from app.db.models.organization import Organization
from app.db.models.user import User
from app.db.models.company import Company
from app.db.models.contact import Contact
from app.db.models.lead import Lead
from app.db.models.campaign import Campaign, CampaignLead
from app.db.models.agent_run import AgentRun, ToolCall, AgentRunStatus
from app.api.routes import (
    auth,
    organizations,
    campaigns,
    leads,
    agent_runs,
    approvals,
    knowledge,
    metrics,
    health,
)

setup_logging(debug=settings.DEBUG)


async def seed_initial_data():
    """Seeds initial demo organization, campaign, and leads if database is empty."""
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            res = await session.execute(select(Organization).limit(1))
            if res.scalars().first():
                return

            logger.info("seeding_initial_demo_data")
            org = Organization(name="Acme HyperGrowth SaaS")
            session.add(org)
            await session.flush()

            user = User(
                organization_id=org.id,
                email="demo@signalos.ai",
                hashed_password=get_password_hash("signalos123"),
                full_name="Alex Mercer (GTM Lead)",
                role="OWNER",
                is_active=True,
            )
            session.add(user)
            await session.flush()

            # Seed Company & Contact
            company = Company(
                organization_id=org.id,
                name="Finflow Systems",
                domain="finflow.io",
                industry="B2B SaaS",
                employee_count=180,
                country="India",
                description="High-throughput financial API orchestration platform.",
                metadata_json={"tech_stack": ["Python", "FastAPI", "AWS", "PostgreSQL"], "funding": "$18M Series A"},
            )
            session.add(company)
            await session.flush()

            contact = Contact(
                organization_id=org.id,
                company_id=company.id,
                first_name="Vikram",
                last_name="Sharma",
                email="vikram.sharma@finflow.io",
                job_title="VP Engineering",
                linkedin_url="https://linkedin.com/in/vikram-sharma-tech",
            )
            session.add(contact)
            await session.flush()

            lead = Lead(
                organization_id=org.id,
                company_id=company.id,
                contact_id=contact.id,
                status="QUALIFIED",
                score=88.5,
                score_reason={
                    "reasons": [
                        "Company size (180 employees) matches 50-500 ICP",
                        "Recent $18M Series A funding in Feb 2026",
                        "Persona is VP Engineering",
                    ],
                    "signals": ["recent funding", "hiring engineers", "technology migration"],
                    "confidence": 0.94,
                },
                source="agent_discovery",
            )
            session.add(lead)
            await session.flush()

            # Seed Campaign
            campaign = Campaign(
                organization_id=org.id,
                name="Indian B2B SaaS CTOs — Post-Funding",
                description="Targeting CTOs and VPs of Engineering in India-based SaaS scaleups (50-500 employees) with recent funding rounds.",
                status="RUNNING",
                icp_definition={
                    "industry": "B2B SaaS",
                    "location": "India",
                    "min_employees": 50,
                    "max_employees": 500,
                    "target_personas": ["CTO", "VP Engineering", "Head of Engineering"],
                },
                signal_definition={
                    "required_signals": ["recent funding", "hiring engineers", "technology migration"],
                },
            )
            session.add(campaign)
            await session.flush()

            cl = CampaignLead(campaign_id=campaign.id, lead_id=lead.id, status="QUALIFIED", score=88.5)
            session.add(cl)
            await session.flush()

            # Seed Agent Run Waiting Approval
            run = AgentRun(
                organization_id=org.id,
                campaign_id=campaign.id,
                lead_id=lead.id,
                agent_type="sdr_pipeline",
                status=AgentRunStatus.WAITING_APPROVAL,
                input_json={"company": "Finflow Systems", "contact": "Vikram Sharma"},
                output_json={
                    "score": 88.5,
                    "signals": [
                        {"name": "recent funding", "evidence": "$18M Series A announced Feb 2026"},
                        {"name": "hiring engineers", "evidence": "Active hiring for Senior Backend Engineers"},
                    ],
                    "email_subject": "Scaling backend throughput post-$18M Series A",
                    "email_body": (
                        "Hi Vikram,\n\n"
                        "Noticed Finflow's recent $18M Series A and your team's active hiring for Senior Backend Engineers to scale API orchestration.\n\n"
                        "As engineering teams expand after a major round, tool fragmentation and slow signal-to-outreach cycles often slow execution. "
                        "SignalOS provides an autonomous agentic pipeline that turns real-time developer signals into verified, evidence-backed workflows.\n\n"
                        "Open to a brief 10-minute technical exchange this Thursday?\n\n"
                        "Best,\nSignalOS Growth Team"
                    ),
                    "critic_passed": True,
                    "requires_approval": True,
                },
                model="gpt-4o",
                input_tokens=3200,
                output_tokens=820,
                cost_usd=0.028,
            )
            session.add(run)
            await session.flush()

            tool1 = ToolCall(
                agent_run_id=run.id,
                tool_name="web_search",
                arguments={"query": "Finflow systems funding news 2026"},
                result={"status": "FOUND", "results_count": 3},
                status="SUCCESS",
                latency_ms=850,
            )
            tool2 = ToolCall(
                agent_run_id=run.id,
                tool_name="fetch_page",
                arguments={"url": "https://finflow.io/careers"},
                result={"title": "Careers at Finflow", "main_content_preview": "Hiring senior backend engineers"},
                status="SUCCESS",
                latency_ms=420,
            )
            session.add_all([tool1, tool2])

            await session.commit()
            logger.info("demo_data_seeded_successfully", org_id=str(org.id))
    except Exception as e:
        logger.warning("seed_data_skipped_or_failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize tables if needed
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_initial_data()
    except Exception as e:
        logger.warning("database_initialization_notice", error=str(e))
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Correlation Tracing Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start_time = time.time()
    response = await call_next(request)
    latency_ms = int((time.time() - start_time) * 1000)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{latency_ms}ms"
    return response


# Centralized Exception Handler
@app.exception_handler(AppError)
async def app_exception_handler(request: Request, exc: AppError):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id,
            }
        },
    )


# Register API Routers
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(organizations.router, prefix=settings.API_V1_STR)
app.include_router(campaigns.router, prefix=settings.API_V1_STR)
app.include_router(leads.router, prefix=settings.API_V1_STR)
app.include_router(agent_runs.router, prefix=settings.API_V1_STR)
app.include_router(approvals.router, prefix=settings.API_V1_STR)
app.include_router(knowledge.router, prefix=settings.API_V1_STR)
app.include_router(metrics.router, prefix=settings.API_V1_STR)
