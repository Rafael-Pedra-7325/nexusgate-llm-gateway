from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "auto"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512
    routing_strategy: Optional[Literal["complexity", "cost", "balanced"]] = None
    use_cache: Optional[bool] = True
    cache_threshold: Optional[float] = None
    simulate_failure: Optional[bool] = False


class GatewayTraceStep(BaseModel):
    step: str
    status: Literal["hit", "miss", "routed", "failed", "recovered", "completed"]
    detail: str
    duration_ms: float


class GatewayMetadata(BaseModel):
    request_id: str
    routing_strategy: str
    complexity_score: float
    complexity_tier: str
    selected_model: str
    provider: str
    cache_hit: bool
    cache_similarity: Optional[float] = None
    fallback_triggered: bool
    attempted_models: List[str]
    latency_ms: float
    cost_usd: float
    baseline_cost_usd: float
    savings_usd: float
    sandbox_mode: bool
    trace: List[GatewayTraceStep]


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"


class UsageStats(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: UsageStats
    gateway: GatewayMetadata
