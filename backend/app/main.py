import os
import time
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings, MODEL_CATALOG, FALLBACK_CHAINS, BASELINE_MODEL
from app.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatChoice,
    ChatMessage,
    UsageStats,
    GatewayMetadata,
    GatewayTraceStep,
)
from app.database import init_db, insert_log, fetch_recent_logs, fetch_analytics_summary
from app.seeder import seed_initial_telemetry
from app.semantic_cache import semantic_cache
from app.router import analyze_complexity, select_model_and_chain
from app.fallback import execute_with_fallback, circuit_breaker


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.seed_demo_data:
        seed_initial_telemetry()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="OpenAI-compatible LLM Proxy with Complexity/Cost Routing, Semantic Cache, and Failover.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _compute_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    meta = MODEL_CATALOG.get(model, MODEL_CATALOG[BASELINE_MODEL])
    return (prompt_tokens / 1_000_000) * meta["input_cost_per_1m"] + (
        completion_tokens / 1_000_000
    ) * meta["output_cost_per_1m"]


@app.get("/api/health")
async def health_check():
    return {
        "status": "operational",
        "service": settings.app_name,
        "sandbox_mode": settings.sandbox_mode,
        "cache": semantic_cache.stats(),
        "providers": circuit_breaker.get_health(),
    }


@app.get("/api/analytics")
async def get_analytics():
    summary = fetch_analytics_summary()
    summary["providers"] = circuit_breaker.get_health()
    summary["cache"] = semantic_cache.stats()
    summary["sandbox_mode"] = settings.sandbox_mode
    return summary


@app.get("/api/logs")
async def get_logs(limit: int = 50):
    return {"logs": fetch_recent_logs(limit=min(limit, 200))}


@app.get("/api/config")
async def get_gateway_config():
    return {
        "sandbox_mode": settings.sandbox_mode,
        "baseline_model": BASELINE_MODEL,
        "models": MODEL_CATALOG,
        "fallback_chains": FALLBACK_CHAINS,
        "cache": semantic_cache.stats(),
    }


