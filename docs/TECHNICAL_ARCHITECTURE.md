# SignalOS — Technical Architecture & Agent Workflow Specification

**Document Version**: 2.0.0  
**Target Audience**: Systems Architects, AI Engineers, Enterprise Security Officers, GTM Engineering Leads  
**Classification**: Technical Design Document (TDD) & System Architecture Specification  

---

## 1. Executive System Overview

**SignalOS** is an enterprise-grade autonomous Go-To-Market (GTM) agent platform designed to automate end-to-end B2B sales development workflows. It identifies high-propensity target accounts, ingests multi-source market signals (funding rounds, engineering hiring spikes, technology stack migrations), verifies qualification criteria via hybrid scoring algorithms, queries tenant-isolated vector databases for product context, synthesizes zero-hallucination personalized outreach copy, and enforces deterministic human-in-the-loop (HITL) approval gates prior to executing external actions.

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       SignalOS Platform Topology                                      │
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘

  [ Web Client / UI ] ──(HTTPS/WSS/SSE)──> [ Application Load Balancer / Ingress ]
                                                          │
                                                          ▼
                                            [ FastAPI Gateway (asyncpg) ]
                                                          │
                    ┌─────────────────────────────────────┼─────────────────────────────────────┐
                    ▼                                     ▼                                     ▼
     [ PostgreSQL 16 + pgvector ]                 [ Redis 7 Cluster ]                  [ Async Task Workers ]
     • Multi-tenant Core Schemas                  • Distributed Locks                  • Campaign Batch Engine
     • Document Chunks & HNSW Index               • Real-time SSE Pub/Sub              • Distributed Task Queues
     • Agent Checkpoints & Audit Logs             • API Rate Limiting                  • Lead Ingestion Pipeline
                                                          │
                                                          ▼
                                             [ LangGraph Orchestration ]
                                                          │
         ┌────────────────────────────────────────────────┼────────────────────────────────────────────────┐
         ▼                                                ▼                                                ▼
 ┌───────────────┐                              ┌───────────────────┐                            ┌───────────────────┐
 │ Research &    │                              │ Knowledge &       │                            │ Quality & Safety  │
 │ Enrichment    │                              │ Intelligence      │                            │ Governance        │
 │ ───────────── │                              │ ───────────────── │                            │ ───────────────── │
 │ • Web Search  │                              │ • pgvector RAG    │                            │ • SSRF Protection │
 │ • Page Fetch  │                              │ • Hybrid Scoring  │                            │ • Critic Guard    │
 │ • CRM Tool    │                              │ • LLM Router      │                            │ • HITL Gateways   │
 └───────────────┘                              └───────────────────┘                            └───────────────────┘
