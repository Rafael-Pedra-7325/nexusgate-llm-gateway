import uuid
import random
from datetime import datetime, timedelta, timezone
from app.database import count_logs, insert_log
from app.config import MODEL_CATALOG, BASELINE_MODEL
from app.semantic_cache import semantic_cache


SAMPLE_EVENTS = [
    ("What is the capital of France?", "complexity", 0.12, "simple", "llama-3.1-8b-instant", False, False, 14, 38, 185.4),
    ("Tell me France's capital city", "complexity", 0.14, "simple", "llama-3.1-8b-instant", True, False, 12, 38, 2.1),
    ("Summarize HTTP/3 QUIC multiplexing benefits", "balanced", 0.45, "moderate", "claude-3-5-haiku", False, False, 24, 140, 462.0),
    ("Design a multi-region active-active PostgreSQL architecture with conflict resolution", "complexity", 0.84, "complex", "gpt-4o", False, False, 48, 390, 910.5),
    ("Convert this JSON payload to a Pydantic v2 schema", "cost", 0.36, "moderate", "gpt-4o-mini", False, False, 65, 110, 320.8),
    ("What is the capital of Japan?", "complexity", 0.11, "simple", "llama-3.1-8b-instant", False, False, 13, 35, 174.2),
    ("Which city serves as Japan's capital?", "complexity", 0.13, "simple", "llama-3.1-8b-instant", True, False, 14, 35, 1.9),
    ("Implement a lock-free ring buffer in Rust with atomic memory ordering", "complexity", 0.91, "complex", "claude-3-5-sonnet", False, True, 56, 440, 1120.4),
    ("Extract key dates from customer support ticket #4921", "cost", 0.18, "simple", "llama-3.1-8b-instant", False, False, 92, 42, 205.0),
    ("Compare Raft vs Paxos consensus latency under network partitions", "complexity", 0.78, "complex", "gpt-4o", False, False, 34, 310, 845.3),
    ("Explain OAuth2 PKCE flow for single-page web apps", "balanced", 0.52, "moderate", "claude-3-5-haiku", False, False, 28, 195, 510.6),
    ("What is the capital of France?", "cost", 0.12, "simple", "llama-3.1-8b-instant", True, False, 14, 38, 1.8),
]


def _calc_cost(model: str, pt: int, ct: int) -> float:
    m = MODEL_CATALOG[model]
    return (pt / 1_000_000) * m["input_cost_per_1m"] + (ct / 1_000_000) * m["output_cost_per_1m"]


def seed_initial_telemetry():
    if count_logs() > 0:
        return

    # Pre-warm semantic cache with two anchor queries so recruiters immediately experience hits
    semantic_cache.store(
        "What is the capital of France?",
        "The capital of France is **Paris**. Located along the Seine River in northern-central France, it serves as the nation's political, economic, and cultural center.",
        "llama-3.1-8b-instant",
        "groq",
        {"prompt_tokens": 14, "completion_tokens": 38, "total_tokens": 52},
    )
    semantic_cache.store(
        "What is the capital of Japan?",
        "The capital of Japan is **Tokyo**. Formerly known as Edo, it is the world's most populous metropolitan area and Japan's seat of government and finance.",
        "llama-3.1-8b-instant",
        "groq",
        {"prompt_tokens": 13, "completion_tokens": 35, "total_tokens": 48},
    )

    now = datetime.now(timezone.utc)
    # Generate 48 realistic chronological telemetry entries across the last 2 hours
    for i in range(48):
        sample = SAMPLE_EVENTS[i % len(SAMPLE_EVENTS)]
        prompt, strategy, c_score, c_tier, model, cache_hit, fallback, pt, ct, base_lat = sample
        provider = MODEL_CATALOG[model]["provider"]
        ts = (now - timedelta(minutes=(48 - i) * 2.5)).isoformat()

        latency = round(base_lat * random.uniform(0.9, 1.12), 1)
        baseline_cost = _calc_cost(BASELINE_MODEL, pt, ct)
        actual_cost = 0.0 if cache_hit else _calc_cost(model, pt, ct)
        savings = max(0.0, baseline_cost - actual_cost)

        attempted = [model]
        if fallback:
            attempted = ["gpt-4o", model]

        trace = [
            {
                "step": "Semantic Cache Lookup",
                "status": "hit" if cache_hit else "miss",
                "detail": "Cosine similarity 0.89 >= 0.72" if cache_hit else "No cached vector above threshold",
                "duration_ms": 1.4,
            }
        ]
        if not cache_hit:
            trace.append({
                "step": f"Complexity Router ({strategy})",
                "status": "routed",
                "detail": f"Score {c_score} ({c_tier}) -> {model}",
                "duration_ms": 0.6,
            })
            if fallback:
                trace.append({
                    "step": "Primary Dispatch (gpt-4o)",
                    "status": "failed",
                    "detail": "HTTP 429 Rate Limit -> failing over",
                    "duration_ms": 140.0,
                })
            trace.append({
                "step": f"Model Execution ({model})",
                "status": "recovered" if fallback else "completed",
                "detail": f"Completed via {provider}/{model}",
                "duration_ms": round(latency - 2.0, 1),
            })

        insert_log({
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "created_at": ts,
            "prompt_preview": prompt[:100],
            "routing_strategy": strategy,
            "complexity_score": c_score,
            "complexity_tier": c_tier,
            "selected_model": model,
            "provider": provider,
            "cache_hit": cache_hit,
            "cache_similarity": 0.8912 if cache_hit else 0.214,
            "fallback_triggered": fallback,
            "attempted_models": attempted,
            "prompt_tokens": pt,
            "completion_tokens": ct,
            "total_tokens": pt + ct,
            "cost_usd": round(actual_cost, 6),
            "baseline_cost_usd": round(baseline_cost, 6),
            "savings_usd": round(savings, 6),
            "latency_ms": latency,
            "trace": trace,
        })
