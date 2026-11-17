from pydantic_settings import BaseSettings
from typing import Dict, List, Any


class Settings(BaseSettings):
    app_name: str = "NexusGate LLM Gateway"
    environment: str = "production"
    port: int = 8000
    database_path: str = "./gateway_telemetry.db"
    seed_demo_data: bool = True
    sandbox_mode: bool = True

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    cache_enabled: bool = True
    cache_similarity_threshold: float = 0.72
    cache_ttl_seconds: int = 3600

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Model Catalog with pricing per 1M tokens (USD), tier, latency profile, and provider
MODEL_CATALOG: Dict[str, Dict[str, Any]] = {
    "llama-3.1-8b-instant": {
        "provider": "groq",
        "display_name": "Llama 3.1 8B Instant",
        "tier": "simple",
        "input_cost_per_1m": 0.05,
        "output_cost_per_1m": 0.08,
        "avg_latency_ms": 210,
        "max_context": 128000,
        "quality_score": 76,
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "display_name": "GPT-4o Mini",
        "tier": "simple",
        "input_cost_per_1m": 0.15,
        "output_cost_per_1m": 0.60,
        "avg_latency_ms": 380,
        "max_context": 128000,
        "quality_score": 84,
    },
    "claude-3-5-haiku": {
        "provider": "anthropic",
        "display_name": "Claude 3.5 Haiku",
        "tier": "moderate",
        "input_cost_per_1m": 0.80,
        "output_cost_per_1m": 4.00,
        "avg_latency_ms": 490,
        "max_context": 200000,
        "quality_score": 88,
    },
    "gpt-4o": {
        "provider": "openai",
        "display_name": "GPT-4o",
        "tier": "complex",
        "input_cost_per_1m": 2.50,
        "output_cost_per_1m": 10.00,
        "avg_latency_ms": 890,
        "max_context": 128000,
        "quality_score": 95,
    },
    "claude-3-5-sonnet": {
        "provider": "anthropic",
        "display_name": "Claude 3.5 Sonnet",
        "tier": "complex",
        "input_cost_per_1m": 3.00,
        "output_cost_per_1m": 15.00,
        "avg_latency_ms": 960,
        "max_context": 200000,
        "quality_score": 97,
    },
}

# Baseline comparison model (used to calculate cost savings vs unrouted flagship usage)
BASELINE_MODEL = "gpt-4o"

# Ordered fallback chains per tier
FALLBACK_CHAINS: Dict[str, List[str]] = {
    "simple": ["llama-3.1-8b-instant", "gpt-4o-mini", "claude-3-5-haiku"],
    "moderate": ["gpt-4o-mini", "claude-3-5-haiku", "gpt-4o"],
    "complex": ["gpt-4o", "claude-3-5-sonnet", "gpt-4o-mini"],
}