```

---

## 2. High-Level System Architecture & Component Topology

SignalOS is organized into 6 core architectural subsystems:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. CLIENT & PRESENTATION TIER                                                                          │
│    • React 18 + TypeScript + Vite SPA                                                                  │
│    • Real-Time Agent Streamer (Server-Sent Events / SSE)                                               │
│    • Human Approval Hub & Interactive DAG Visualizer                                                   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                  │ REST / SSE
                                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. API GATEWAY & CONTROL PLANE                                                                         │
│    • FastAPI Async REST Engine (Python 3.11+, asyncpg, Pydantic v2)                                    │
│    • Correlation Context Tracking (X-Request-ID, Structlog)                                           │
│    • Tenant Isolation Middleware & Role-Based Access Control (RBAC)                                    │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                  │
         ┌────────────────────────────────────────┴────────────────────────────────────────┐
         ▼                                                                                 ▼
┌────────────────────────────────────────┐                       ┌────────────────────────────────────────┐
│ 3. PERSISTENCE & CACHING TIER          │                       │ 4. DISTRIBUTED EXECUTION TIER          │
│    • PostgreSQL 16: Multi-Tenant RDBMS │                       │    • Queue Manager & Batch Dispatchers │
│    • pgvector: HNSW Cosine Search (1536d)                       │    • Cursor-based 10M Lead Paginator  │
│    • Redis 7: Distributed Locks & SSE  │                       │    • Concurrency & Backpressure Guards │
└────────────────────────────────────────┘                       └────────────────────────────────────────┘
                                                                                   │
                                                                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 5. AGENTIC REASONING & ORCHESTRATION ENGINE (LangGraph StateGraph)                                     │
│    • Explicit Typed State Machine (`SDRState`)                                                         │
│    • Cyclic Graph Topology with Self-Correction Feedback Loops                                         │
│    • Zero-Hallucination Critic Node & Evidence Grounding Verification                                  │
│    • Deterministic Human-in-the-Loop Interruption Handlers                                             │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                  │
         ┌────────────────────────────────────────┴────────────────────────────────────────┐
         ▼                                                                                 ▼
┌────────────────────────────────────────┐                       ┌────────────────────────────────────────┐
│ 6. TOOL REGISTRY & SECURITY SHIELD     │                       │ 7. MULTI-PROVIDER LLM ROUTER           │
│    • In-Memory SSRF IP/DNS Filter      │                       │    • Dynamic Multi-Model Dispatcher    │
│    • Rate-Limited Web Search & Scraper │                       │    • Automatic Failover Chain          │
│    • Idempotent Action Dispatcher      │                       │    • Real-Time USD & Token Ledger      │
└────────────────────────────────────────┘                       └────────────────────────────────────────┘
```

---

## 3. Deep-Dive Component Breakdown

### 3.1. API Gateway & Control Plane (`backend/app/api/`)
* **Technology**: FastAPI, `asyncpg`, Pydantic v2, `structlog`.
* **Key Responsibilities**:
  * **Ingress & Correlation Tracing**: Intercepts every inbound request, binds a unique `X-Request-ID` into `structlog` contextvars, and records response latency headers (`X-Response-Time`).
  * **Tenant-Scoped Authorization**: Validates JWT tokens, extracts `organization_id`, and enforces row-level tenant boundary checks across all ORM queries.
  * **Unified Error Schema**: Converts all domain errors (`AppError`, `NotFoundError`, `SecurityError`, `ValidationError`) into standard structured error payloads with correlated request IDs.
  * **Real-time SSE Streaming**: Emits agent execution step events, token consumption updates, tool outputs, and status transitions directly to the browser.

### 3.2. Relational & Vector Storage (`backend/app/db/`)
* **Technology**: PostgreSQL 16 + `pgvector` extension, SQLAlchemy 2.0 (Async).
* **Multi-Tenant Relational Entities**:
  * `organizations` & `users`: Multi-tenant boundary and RBAC controls.
  * `companies` & `contacts`: Verified business entities and prospect personas.
  * `campaigns` & `campaign_leads`: Outbound initiatives, ICP definitions, and lead association states.
  * `agent_runs` & `tool_calls`: Granular execution logs, state checkpoints, token usage, and latency records.
  * `actions` & `audit_logs`: Durable idempotency registers and compliance audit trails.
* **Vector Knowledge Retrieval (`knowledge_documents` & `document_chunks`)**:
  * Ingests sales battlecards, product whitepapers, case studies, and pitch guidelines.
  * Generates 1536-dimensional embeddings (`text-embedding-3-small`).
  * Creates an HNSW index with Cosine Similarity metric (`vector_cosine_ops`) for sub-10ms context retrieval filtered by `organization_id`.

