# Architecture Decision Record: LangGraph vs. CrewAI for Production GTM Orchestration

**Status**: Accepted  
**Decision**: Adopt **LangGraph** as the primary production orchestration framework for SignalOS, maintaining **CrewAI** as a reference POC.

---

## Context & Problem Statement

SignalOS requires an autonomous agentic pipeline that discovers accounts, extracts data with SSRF-safe tools, evaluates buying signals, queries a multi-tenant pgvector knowledge base, computes hybrid scores, drafts evidence-grounded copy, and **pauses deterministically for human approval before executing side effects**.

We evaluated two leading agent frameworks:
1. **LangGraph** (StateGraph / Pregel-based cyclic computational graph)
2. **CrewAI** (Role-playing collaborative multi-agent framework)

---

## Architectural Comparison Matrix

| Dimension | LangGraph (Selected) | CrewAI (POC) |
| :--- | :--- | :--- |
| **State Management** | **Explicit, Typed State (`SDRState`)**. Every node deterministically updates typed state keys. | Implicit conversation history and textual output passing between agents. |
| **Control Flow** | **Cyclic Graphs with Conditional Edges**. Supports explicit loops (e.g., Critic rejecting draft -> back to Research). | Primarily linear sequences or hierarchical manager loops; harder to enforce strict state machines. |
| **Human-in-the-Loop** | Native breakpoint/interruption support at arbitrary graph nodes (`WAITING_APPROVAL`). | Requires custom external hooks and pauses during task execution. |
| **Observability & Checkpointing** | Granular step-by-step checkpointing with durable state serialization to PostgreSQL/Redis. | Logging output streams; less built-in state checkpoint rollback capability. |
| **Tool Execution Safety** | Tools are strictly defined Python functions with explicit argument typing and allowlisting. | Tools passed as agent capabilities; risk of free-form tool calling hallucinations. |
| **Deterministic Business Logic** | Hybrid Python deterministic logic seamlessly intermingled with LLM reasoning nodes. | Heavily oriented around LLM prompts driving every step, increasing latency and cost. |

---

## Decision Rationale

1. **Production Reliability & Auditability**: LangGraph treats agent execution as a state machine where state transitions are explicit, serializable, and auditable. If an agent run crashes at Step 8, the state can be inspected and resumed without repeating prior LLM calls.
2. **Deterministic Guardrails**: LangGraph allows strict policies (`MAX_STEPS`, `MAX_COST_USD`, `MAX_TOOL_CALLS`) to be enforced at each edge evaluation.
3. **Approval State Persistence**: SignalOS requires high-impact actions (sending email, mutating CRM) to pause for human approval. LangGraph's architecture makes state pausing and resumption straightforward.

---

## Conclusion

For enterprise GTM workflows where compliance, auditability, latency, and cost control are paramount, **LangGraph provides the determinism required for production SaaS**. CrewAI remains a valuable prototype for exploratory role-playing research.
