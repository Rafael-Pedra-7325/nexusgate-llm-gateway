import asyncio
import random
import httpx
from typing import List, Dict, Any, Tuple
from app.config import settings, MODEL_CATALOG


class ProviderError(Exception):
    def __init__(self, provider: str, model: str, status_code: int, message: str):
        self.provider = provider
        self.model = model
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{provider}/{model}] HTTP {status_code}: {message}")


def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 1.33))


def _generate_sandbox_answer(prompt: str, model: str, provider: str, complexity_tier: str) -> str:
    lower = prompt.lower()
    if "capital" in lower and "france" in lower:
        return (
            "The capital of France is **Paris**. Located along the Seine River in northern-central France, "
            "it serves as the nation's political, economic, and cultural center."
        )
    if "capital" in lower and ("japan" in lower or "japão" in lower):
        return (
            "The capital of Japan is **Tokyo**. Formerly known as Edo, it is the world's most populous "
            "metropolitan area and Japan's seat of government and finance."
        )
    if "rate limit" in lower or "distributed" in lower or "architecture" in lower:
        return (
            f"### Distributed System Design (Generated via `{model}` on `{provider}`)

"
            "1. **Token Bucket in Redis**: Use atomic Lua scripts (`EVAL`) in Redis Cluster to check and decrement "
            "tokens per tenant key in a single network round-trip.
"
            "2. **Local L1 Sliding Window**: Maintain an in-memory approximate counter with 100ms sync intervals to "
            "absorb traffic spikes without saturating Redis.
"
            "3. **Graceful Degradation**: Return `HTTP 429` with `Retry-After` headers and fail-open policies if "
            "the coordination store experiences transient partitioning."
        )
    if "quicksort" in lower or "code" in lower or "python" in lower or "sql" in lower:
        return (
            f"Here is an optimized implementation produced by **`{model}`**:

"
            "```python
"
            "def quicksort(arr: list[int]) -> list[int]:
"
            "    if len(arr) <= 1:
"
            "        return arr
"
            "    pivot = arr[len(arr) // 2]
"
            "    left = [x for x in arr if x < pivot]
"
            "    mid = [x for x in arr if x == pivot]
"
            "    right = [x for x in arr if x > pivot]
"
            "    return quicksort(left) + mid + quicksort(right)
"
            "```"
        )

    preview = prompt[:90] + ("..." if len(prompt) > 90 else "")
    return (
        f"**[{MODEL_CATALOG[model]['display_name']} • {provider.upper()}]** "
        f"Processed `{complexity_tier}` tier request for: *"{preview}"*. "
        "NexusGate dynamically selected this model to optimize quality-per-dollar and latency SLAs."
    )


async def invoke_model(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 512,
    complexity_tier: str = "simple",
    force_fail: bool = False,
) -> Tuple[str, Dict[str, int]]:
    meta = MODEL_CATALOG[model]
    provider = meta["provider"]

    if force_fail:
        await asyncio.sleep(0.08)
        raise ProviderError(
            provider=provider,
            model=model,
            status_code=429,
            message="Simulated upstream 429 Too Many Requests / Rate Limit Exceeded",
        )

    # Check if live key is configured and sandbox mode is disabled
    has_key = (
        (provider == "openai" and bool(settings.openai_api_key))
        or (provider == "anthropic" and bool(settings.anthropic_api_key))
        or (provider == "groq" and bool(settings.groq_api_key))
    )

    if not settings.sandbox_mode and has_key:
        if provider == "openai":
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                if resp.status_code >= 400:
                    raise ProviderError(provider, model, resp.status_code, resp.text[:200])
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                return text, {
                    "prompt_tokens": usage.get("prompt_tokens", 20),
                    "completion_tokens": usage.get("completion_tokens", 40),
                    "total_tokens": usage.get("total_tokens", 60),
                }

        if provider == "groq":
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                if resp.status_code >= 400:
                    raise ProviderError(provider, model, resp.status_code, resp.text[:200])
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                return text, {
                    "prompt_tokens": usage.get("prompt_tokens", 20),
                    "completion_tokens": usage.get("completion_tokens", 40),
                    "total_tokens": usage.get("total_tokens", 60),
                }

        if provider == "anthropic":
            system_msg = "
".join(m["content"] for m in messages if m["role"] == "system")
            user_msgs = [m for m in messages if m["role"] != "system"]
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-3-5-sonnet-20241022" if "sonnet" in model else "claude-3-5-haiku-20241022",
                        "max_tokens": max_tokens,
                        "system": system_msg or "You are a helpful AI assistant.",
                        "messages": user_msgs,
                    },
                )
                if resp.status_code >= 400:
                    raise ProviderError(provider, model, resp.status_code, resp.text[:200])
                data = resp.json()
                text = data["content"][0]["text"]
                usage = data.get("usage", {})
                pt = usage.get("input_tokens", 25)
                ct = usage.get("output_tokens", 45)
                return text, {
                    "prompt_tokens": pt,
                    "completion_tokens": ct,
                    "total_tokens": pt + ct,
                }

    # Realistic Sandbox Simulation Mode
    base_delay = meta["avg_latency_ms"] / 1000.0
    jitter = random.uniform(-0.08, 0.12)
    await asyncio.sleep(max(0.06, (base_delay * 0.35) + jitter))

    user_prompt = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    response_text = _generate_sandbox_answer(user_prompt, model, provider, complexity_tier)

    prompt_tokens = sum(_estimate_tokens(m["content"]) for m in messages)
    completion_tokens = _estimate_tokens(response_text)
    return response_text, {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
