# ⚡ NexusGate — Intelligent LLM Gateway & Observability Control Plane

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**NexusGate** is a production-grade, OpenAI-compatible **LLM Proxy Gateway** and **Real-Time Observability Dashboard**. It sits between your applications and foundation model providers (OpenAI, Anthropic, Groq) to cut inference spend by up to **65%**, eliminate single-provider downtime, and provide full token, cost, and latency telemetry.

---

## ✨ Key Capabilities

1. **🧠 Complexity & Cost-Aware Routing Engine**
   - Evaluates prompt structure, token footprint, code blocks, and multi-step reasoning markers in `<1ms` to score prompt complexity (`0.00` – `1.00`).
   - Supports **`complexity`** (routes simple queries to fast/cheap models like `gpt-4o-mini` or `llama-3.1-8b`, and deep reasoning/code to `gpt-4o` / `claude-3-5-sonnet`), **`cost`** (maximizes margin), and **`balanced`** strategies.
2. **⚡ Vector Semantic Cache**
   - Computes dense L2-normalized semantic embeddings and performs cosine-similarity lookups against cached responses.
   - Paraphrased queries (e.g., *"What is the capital of France?"* vs. *"Tell me France's capital city"*) hit the cache in **~2ms** at **$0.00 inference cost**.
3. **🛡️ Automatic Fallback & Circuit Breaker**
   - Configured with ordered multi-provider fallback chains (`OpenAI` → `Anthropic` → `Groq`).
   - Automatically recovers from `429 Rate Limit`, `503 Upstream Unavailable`, or timeout errors while tracking live provider circuit states (`healthy`, `degraded`, `circuit_open`).
4. **📊 Real-Time Telemetry Control Plane**
   - Interactive React + Recharts dashboard tracking **Total Tokens**, **Actual Cost vs. Baseline Cost Savings**, **P50/P95 Latency**, **Cache Hit Rate**, and **Request Execution Traces**.
5. **🔌 Drop-In OpenAI SDK Compatibility + Live Sandbox Mode**
   - Point any OpenAI SDK client to `http://localhost:8000/v1` with zero code changes.
   - Includes a built-in **Sandbox Simulation Mode** so recruiters and reviewers can test routing, semantic caching, and failure recovery immediately without needing paid API keys.

---

## 🏗️ System Architecture

```text
                        ┌─────────────────────────────────────────┐
                        │         Client Application / UI         │
                        │   (OpenAI SDK / REST / Web Playground)  │
                        └────────────────────┬────────────────────┘
                                             │ POST /v1/chat/completions
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                 NEXUSGATE PROXY                                    │
│                                                                                    │
│  ┌──────────────────────┐    HIT     ┌──────────────────────────────────────────┐  │
│  │ 1. Semantic Cache    │───────────►│ Return Cached Response (~2ms, $0.00)     │  │
│  │  (Cosine Similarity) │            └──────────────────────────────────────────┘  │
│  └──────────┬───────────┘                                                          │
│             │ MISS                                                                 │
│             ▼                                                                      │
│  ┌──────────────────────┐            ┌──────────────────────────────────────────┐  │
│  │ 2. Prompt Router     │───────────►│ Complexity Classifier + Cost Optimizer   │  │
│  │  (Cost / Complexity) │            │ Selects Optimal Model Tier               │  │
│  └──────────┬───────────┘            └──────────────────────────────────────────┘  │
│             │                                                                      │
│             ▼                                                                      │
│  ┌──────────────────────┐   ERROR    ┌──────────────────────────────────────────┐  │
│  │ 3. Provider Dispatch │───────────►│ Automatic Fallback & Circuit Breaker     │  │
│  │  (Primary Model)     │            │ OpenAI ──► Anthropic ──► Groq            │  │
│  └──────────┬───────────┘            └────────────────────┬─────────────────────┘  │
│             │                                             │                        │
│             └──────────────────────┬──────────────────────┘                        │
│                                    ▼                                               │
│                     ┌─────────────────────────────┐                                │
│                     │ 4. Async Telemetry Logger   │                                │
│                     │  (SQLite / Cost / Latency)  │                                │
│                     └─────────────────────────────┘                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Docker (Full-Stack Single Container)
```bash
git clone https://github.com/YOUR_USERNAME/llm-gateway.git
cd llm-gateway
docker compose up --build
```
Open **`http://localhost:8000`** to access the Observability Dashboard & Interactive Playground.

### Option 2: Local Development (Backend + Frontend)

**1. Start the FastAPI Gateway (`:8000`)**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**2. Start the React Dashboard (`:5173`)**
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`**.

---

## 🔌 Using with the Official OpenAI Python SDK

NexusGate implements the `/v1/chat/completions` contract, allowing drop-in integration:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="nexus-demo-key",
)

response = client.chat.completions.create(
    model="auto",  # Let NexusGate route based on complexity & cost
    messages=[
        {"role": "user", "content": "Explain consistent hashing and design a distributed cache."}
    ],
    extra_headers={
        "X-Routing-Strategy": "complexity",   # "complexity" | "cost" | "balanced"
        "X-Cache-Threshold": "0.75",
    },
)

print(response.choices[0].message.content)
```

---

## 🌐 Deploying Live for Recruiters

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for a step-by-step guide to deploying NexusGate for **$0/month** on **Render**, **Railway**, or **Fly.io** using the included multi-stage `Dockerfile`.
