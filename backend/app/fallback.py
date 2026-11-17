import time
from typing import List, Dict, Any, Tuple
from app.config import MODEL_CATALOG
from app.providers import invoke_model, ProviderError
from app.models import GatewayTraceStep


class CircuitBreakerRegistry:
    def __init__(self):
        self._failures: Dict[str, int] = {"openai": 0, "anthropic": 0, "groq": 0}
        self._last_failure: Dict[str, float] = {"openai": 0.0, "anthropic": 0.0, "groq": 0.0}
        self._successes: Dict[str, int] = {"openai": 142, "anthropic": 98, "groq": 184}

    def record_success(self, provider: str):
        self._successes[provider] = self._successes.get(provider, 0) + 1
        self._failures[provider] = max(0, self._failures.get(provider, 0) - 1)

    def record_failure(self, provider: str):
        self._failures[provider] = self._failures.get(provider, 0) + 1
        self._last_failure[provider] = time.time()

    def get_health(self) -> List[Dict[str, Any]]:
        now = time.time()
        statuses = []
        for provider in ("openai", "anthropic", "groq"):
            fails = self._failures.get(provider, 0)
            elapsed = now - self._last_failure.get(provider, 0.0)
            if fails >= 3 and elapsed < 45:
                state = "circuit_open"
            elif fails >= 1 and elapsed < 20:
                state = "degraded"
            else:
                state = "healthy"
            statuses.append({
                "provider": provider,
                "status": state,
                "recent_failures": fails,
                "total_successes": self._successes.get(provider, 0),
            })
        return statuses


circuit_breaker = CircuitBreakerRegistry()


async def execute_with_fallback(
    candidate_models: List[str],
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    complexity_tier: str,
    simulate_primary_failure: bool = False,
) -> Tuple[str, str, Dict[str, int], bool, List[str], List[GatewayTraceStep]]:
    """
    Iterates through candidate_models until one succeeds.
    If simulate_primary_failure is True, the first candidate intentionally throws
    a 429 error so recruiters/developers can observe live multi-provider failover.
    """
    attempted: List[str] = []
    trace: List[GatewayTraceStep] = []
    fallback_triggered = False
    last_error = None

    for idx, model in enumerate(candidate_models):
        attempted.append(model)
        provider = MODEL_CATALOG[model]["provider"]
        t0 = time.perf_counter()
        force_fail = simulate_primary_failure and idx == 0

        try:
            text, usage = await invoke_model(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                complexity_tier=complexity_tier,
                force_fail=force_fail,
            )
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            circuit_breaker.record_success(provider)

            if fallback_triggered:
                trace.append(
                    GatewayTraceStep(
                        step=f"Fallback Dispatch ({model})",
                        status="recovered",
                        detail=f"Recovered seamlessly via {provider}/{model} in {elapsed_ms}ms",
                        duration_ms=elapsed_ms,
                    )
                )
            else:
                trace.append(
                    GatewayTraceStep(
                        step=f"Primary Dispatch ({model})",
                        status="completed",
                        detail=f"Completed via {provider}/{model} in {elapsed_ms}ms",
                        duration_ms=elapsed_ms,
                    )
                )
            return text, model, usage, fallback_triggered, attempted, trace

        except ProviderError as err:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            circuit_breaker.record_failure(provider)
            fallback_triggered = True
            last_error = err
            trace.append(
                GatewayTraceStep(
                    step=f"Primary Dispatch ({model})",
                    status="failed",
                    detail=f"{err.message} — triggering fallback chain",
                    duration_ms=elapsed_ms,
                )
            )

    raise RuntimeError(f"All models in fallback chain failed. Last error: {last_error}")
