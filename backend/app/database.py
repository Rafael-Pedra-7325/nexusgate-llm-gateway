import sqlite3
import json
from typing import Dict, Any, List
from app.config import settings


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            prompt_preview TEXT NOT NULL,
            routing_strategy TEXT NOT NULL,
            complexity_score REAL NOT NULL,
            complexity_tier TEXT NOT NULL,
            selected_model TEXT NOT NULL,
            provider TEXT NOT NULL,
            cache_hit INTEGER NOT NULL,
            cache_similarity REAL,
            fallback_triggered INTEGER NOT NULL,
            attempted_models TEXT NOT NULL,
            prompt_tokens INTEGER NOT NULL,
            completion_tokens INTEGER NOT NULL,
            total_tokens INTEGER NOT NULL,
            cost_usd REAL NOT NULL,
            baseline_cost_usd REAL NOT NULL,
            savings_usd REAL NOT NULL,
            latency_ms REAL NOT NULL,
            trace_json TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def count_logs() -> int:
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) as cnt FROM request_logs")
    row = cur.fetchone()
    conn.close()
    return int(row["cnt"]) if row else 0


def insert_log(record: Dict[str, Any]):
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO request_logs (
            request_id, created_at, prompt_preview, routing_strategy,
            complexity_score, complexity_tier, selected_model, provider,
            cache_hit, cache_similarity, fallback_triggered, attempted_models,
            prompt_tokens, completion_tokens, total_tokens,
            cost_usd, baseline_cost_usd, savings_usd, latency_ms, trace_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["request_id"],
            record["created_at"],
            record["prompt_preview"],
            record["routing_strategy"],
            record["complexity_score"],
            record["complexity_tier"],
            record["selected_model"],
            record["provider"],
            1 if record["cache_hit"] else 0,
            record.get("cache_similarity"),
            1 if record["fallback_triggered"] else 0,
            json.dumps(record["attempted_models"]),
            record["prompt_tokens"],
            record["completion_tokens"],
            record["total_tokens"],
            record["cost_usd"],
            record["baseline_cost_usd"],
            record["savings_usd"],
            record["latency_ms"],
            json.dumps(record["trace"]),
        ),
    )
    conn.commit()
    conn.close()


def fetch_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM request_logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        item = dict(r)
        item["cache_hit"] = bool(item["cache_hit"])
        item["fallback_triggered"] = bool(item["fallback_triggered"])
        item["attempted_models"] = json.loads(item["attempted_models"])
        item["trace"] = json.loads(item["trace_json"])
        del item["trace_json"]
        results.append(item)
    return results


def fetch_analytics_summary() -> Dict[str, Any]:
    conn = get_conn()
    agg = conn.execute(
        """
        SELECT
            COUNT(*) as total_requests,
            COALESCE(SUM(total_tokens), 0) as total_tokens,
            COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
            COALESCE(SUM(completion_tokens), 0) as completion_tokens,
            COALESCE(SUM(cost_usd), 0.0) as total_cost_usd,
            COALESCE(SUM(baseline_cost_usd), 0.0) as total_baseline_cost_usd,
            COALESCE(SUM(savings_usd), 0.0) as total_savings_usd,
            COALESCE(AVG(latency_ms), 0.0) as avg_latency_ms,
            COALESCE(SUM(cache_hit), 0) as cache_hits,
            COALESCE(SUM(fallback_triggered), 0) as fallback_count
        FROM request_logs
        """
    ).fetchone()

    latencies = [
        r["latency_ms"]
        for r in conn.execute("SELECT latency_ms FROM request_logs ORDER BY latency_ms ASC").fetchall()
    ]
    p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

    by_model_rows = conn.execute(
        """
        SELECT
            selected_model as model,
            provider,
            COUNT(*) as requests,
            SUM(total_tokens) as tokens,
            ROUND(SUM(cost_usd), 6) as cost_usd,
            ROUND(AVG(latency_ms), 1) as avg_latency_ms
        FROM request_logs
        GROUP BY selected_model, provider
        ORDER BY requests DESC
        """
    ).fetchall()

    # Time-series bucketed by hour/group for clean chart visualization
    series_rows = conn.execute(
        """
        SELECT
            substr(created_at, 12, 5) as time_bucket,
            COUNT(*) as requests,
            SUM(total_tokens) as tokens,
            ROUND(SUM(cost_usd), 5) as actual_cost,
            ROUND(SUM(baseline_cost_usd), 5) as baseline_cost,
            ROUND(AVG(latency_ms), 1) as avg_latency
        FROM (
            SELECT * FROM request_logs ORDER BY id DESC LIMIT 120
        )
        GROUP BY substr(created_at, 1, 15)
        ORDER BY MIN(id) ASC
        """
    ).fetchall()

    conn.close()

    total_req = int(agg["total_requests"])
    cache_hits = int(agg["cache_hits"])
    total_cost = float(agg["total_cost_usd"])
    baseline_cost = float(agg["total_baseline_cost_usd"])
    savings = float(agg["total_savings_usd"])
    savings_pct = round((savings / baseline_cost) * 100, 1) if baseline_cost > 0 else 0.0
    cache_hit_rate = round((cache_hits / total_req) * 100, 1) if total_req > 0 else 0.0

    return {
        "kpis": {
            "total_requests": total_req,
            "total_tokens": int(agg["total_tokens"]),
            "prompt_tokens": int(agg["prompt_tokens"]),
            "completion_tokens": int(agg["completion_tokens"]),
            "total_cost_usd": round(total_cost, 5),
            "baseline_cost_usd": round(baseline_cost, 5),
            "total_savings_usd": round(savings, 5),
            "savings_percentage": savings_pct,
            "avg_latency_ms": round(float(agg["avg_latency_ms"]), 1),
            "p95_latency_ms": round(float(p95_latency), 1),
            "cache_hits": cache_hits,
            "cache_hit_rate": cache_hit_rate,
            "fallback_count": int(agg["fallback_count"]),
        },
        "model_breakdown": [dict(r) for r in by_model_rows],
        "timeseries": [dict(r) for r in series_rows],
    }
