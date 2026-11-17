import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Point tests to an isolated temporary SQLite database
tmp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
tmp_db.close()
os.environ["DATABASE_PATH"] = tmp_db.name
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["SANDBOX_MODE"] = "true"

from app.main import app  # noqa: E402
from app.router import analyze_complexity  # noqa: E402
from app.semantic_cache import semantic_cache  # noqa: E402


def test_complexity_classifier():
    low_score, low_tier, _ = analyze_complexity("What is 2 + 2?")
    assert low_tier == "simple"
    assert low_score < 0.34

    high_score, high_tier, _ = analyze_complexity(
        "Design a distributed consensus algorithm comparing Raft and Paxos trade-offs "
        "under network partitions and implement a Python state machine simulation."
    )
    assert high_tier == "complex"
    assert high_score >= 0.66


def test_semantic_cache_and_routing_flow():
    semantic_cache.clear()
    with TestClient(app) as client:
        # 1. First request -> Cache MISS, routed to simple/cheap model
        res1 = client.post(
            "/v1/chat/completions",
            json={
                "model": "auto",
                "routing_strategy": "complexity",
                "messages": [{"role": "user", "content": "What is the capital of France?"}],
            },
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["gateway"]["cache_hit"] is False
        assert data1["gateway"]["complexity_tier"] == "simple"
        assert data1["gateway"]["selected_model"] == "llama-3.1-8b-instant"

        # 2. Paraphrased follow-up -> Semantic Cache HIT at $0.00 cost
        res2 = client.post(
            "/v1/chat/completions",
            json={
                "model": "auto",
                "routing_strategy": "complexity",
                "messages": [{"role": "user", "content": "Tell me France's capital city"}],
            },
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["gateway"]["cache_hit"] is True
        assert data2["gateway"]["cost_usd"] == 0.0
        assert data2["gateway"]["cache_similarity"] >= 0.72


def test_automatic_fallback_on_provider_failure():
    semantic_cache.clear()
    with TestClient(app) as client:
        res = client.post(
            "/v1/chat/completions",
            json={
                "model": "auto",
                "routing_strategy": "complexity",
                "use_cache": False,
                "simulate_failure": True,
                "messages": [
                    {
                        "role": "user",
                        "content": "Architect a distributed rate limiter in Python with Redis Lua scripts",
                    }
                ],
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["gateway"]["fallback_triggered"] is True
        assert len(body["gateway"]["attempted_models"]) == 2
        assert body["gateway"]["attempted_models"][0] == "gpt-4o"
        assert body["gateway"]["selected_model"] == "claude-3-5-sonnet"
