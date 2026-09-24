import asyncio
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
from app.core.config import settings
from app.core.exceptions import ProviderError
from app.core.logging import logger
from app.llm.base import ChatMessage, LLMProvider, LLMResponse
from app.llm.openai import OpenAIProvider
from app.llm.anthropic import AnthropicProvider
from app.llm.gemini import GeminiProvider
from app.llm.mock_provider import MockLLMProvider

T = TypeVar("T", bound=BaseModel)


class ModelRouter:
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
            "mock": MockLLMProvider(),
        }

    def select_model(self, task_type: str) -> str:
        """
        Routes task types to optimal model class:
        - classification / extraction -> fast cheap models
        - research_synthesis / personalization -> flagship reasoning models
        """
        task = task_type.lower()
        if task in ["classification", "extraction", "filtering", "summary"]:
            return "gpt-4o-mini"
        elif task in ["research_synthesis", "signal_detection"]:
            return "gpt-4o"
        elif task in ["complex_reasoning", "critic", "personalization"]:
            return "gpt-4o"
        return settings.DEFAULT_FAST_MODEL

    async def generate_with_fallback(
        self,
        messages: List[ChatMessage],
        task_type: str = "general",
        temperature: float = 0.2,
        max_retries: int = 2,
    ) -> LLMResponse:
        model = self.select_model(task_type)
        provider_order = [settings.DEFAULT_LLM_PROVIDER, "anthropic", "gemini", "mock"]

        # Ensure order has no duplicates
        seen = set()
        unique_providers = [p for p in provider_order if not (p in seen or seen.add(p))]

        last_error = None
        for provider_name in unique_providers:
            provider = self.providers.get(provider_name)
            if not provider:
                continue

            for attempt in range(max_retries + 1):
                try:
                    logger.debug(
                        "llm_request_attempt",
                        provider=provider_name,
                        model=model,
                        task_type=task_type,
                        attempt=attempt,
                    )
                    response = await provider.generate(
                        messages=messages,
                        model=model if provider_name != "gemini" else "gemini-1.5-flash",
                        temperature=temperature,
                    )
                    return response
                except Exception as e:
                    last_error = e
                    logger.warning(
                        "llm_provider_attempt_failed",
                        provider=provider_name,
                        attempt=attempt,
                        error=str(e),
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(2 ** attempt * 0.5)

        # Fallback to Mock provider for guaranteed resilience
        logger.info("llm_fallback_to_mock", reason="all_providers_failed", last_error=str(last_error))
        return await self.providers["mock"].generate(messages=messages, model="mock-gpt-4o")

    async def generate_structured_with_fallback(
        self,
        messages: List[ChatMessage],
        response_schema: Type[T],
        task_type: str = "general",
        temperature: float = 0.1,
    ) -> T:
        provider_order = [settings.DEFAULT_LLM_PROVIDER, "anthropic", "gemini", "mock"]
        seen = set()
        unique_providers = [p for p in provider_order if not (p in seen or seen.add(p))]

        for provider_name in unique_providers:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            try:
                res = await provider.generate_structured(
                    messages=messages,
                    response_schema=response_schema,
                    model=self.select_model(task_type),
                    temperature=temperature,
                )
                return res
            except Exception as e:
                logger.warning("structured_llm_failed", provider=provider_name, error=str(e))

        return await self.providers["mock"].generate_structured(
            messages=messages,
            response_schema=response_schema,
        )


model_router = ModelRouter()
