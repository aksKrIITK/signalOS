# SignalOS — Production AI GTM Agent Platform

SignalOS is an enterprise-grade autonomous GTM agent platform for modern B2B revenue teams. It discovers accounts, extracts data using SSRF-safe web tools, detects buying signals (funding rounds, engineering hiring, technology migrations), queries multi-tenant `pgvector` knowledge bases, computes hybrid qualification scores, drafts evidence-grounded personalized outreach, and executes approved workflows with human sign-off.

---

## Architecture Overview

```
                         React Frontend (Vite + TS)
                                     │
                                     ▼ (REST / SSE)
                              FastAPI Gateway
                                     │
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
        PostgreSQL 16 + pgvector   Redis           Queue Manager
        (Multi-Tenant Accounts &   (Cache, Locks,  (Async Campaign
         Vector Knowledge Base)     Rate Limits)    Batch Workers)
                                                         │
                                                         ▼
                                                 LangGraph Pipeline
                                                         │
                 ┌───────────────────────────────────────┴───────────────────────┐
                 ▼                                                               ▼
        Research & Enrichment                                              Scoring & Copy
                 │                                                               │
                 └───────────────────────────────┬───────────────────────────────┘
                                                 ▼
                                        Safe Tool Registry
                               (SSRF Filter, Web Search, CRM, RAG)
                                                 │
                                                 ▼
                                         LLM Model Router
                                  (OpenAI, Anthropic, Gemini, Mock)
                                                 │
                                                 ▼
                                            Critic Node
                                    (Zero Hallucination Guard)
                                                 │
                                                 ▼
                                        Human Approval Hub
                                                 │
                                                 ▼
                                    Idempotent Action Executor
```

---

## Key Features

1. **Deterministic + LLM Hybrid Scoring**: Deterministic rules (company size 30%, industry match, persona seniority 20%) combined with LLM qualitative signal extraction (funding recency 30%, technology migration) and data confidence weighting (10%).
2. **LangGraph Cyclic State Machine**: Explicit typed `SDRState` with checkpointing, conditional routing (critic rejection -> research retry), loop limits (`MAX_STEPS`, `MAX_COST_USD`), and human approval checkpoints.
3. **SSRF-Protected Web Tools**: Web extraction tool verifies destination IPs against private subnets (RFC 1918, RFC 3927), AWS EC2 metadata endpoints (`169.254.169.254`), and strips prompt injection patterns.
4. **LLM Provider Abstraction & Model Router**: Multi-provider resilience (OpenAI, Anthropic, Gemini) with automated fallback, timeout handling, and exact USD cost calculation.
5. **Multi-Tenant RAG (`pgvector`)**: Tenant-isolated document ingestion, chunking, 1536-dimension embeddings, and HNSW cosine similarity vector retrieval.
6. **Scalable Batch Processing (10M Leads)**: Queue-backed cursor pagination processing leads in bounded batches with backpressure, concurrency throttling, and progress tracking.
7. **Idempotency & Human Approvals**: All external side effects (`send_email`, `crm_update`) use unique idempotency keys (`campaign_id:lead_id:action_type`) to prevent duplicate executions.
8. **Real-time Observability**: Live Server-Sent Events (SSE) streaming execution traces to the UI with step-by-step DAG progress, token consumption, tool latency, and cost ledger.

---

## Bitscale Interview Architecture Deep Dive: The 4 Core Questions

| Component | 1. Why is it there? | 2. What happens if it fails? | 3. How does it scale? | 4. What alternative could you use? |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI + asyncpg** | Non-blocking high-throughput API gateway with automatic OpenAPI documentation. | Connection pool reconnects; healthcheck fails and ALB routes traffic to healthy replicas. | Horizontal scaling via ECS / Kubernetes behind an Application Load Balancer. | Go (Gin), Node.js (Fastify) |
| **PostgreSQL 16 + pgvector** | Unified relational data model with ACID guarantees and in-database vector similarity search. | Read replicas take over; point-in-time recovery via WAL archiving. | Table partitioning by `organization_id`, read replicas, HNSW indexing. | Qdrant, Pinecone, Milvus + Postgres |
| **Redis** | Sub-millisecond distributed locks, rate limiting, and short-lived state coordination. | Critical data remains durable in PostgreSQL; rate limiting falls back to open state. | Redis Cluster with sharding and multi-AZ replication. | Memcached, AWS DynamoDB |
| **LangGraph Orchestrator** | Explicit state machines with cycle support, conditional edges, and native human-in-the-loop pauses. | Run marked as `FAILED`; state persisted to PostgreSQL allowing resumption from last valid node. | Workers run independent stateless graphs; state synced via Redis/Postgres. | Temporal, AWS Step Functions, CrewAI |
| **Model Router & Fallback** | Prevents vendor lock-in, optimizes cost (cheap models for extraction, flagship for reasoning), and guarantees high availability. | Automatically fails over across providers: OpenAI -> Anthropic -> Gemini -> Mock. | Async request multiplexing, client-side rate limit queues. | LiteLLM Proxy, Portkey |
| **SSRF Guard** | Prevents prompt-injected or malicious URLs from probing AWS metadata (`169.254.169.254`) or internal VPC services. | Blocked URLs raise `SecurityError`; agent safely degrades to cached knowledge. | Zero-overhead in-memory IP range verification before socket connection. | Squid Proxy, AWS Network Firewall |
| **Idempotent Action Executor** | Prevents duplicate outreach emails or CRM mutations when retrying failed worker tasks. | If key already exists in `action_executions`, returns previous result without repeating side effect. | Unique database index on `idempotency_key` with high-speed B-Tree lookup. | Redis distributed lock + DB transaction |

---

## Quickstart

### 1. Run via Docker Compose (Recommended)
```bash
docker compose up --build
```
- **React Frontend**: `http://localhost:5173`
- **FastAPI Backend & Swagger**: `http://localhost:8000/docs`
- **Postgres pgvector**: `localhost:5432`
- **Redis**: `localhost:6379`

---

### 2. Local Development Setup

#### Backend:
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## Running the Automated Test Suite

```bash
cd backend
pytest tests/unit tests/agent tests/evaluation -v
```

Output:
```
tests/unit/test_lead_scoring.py::test_perfect_fit_lead_scoring PASSED
tests/unit/test_lead_scoring.py::test_disqualified_lead_scoring PASSED
tests/unit/test_security_ssrf.py::test_ssrf_blocks_localhost PASSED
tests/unit/test_security_ssrf.py::test_ssrf_blocks_aws_metadata PASSED
tests/agent/test_langgraph_flow.py::test_langgraph_full_sdr_execution PASSED
tests/evaluation/test_benchmark_evaluator.py::test_evaluation_benchmark_suite PASSED
```
