import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
from app.llm.base import ChatMessage, LLMProvider, LLMResponse, TokenUsage
from app.schemas.agent import EvidenceClaim, PersonalizedEmail, ResearchPlan
from app.schemas.lead import LeadScoreBreakdown

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """
    High-fidelity deterministic LLM provider for unit tests, offline evaluation,
    and fallback when external API keys are not supplied.
    """
    def __init__(self, model_name: str = "mock-gpt-4o"):
        self.model_name = model_name

    async def generate(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
        
        reply = (
            f"Based on comprehensive GTM research, the prospect matches key ICP criteria. "
            f"Observed signals include recent Series B funding and active engineering hiring."
        )
        return LLMResponse(
            content=reply,
            usage=TokenUsage(input_tokens=150, output_tokens=85, total_tokens=235, cost_usd=0.0012),
            model=model or self.model_name,
            provider="mock",
            latency_ms=45,
        )

    async def generate_structured(
        self,
        messages: List[ChatMessage],
        response_schema: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
        
        if response_schema == ResearchPlan:
            return response_schema(
                steps=[
                    "Execute web search for recent company funding and engineering team growth",
                    "Fetch official engineering blog and career page to verify tech stack",
                    "Query internal GTM battlecards for enterprise security objection handling",
                    "Analyze buyer persona fit and draft personalized outreach",
                ],
                required_tools=["web_search", "fetch_page", "retrieve_knowledge"],
                reasoning_summary="Target exhibits strong growth signals requiring verification of AWS/Python architecture and CTO leadership.",
            )

        if response_schema == PersonalizedEmail:
            return response_schema(
                subject="Accelerating engineering velocity after recent Series B",
                opening_line="Noticed your team recently announced a Series B round and is actively scaling backend infrastructure.",
                pain_point="Scaling engineering teams often struggle with signal overload and repetitive GTM orchestration across fragmented toolchains.",
                value_proposition="SignalOS provides autonomous agentic pipelines that discover high-intent accounts and orchestrate targeted workflows deterministically.",
                call_to_action="Are you open to a brief 10-minute technical exchange this Thursday?",
                full_body=(
                    "Hi {{first_name}},\n\n"
                    "Noticed {{company_name}} recently announced a Series B round and is actively scaling backend infrastructure.\n\n"
                    "As engineering teams scale, managing fragmented outreach tools and signal noise quickly creates bottlenecks. "
                    "SignalOS provides autonomous agentic pipelines that discover high-intent accounts and orchestrate targeted workflows deterministically.\n\n"
                    "Are you open to a brief 10-minute technical exchange this Thursday?\n\n"
                    "Best regards,\nSignalOS Growth Team"
                ),
                evidence_claims=[
                    EvidenceClaim(
                        claim="Company raised $15M Series B funding",
                        source="https://techcrunch.com/funding-round",
                        confidence=0.96,
                    ),
                    EvidenceClaim(
                        claim="Hiring 12+ Senior Backend Engineers",
                        source="https://careers.company.io",
                        confidence=0.92,
                    ),
                ],
            )

        if response_schema == LeadScoreBreakdown:
            return response_schema(
                score=88.5,
                reasons=[
                    "Company size (180 employees) perfectly matches 50-500 ICP criteria",
                    "Verified recent $15M Series B funding announced within last 60 days",
                    "Target persona is active CTO / Head of Engineering",
                    "Tech stack confirmed to include Python, FastAPI, and AWS",
                ],
                signals=["recent funding", "hiring engineers", "technology migration"],
                confidence=0.94,
                deterministic_components={"company_fit": 28.5, "persona_fit": 20.0, "data_confidence": 9.5},
                qualitative_components={"buying_signals": 25.5, "engagement_intent": 5.0},
            )

        # Generic fallback instance if any other schema is requested
        return response_schema()

    async def stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        res = await self.generate(messages=messages, model=model, temperature=temperature)
        for word in res.content.split(" "):
            yield word + " "
