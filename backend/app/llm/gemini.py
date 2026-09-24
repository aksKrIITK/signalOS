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


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

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
            raise ProviderError("Gemini API key is missing")

        model_name = model or "gemini-1.5-flash"
        url = f"{self.base_url}/models/{model_name}:generateContent?key={self.api_key}"

        contents = []
        system_instruction = None

        for m in messages:
            if m.role == "system":
                system_instruction = {"parts": [{"text": m.content}]}
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        start_t = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    raise ProviderError(f"Gemini error {res.status_code}: {res.text}")
                data = res.json()
        except httpx.RequestError as e:
            raise ProviderError(f"Gemini connection error: {str(e)}")

        latency_ms = int((time.time() - start_t) * 1000)
        content = ""
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts:
                content = parts[0].get("text", "")

        usage_meta = data.get("usageMetadata", {})
        inp_tokens = usage_meta.get("promptTokenCount", 0)
        out_tokens = usage_meta.get("candidatesTokenCount", 0)
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
            provider="gemini",
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
            content=f"Respond strictly in JSON matching: {schema_json}. No markdown backticks."
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
