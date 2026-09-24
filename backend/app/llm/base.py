from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class ChatMessage(BaseModel):
    role: str = Field(description="'system', 'user', 'assistant', 'tool'")
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


class LLMResponse(BaseModel):
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model: str
    provider: str
    latency_ms: int = 0


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        messages: List[ChatMessage],
        response_schema: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        pass