### 3.3. Multi-Provider LLM Router & Cost Engine (`backend/app/llm/`)
* **Technology**: Custom unified abstraction layer supporting OpenAI (`gpt-4o`, `gpt-4o-mini`), Anthropic (`claude-3-5-sonnet`), Google Gemini (`gemini-1.5-pro`), and deterministic MockProvider for local CI/CD testing.
* **Key Mechanisms**:
  * **Dynamic Model Routing**: Routes lightweight extraction tasks to cost-effective models (`gpt-4o-mini`) and complex reasoning/copywriting/critic tasks to flagship models (`gpt-4o` or `claude-3-5-sonnet`).
  * **Resilient Fallback Chains**: If a primary LLM endpoint throws a rate-limit (HTTP 429), timeout, or service error (HTTP 5xx), the router cascades automatically to secondary and tertiary providers:
    $$\text{OpenAI} \longrightarrow \text{Anthropic} \longrightarrow \text{Gemini} \longrightarrow \text{Mock (Safe Degradation)}$$
  * **Exact Cost & Token Ledger**: Tracks exact prompt tokens, completion tokens, and dollar costs calculated using exact per-token pricing tables.

### 3.4. Safe Tool Registry & Security Perimeter (`backend/app/agents/tools/`)
* **SSRF Protection (`fetch_page.py`)**:
  * Protects against Server-Side Request Forgery by resolving hostnames to IP addresses before initiating HTTP connections.
  * Validates against RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopbacks (`127.0.0.0/8`), link-local IPs (`169.254.0.0/16`), and AWS EC2 instance metadata endpoints (`169.254.169.254`).
  * Disallows non-standard schemas (`file://`, `gopher://`, `ftp://`), permitting only `http://` and `https://`.
* **Prompt Injection Defense**:
  * Strips HTML scripts, styling, hidden divs, and known jailbreak syntax before injecting web-scraped content into LLM prompt contexts.
* **Idempotency Guarantee (`action_service.py`)**:
  * Every mutation (e.g., `send_email`, `crm_update`) is prefixed with a deterministic key:
    $$\text{Idempotency Key} = \text{campaign\_id} : \text{lead\_id} : \text{action\_type}$$
  * A database unique constraint on `idempotency_key` guarantees that network retries or worker duplicate deliveries never result in duplicate external outreach.

### 3.5. Batch Orchestration & Scale Engine (`backend/app/workers/`)
* **Capacity Goal**: Process 10,000,000 leads across concurrent campaigns without memory starvation.
* **Mechanisms**:
  * **Cursor-Based Pagination**: Reads database leads using bounded ID cursors (`WHERE id > :last_id ORDER BY id ASC LIMIT 500`) instead of expensive `OFFSET` queries.
  * **Async Task Worker Queues**: Ingestion tasks dispatch jobs onto Redis queues with bounded concurrency pools.
  * **Backpressure Throttling**: Monitors LLM token bucket consumption and dynamically slows dispatch when provider rate limits are approached.

---

## 4. Agent Architecture: The LangGraph State Machine

SignalOS implements an explicit, stateful, cyclic computational graph using **LangGraph**. Unlike unbounded autonomous loops, SignalOS structures agent decision-making into deterministic nodes with typed inputs, outputs, and conditional edges.

```
                                  [ START ]
                                      │
                                      ▼
                                [ 1. Planner ]
                                      │
                                      ▼
                           [ 2. Company Discovery ]
                                      │
                                      ▼
                               [ 3. Research ] ◄─────────────────────────────────┐
                                      │                                          │
                                      ▼                                          │ (Critic Failed &
                           [ 4. Contact Discovery ]                              │  Iterations < 2)
                                      │                                          │
                                      ▼                                          │
                              [ 5. Enrichment ]                                  │
                                      │                                          │
                                      ▼                                          │
                           [ 6. Signal Detection ]                               │
                                      │                                          │
                                      ▼                                          │
                           [ 7. RAG Knowledge Fetch ]                            │
                                      │                                          │
                                      ▼                                          │
                             [ 8. Hybrid Scoring ]                               │
                                      │                                          │
                                      ▼                                          │
                            [ 9. Personalization ]                               │
                                      │                                          │
                                      ▼                                          │
                              [ 10. Critic Guard ] ──────────────────────────────┘
                                      │
                                      ▼ (Critic Passed OR Iterations >= 2)
                             [ 11. Human Approval ]
                                      │
                     ┌────────────────┴────────────────┐
                     │ (Approved == True)              │ (Approved == False)
                     ▼                                 ▼
           [ 12. Idempotent Execution ]             [ END ]
                     │
                     ▼
                  [ END ]
```

