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


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"

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
            raise ProviderError("OpenAI API key is missing")

        model_name = model or settings.DEFAULT_FAST_MODEL
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": [m.model_dump(exclude_none=True) for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice

        start_t = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if res.status_code != 200:
                    raise ProviderError(f"OpenAI error {res.status_code}: {res.text}")
                data = res.json()
        except httpx.RequestError as e:
            raise ProviderError(f"OpenAI connection error: {str(e)}")

        latency_ms = int((time.time() - start_t) * 1000)
        choice = data["choices"][0]["message"]
        usage_data = data.get("usage", {})
        inp_tokens = usage_data.get("prompt_tokens", 0)
        out_tokens = usage_data.get("completion_tokens", 0)
        cost = calculate_cost(model_name, inp_tokens, out_tokens)

        return LLMResponse(
            content=choice.get("content") or "",
            tool_calls=choice.get("tool_calls"),
            usage=TokenUsage(
                input_tokens=inp_tokens,
                output_tokens=out_tokens,
                total_tokens=inp_tokens + out_tokens,
                cost_usd=cost,
            ),
            model=model_name,
            provider="openai",
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
            content=f"You must respond ONLY with valid JSON matching this schema: {schema_json}. Do not include markdown ticks or extra text."
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
