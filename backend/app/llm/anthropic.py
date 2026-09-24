import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel
from app.core.config import settings
from app.core.exceptions import ProviderError
from app.llm.base import ChatMessage, LLMProvider, LLMResponse, TokenUsage
from app.llm.usage import calculate_cost

T = TypeVar("T", bound=BaseModel)


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.base_url = "https://api.anthropic.com/v1"

    async def generate(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ProviderError("Anthropic API key is missing")

        model_name = model or "claude-3-5-sonnet-20241022"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        system_prompt = ""
        anthropic_messages = []
        for m in messages:
            if m.role == "system":
                system_prompt += f"{m.content}\n"
            else:
                anthropic_messages.append({"role": m.role if m.role in ["user", "assistant"] else "user", "content": m.content})

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_prompt:
            payload["system"] = system_prompt.strip()

        start_t = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self.base_url}/messages", headers=headers, json=payload)
                if res.status_code != 200:
                    raise ProviderError(f"Anthropic error {res.status_code}: {res.text}")
                data = res.json()
        except httpx.RequestError as e:
            raise ProviderError(f"Anthropic connection error: {str(e)}")

        latency_ms = int((time.time() - start_t) * 1000)
        content = ""
        if "content" in data and len(data["content"]) > 0:
            content = data["content"][0].get("text", "")

        usage_data = data.get("usage", {})
        inp_tokens = usage_data.get("input_tokens", 0)
        out_tokens = usage_data.get("output_tokens", 0)
        cost = calculate_cost(model_name, inp_tokens, out_tokens)

        return LLMResponse(
            content=content,
            usage=TokenUsage(
                input_tokens=inp_tokens,
                output_tokens=out_tokens,
                total_tokens=inp_tokens + out_tokens,
                cost_usd=cost,
            ),
            model=model_name,
            provider="anthropic",
            latency_ms=latency_ms,
        )

    async def generate_structured(
        self,
        messages: List[ChatMessage],
        response_schema: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        schema_json = json.dumps(response_schema.model_json_schema())
        system_injection = ChatMessage(
            role="system",
            content=f"You must respond ONLY with valid JSON matching this schema: {schema_json}. Do not include markdown ticks or explanation."
        )
        res = await self.generate(
            messages=[system_injection] + messages,
            model=model,
            temperature=temperature,
        )
        content = res.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        return response_schema.model_validate_json(content.strip())

    async def stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        res = await self.generate(messages=messages, model=model, temperature=temperature)
        yield res.content