### 4.1. Typed State Structure (`SDRState`)

The entire context of an agent execution is held in a strongly typed dictionary:

```python
class SDRState(TypedDict, total=False):
    # Context Identifiers
    organization_id: str
    campaign_id: str
    lead_id: str
    agent_run_id: str
    objective: str

    # Target Entities
    company: Dict[str, Any]
    contact: Dict[str, Any]
    icp: Dict[str, Any]

    # Research & Signals
    research_plan: Dict[str, Any]
    research: List[Dict[str, Any]]
    signals: List[Dict[str, Any]]
    retrieved_context: List[Dict[str, Any]]

    # Hybrid Qualification
    score: float
    score_reasons: List[str]
    score_confidence: float

    # Copy Synthesis & Evidence Tracking
    email_subject: str
    email_body: str
    evidence_claims: List[Dict[str, Any]]

    # Quality Assurance & Iteration
    critic_feedback: str
    critic_passed: bool
    research_iterations: int

    # Safety & Telemetry
    tool_calls: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    step_count: int
    total_tokens: int
    total_cost_usd: float

    # Execution Gates
    requires_human_approval: bool
    approved: bool
    action_executed: bool
    action_result: Dict[str, Any]
```

### 4.2. Sequential Node Responsibilities & Logic

| Step | Node Name | Implementation Purpose | Primary Inputs / Tools | Outputs / State Mutations |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **`planner`** | Formulates target-specific research objectives based on campaign ICP and company domain. | `company`, `icp`, `objective` | `research_plan` |
| **2** | **`company_discovery`** | Resolves verified company data, industry classification, employee count, and website. | `web_search`, `fetch_page` | `company` (enriched) |
| **3** | **`research`** | Performs deep web searches for press releases, engineering blogs, and leadership updates. | `web_search`, `fetch_page` | `research` list, increments `research_iterations` |
| **4** | **`contact_discovery`** | Identifies optimal buyer persona (e.g. VP Eng, CTO) matching campaign criteria. | `company`, `icp.target_personas` | `contact` |
| **5** | **`enrichment`** | Enriches prospect's LinkedIn profile, role tenure, and verified business email. | `crm_tool`, `web_search` | `contact` (enriched) |
| **6** | **`signal_detection`** | Extracts explicit buying triggers: funding rounds, active hiring spikes, technology migrations. | `research`, `llm_router` | `signals` list with extracted evidence snippets |
| **7** | **`rag_retrieval`** | Retrieves relevant pitch angles, case studies, and value props from `pgvector` knowledge base. | `rag_tool` (cosine similarity) | `retrieved_context` |
| **8** | **`scoring`** | Executes deterministic & qualitative hybrid qualification formula. | `scoring_service.compute_score` | `score`, `score_reasons`, `score_confidence` |
| **9** | **`personalization`** | Synthesizes 1-to-1 cold outreach copy grounded strictly in detected signals and RAG context. | `prompts.personalization_prompt` | `email_subject`, `email_body`, `evidence_claims` |
| **10** | **`critic`** | Evaluates generated email against evidence claims; detects unsupported assertions and hallucinations. | Zero-hallucination verification prompt | `critic_passed`, `critic_feedback` |
| **11** | **`approval`** | Inspects qualification threshold and human-in-the-loop policies; sets status to `WAITING_APPROVAL`. | `score`, `requires_human_approval` | `requires_human_approval`, `approved` |
| **12** | **`execution`** | Dispatches email or updates CRM via idempotent action executor upon human sign-off. | `action_service.execute_action` | `action_executed`, `action_result` |