@app.post("/api/cache/clear")
async def clear_semantic_cache():
    cleared = semantic_cache.clear()
    return {"cleared_entries": cleared, "status": "ok"}


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    payload: ChatCompletionRequest,
    x_routing_strategy: Optional[str] = Header(default=None),
    x_cache_threshold: Optional[float] = Header(default=None),
    x_simulate_failure: Optional[bool] = Header(default=None),
):
    t_start = time.perf_counter()
    request_id = f"req_{uuid.uuid4().hex[:12]}"

    strategy = payload.routing_strategy or x_routing_strategy or "complexity"
    if strategy not in ("complexity", "cost", "balanced"):
        strategy = "complexity"

    threshold = (
        payload.cache_threshold
        if payload.cache_threshold is not None
        else (x_cache_threshold if x_cache_threshold is not None else settings.cache_similarity_threshold)
    )
    simulate_failure = bool(payload.simulate_failure or x_simulate_failure)
    use_cache = settings.cache_enabled and (payload.use_cache is not False)

    user_prompt = next(
        (m.content for m in reversed(payload.messages) if m.role == "user"), ""
    )
    if not user_prompt.strip():
        raise HTTPException(status_code=400, detail="At least one non-empty user message is required.")

    trace: list[GatewayTraceStep] = []

    # Step 1: Prompt Complexity Analysis
    t_route = time.perf_counter()
    complexity_score, complexity_tier, signals = analyze_complexity(
        user_prompt, len(payload.messages)
    )

    # Step 2: Semantic Cache Lookup
    if use_cache:
        t_cache = time.perf_counter()
        cached_entry, sim_score = semantic_cache.lookup(user_prompt, threshold=threshold)
        cache_ms = round((time.perf_counter() - t_cache) * 1000, 2)

        if cached_entry is not None:
            total_ms = round((time.perf_counter() - t_start) * 1000, 2)
            usage = cached_entry["usage"]
            model = cached_entry["model"]
            provider = cached_entry["provider"]
            baseline_cost = _compute_cost(
                BASELINE_MODEL, usage["prompt_tokens"], usage["completion_tokens"]
            )

            trace.append(
                GatewayTraceStep(
                    step="Semantic Cache Lookup",
                    status="hit",
                    detail=f"Vector match ({sim_score:.2f} >= {threshold:.2f}) — served from memory",
                    duration_ms=cache_ms,
                )
            )

            insert_log({
                "request_id": request_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "prompt_preview": user_prompt[:100],
                "routing_strategy": strategy,
                "complexity_score": complexity_score,
                "complexity_tier": complexity_tier,
                "selected_model": model,
                "provider": provider,
                "cache_hit": True,
                "cache_similarity": sim_score,
                "fallback_triggered": False,
                "attempted_models": [model],
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "total_tokens": usage["total_tokens"],
                "cost_usd": 0.0,
                "baseline_cost_usd": round(baseline_cost, 6),
                "savings_usd": round(baseline_cost, 6),
                "latency_ms": total_ms,
                "trace": [s.model_dump() for s in trace],
            })

            return ChatCompletionResponse(
                id=request_id,
                created=int(time.time()),
                model=model,
                choices=[
                    ChatChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=cached_entry["response_text"]),
                    )
                ],
                usage=UsageStats(**usage),
                gateway=GatewayMetadata(
                    request_id=request_id,
                    routing_strategy=strategy,
                    complexity_score=complexity_score,
                    complexity_tier=complexity_tier,
                    selected_model=model,
                    provider=provider,
                    cache_hit=True,
                    cache_similarity=sim_score,
                    fallback_triggered=False,
                    attempted_models=[model],
                    latency_ms=total_ms,
                    cost_usd=0.0,
                    baseline_cost_usd=round(baseline_cost, 6),
                    savings_usd=round(baseline_cost, 6),
                    sandbox_mode=settings.sandbox_mode,
                    trace=trace,
                ),
            )
        else:
            trace.append(
                GatewayTraceStep(
                    step="Semantic Cache Lookup",
                    status="miss",
                    detail=f"Best cosine similarity {sim_score:.2f} < threshold {threshold:.2f}",
                    duration_ms=cache_ms,
                )
            )
    else:
        sim_score = 0.0
        trace.append(
            GatewayTraceStep(
                step="Semantic Cache Lookup",
                status="miss",
                detail="Cache bypassed by request flag",
                duration_ms=0.1,
            )
        )

    # Step 3: Routing Decision
    primary_model, chain, route_reason = select_model_and_chain(
        requested_model=payload.model,
        strategy=strategy,
        complexity_tier=complexity_tier,
    )
    route_ms = round((time.perf_counter() - t_route) * 1000, 2)
    signal_note = f" [{', '.join(signals)}]" if signals else ""
    trace.append(
        GatewayTraceStep(
            step=f"Intelligent Router ({strategy})",
            status="routed",
            detail=f"{route_reason} (score={complexity_score}){signal_note}",
            duration_ms=route_ms,
        )
    )

    # Step 4: Provider Execution with Automatic Fallback
    raw_messages = [{"role": m.role, "content": m.content} for m in payload.messages]
    response_text, final_model, usage, fallback_triggered, attempted, exec_trace = (
        await execute_with_fallback(
            candidate_models=chain,
            messages=raw_messages,
            temperature=payload.temperature or 0.7,
            max_tokens=payload.max_tokens or 512,
            complexity_tier=complexity_tier,
            simulate_primary_failure=simulate_failure,
        )
    )
    trace.extend(exec_trace)

    final_provider = MODEL_CATALOG[final_model]["provider"]
    if use_cache:
        semantic_cache.store(user_prompt, response_text, final_model, final_provider, usage)

    total_ms = round((time.perf_counter() - t_start) * 1000, 2)
    actual_cost = _compute_cost(final_model, usage["prompt_tokens"], usage["completion_tokens"])
    baseline_cost = _compute_cost(BASELINE_MODEL, usage["prompt_tokens"], usage["completion_tokens"])
    savings = max(0.0, baseline_cost - actual_cost)

    insert_log({
        "request_id": request_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt_preview": user_prompt[:100],
        "routing_strategy": strategy,
        "complexity_score": complexity_score,
        "complexity_tier": complexity_tier,
        "selected_model": final_model,
        "provider": final_provider,
        "cache_hit": False,
        "cache_similarity": sim_score,
        "fallback_triggered": fallback_triggered,
        "attempted_models": attempted,
        "prompt_tokens": usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
        "total_tokens": usage["total_tokens"],
        "cost_usd": round(actual_cost, 6),
        "baseline_cost_usd": round(baseline_cost, 6),
        "savings_usd": round(savings, 6),
        "latency_ms": total_ms,
        "trace": [s.model_dump() for s in trace],
    })

    return ChatCompletionResponse(
        id=request_id,
        created=int(time.time()),
        model=final_model,
        choices=[
            ChatChoice(
                index=0,
                message=ChatMessage(role="assistant", content=response_text),
            )
        ],
        usage=UsageStats(**usage),
        gateway=GatewayMetadata(
            request_id=request_id,
            routing_strategy=strategy,
            complexity_score=complexity_score,
            complexity_tier=complexity_tier,
            selected_model=final_model,
            provider=final_provider,
            cache_hit=False,
            cache_similarity=sim_score,
            fallback_triggered=fallback_triggered,
            attempted_models=attempted,
            latency_ms=total_ms,
            cost_usd=round(actual_cost, 6),
            baseline_cost_usd=round(baseline_cost, 6),
            savings_usd=round(savings, 6),
            sandbox_mode=settings.sandbox_mode,
            trace=trace,
        ),
    )


# Serve compiled React SPA in single-container production deployments
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