---

## 5. End-to-End Execution Workflow

```
[ Ingest Lead ] ──> [ Planner ] ──> [ Company / Contact Discovery ] ──> [ Web Extraction & SSRF Check ]
                                                                                   │
                                                                                   ▼
[ RAG Knowledge Retrieval ] ◄── [ Signal Detection (Funding / Hiring / Tech) ] ◄───┘
            │
            ▼
[ Hybrid Scoring Engine ] ──> [ Personalized Copy Synthesis ] ──> [ Critic Node (Hallucination Guard) ]
                                                                                   │
                                                                   ┌───────────────┴───────────────┐
                                              (Failed & Retries<2) │                               │ (Passed)
                                                                   ▼                               ▼
                                                        [ Research Node Retry ]       [ Human Approval Gate ]
                                                                                                   │
                                                                                   ┌───────────────┴───────────────┐
                                                                                   │ (Approved)                    │ (Rejected)
                                                                                   ▼                               ▼
                                                                      [ Idempotent Dispatcher ]                 [ Discard ]
                                                                                   │
                                                                                   ▼
                                                                           [ CRM / Outbound ]
```

### 5.1. The Hybrid Lead Qualification Algorithm

SignalOS avoids purely subjective LLM scoring by combining deterministic rule evaluation with qualitative LLM signal confidence:

$$\text{Final Score} = \sum_{i} w_i \cdot S_i \times C_{\text{data}}$$

Where:
1. **Company Size Fit ($w_1 = 0.30$)**: Strict deterministic match against campaign employee bands (e.g., 50–500 employees).
2. **Industry & Tech Stack Fit ($w_2 = 0.20$)**: Keyword and semantic overlap between target company description and ICP definitions.
3. **Persona Seniority Match ($w_3 = 0.20$)**: Title hierarchy matching (CTO/VP Eng = 100%, Director = 80%, Lead = 50%).
4. **Qualitative Buying Signals ($w_4 = 0.30$)**: Recency and impact of detected signals:
   * Funding round within last 90 days: $+30\text{ pts}$
   * Active backend/platform engineering hiring spike: $+25\text{ pts}$
   * Active cloud/database technology migration: $+20\text{ pts}$
5. **Data Confidence Multiplier ($C_{\text{data}} \in [0.85, 1.0]$)**: Weighted based on the verification status of corporate domain, email deliverability, and source URL freshness.

### 5.2. Zero-Hallucination Critic Guardrail

The **Critic Node** inspects every generated sentence in `email_body` and maps it directly against `evidence_claims`:
* **Rule 1**: Every factual statement (e.g., *"Noticed your recent $18M Series A"*) must have an identical cited snippet in `state["signals"]`.
* **Rule 2**: Every customer reference or value metric must exist in `state["retrieved_context"]`.
* **Rejection Action**: If an unsubstantiated claim is detected, the Critic sets `critic_passed = False` with explicit feedback. LangGraph routes state back to the `research` node to locate verified proof or eliminate the assertion.
* **Cycle Limiter**: Cycles are bounded to a maximum of 2 iterations (`research_iterations < 2`) to prevent infinite token loops and enforce cost predictability.

---

## 6. Human-in-the-Loop (HITL) Governance & Security

Enterprise GTM actions carry real-world brand and compliance risks. SignalOS guarantees strict boundaries:

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 Autonomous Agent Run                   │
                  └────────────────────────────────────────────────────────┘
                                              │
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │             Status: WAITING_APPROVAL                   │
                  │  • Graph paused at Approval Node                       │
                  │  • State serialized to PostgreSQL                      │
                  │  • Review notification dispatched                      │
                  └────────────────────────────────────────────────────────┘
                                              │
                         ┌────────────────────┴────────────────────┐
                         ▼                                         ▼
            [ Human Approves / Edits ]                     [ Human Rejects ]
                         │                                         │
                         ▼                                         ▼
      ┌──────────────────────────────────────┐          ┌──────────────────────┐
      │  Status: RUNNING                     │          │  Status: REJECTED    │
      │  • Graph resumed from checkpoint     │          │  • Graph terminates  │
      │  • Idempotency key locked            │          │  • Audit reason log  │
      │  • Side effect dispatched (Email/CRM)│          └──────────────────────┘
      └──────────────────────────────────────┘
```

1. **Stateful Breakpoints**: When an agent completes drafting and passes Critic evaluation, the run enters `WAITING_APPROVAL`. The exact state is saved in PostgreSQL.
2. **Interactive UI Review**: Operators review the prospect profile, detected signal evidence, exact retrieved RAG chunks, and drafted copy in the SignalOS web interface. Operators can edit copy directly or click **Approve & Send**.
3. **Resumption Protocol**: The `/api/v1/approvals/{id}/approve` endpoint loads the serialized graph, updates the state with any manual copy modifications, sets `approved = True`, and resumes the graph into the `execution` node.

---

## 7. Operational Observability, Tracing & Evaluation

### 7.1. Real-Time Telemetry & SSE Streaming
* Every node transition emits a typed event over Server-Sent Events (`/api/v1/agent-runs/{id}/stream`):
  * `step_start`: Node name, input state snapshot.
  * `tool_call`: Tool name, sanitized arguments, execution latency in milliseconds.
  * `llm_usage`: Model name, prompt tokens, completion tokens, step cost in USD.
  * `step_complete`: Output state delta, updated total cost.
  * `state_change`: Run status transition (`RUNNING` $\rightarrow$ `WAITING_APPROVAL` $\rightarrow$ `COMPLETED`).

### 7.2. Continuous Evaluation Benchmark Suite (`backend/app/evaluation/`)
SignalOS includes an automated evaluation harness (`evaluator.py`) running across standardized benchmark datasets (`dataset.py`):

| Evaluation Metric | Target Threshold | Assessment Methodology |
| :--- | :--- | :--- |
| **Groundedness / Hallucination Rate** | $< 1.0\%$ | Critic LLM verifies 100% of body claims against ground-truth evidence snippets. |
| **Scoring Consistency** | $> 95\%$ | Evaluates ICP scoring output against standardized golden test sets. |
| **SSRF Security Block Rate** | $100.0\%$ | Automated test suite verifies private IP / metadata endpoint blocking. |
| **End-to-End Latency** | $< 12.0\text{s}$ | P95 latency across complete 12-node pipeline execution. |
| **Cost Per Qualified Lead** | $< \$0.05$ | Total LLM + search tool consumption per enriched account. |

---

## 8. Summary Comparison: Architectural Decisions

| Decision Area | Selected Architecture | Evaluated Alternative | Decisive Rationale |
| :--- | :--- | :--- | :--- |
| **Agent Framework** | **LangGraph (StateGraph)** | CrewAI / AutoGen | Explicit typed state, deterministic cyclic loops, and native human-in-the-loop pause/resume checkpoints. |
| **Vector Storage** | **PostgreSQL + `pgvector`** | Pinecone / Qdrant | Single database engine for relational tables and vector embeddings; transactional ACID guarantees with zero data synchronization lag. |
| **API Framework** | **FastAPI + asyncpg** | Node.js / Go | Native Python async IO allowing direct in-process execution of LangGraph agents and Pydantic validation schemas. |
| **Tool Security** | **In-Memory SSRF Socket Guard** | Proxy / WAF only | Zero-latency DNS/IP inspection before opening socket connections, immune to DNS rebinding attacks. |
| **Action Execution** | **Idempotent Unique DB Index** | Distributed locks only | Guarantees zero duplicate outreach emails even under severe network retries or database reconnections. |

---

*SignalOS Architecture Specification — Approved for Production Deployment.*
