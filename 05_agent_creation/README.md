# Databricks Agent Creation: Product Catalog Assistant

## Purpose

A tool-calling agent that routes between semantic product search, structured policy lookup, and structured customer-service history lookup — the agent-orchestration layer this repo's root CLAUDE.md describes ("An agent routes questions to analytics or document retrieval and reports tool failures clearly"), built here over the product catalog use case instead of the HR use case.

**This is not a proposal.** The agent is logged, evaluated, registered, and deployed — live in the workspace today, confirmed read-only before writing anything in this folder:

| | |
|---|---|
| UC registered model | `uc_agentic_ai.agentic_ai_schema.sai_agent_model`, version 1 |
| Serving endpoint | `agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model` |
| Status | `READY` (scaled to zero) |
| Task | `agent/v1/responses` |
| LLM | `databricks-gpt-oss-120b` |

## What's Here

- [`notebooks/agent.py`](notebooks/agent.py) — the agent definition itself (MLflow `ResponsesAgent`, tool-calling loop), originally authored as an AI Playground export, and the exact code backing the live endpoint.
- [`notebooks/deploy_agent.py`](notebooks/deploy_agent.py) — logs, evaluates, registers, and deploys `agent.py`.
- [`notebooks/03_agent_evaluation.py`](notebooks/03_agent_evaluation.py) — a real 10-question eval set (not the original's 1) across all 3 tools plus deliberate edge cases, using all 4 scorers (not 2). Evaluates the local `AGENT` object — doesn't touch the deployed model.
- [`notebooks/04_tracing_and_root_cause.py`](notebooks/04_tracing_and_root_cause.py) — deliberately breaks a tool on a local agent instance and walks through finding the root cause via its MLflow trace's span tree, without reading `agent.py`'s full call chain manually.
- [`notebooks/05_deployment_monitoring.py`](notebooks/05_deployment_monitoring.py) — endpoint status/config (read-only), optional live requests with cold-start latency measurement (disabled by default — costs compute), and pulling per-request traces from the endpoint's MLflow experiment.

## Architecture

```
User question
     │
     ▼
ToolCallingAgent (databricks-gpt-oss-120b)
     │
     ├── VectorSearchRetrieverTool → product_index          (semantic: "what product matches X?")
     ├── get_policy_details (UC function)                   (exact: "what's our return policy?")
     └── get_customer_service_history (UC function)          (exact: "what did customer X contact us about?")
```

The LLM decides which tool(s) to call per question — up to 10 tool-call iterations before giving up — rather than every question going through one retrieval path. See [`04_rag/README.md`](../04_rag/README.md) for why a single vector index isn't the right tool for all three question types.

Every Databricks resource the agent depends on (the LLM endpoint, the vector index, both UC functions) is declared explicitly at logging time (`deploy_agent.py`, the "Log the agent" step) so the serving endpoint receives scoped credentials for exactly those resources — not broad workspace access.

## One Change From the Original, Documented

`agent.py`'s `VectorSearchRetrieverTool` had a `# TODO: specify index description for better agent tool selection` left unfilled in the original. Filled in here with a real description ("Semantic search over the product catalog... not for exact policy or customer lookups") since an empty tool description makes it harder for the LLM to pick the right tool — but **this version has not been redeployed**, so the live endpoint is still running with the original blank description. Redeploying with this fix would require re-running `deploy_agent.py`'s log/register/deploy steps, which is a real change to production behavior and needs the same approval as any other deployment.

## Scenario Coverage

| Scenario | Status |
|---|---|
| 1. First Tool-Calling Agent (single UC function tool) | Not rebuilt as a separate step — the ported `agent.py` is the actual final multi-tool version, not a from-scratch progression. `03_agent_evaluation.py`'s rows 1–3 (each targeting exactly one tool) substitute for "does it decide when to call a tool vs. answer directly." |
| 2. Multi-Tool Composition | Done — 3 tools (vector search + 2 UC functions) — see the Genie gap below for a fourth tool that isn't wired in. |
| 3. Evaluation Before Trust | Done — `03_agent_evaluation.py`, 10 questions, 4 scorers. |
| 4. Tracing and Root Cause Analysis | Done — `04_tracing_and_root_cause.py`, against a local broken instance rather than the live endpoint. |
| 5. Deployment and Monitoring | Done — `05_deployment_monitoring.py`, endpoint status, live request latency, and MLflow trace pull. |

## Known Gaps (found while porting, not fixed silently)

1. **Empty `SYSTEM_PROMPT`.** The live agent has no system prompt at all — no explicit instruction to stay grounded in tool results rather than the LLM's general knowledge, unlike the grounding discipline enforced in `04_rag/notebooks/02_rag_retrieval_demo.py`'s standalone RAG demo. Worth adding before this agent is treated as production-ready; not changed here without your review since it changes deployed behavior.
2. **No Genie tool.** This agent uses vector search + two UC functions, with no Genie integration at all, even though `02_genie_space/` has a working Genie Space on the same data. Wiring Genie in as a fourth tool (e.g. via the Genie Conversation API, similar to `02_genie_space/notebooks/genie_api_conversation.py`, wrapped as a callable tool) would let the agent answer aggregate/analytical questions ("how many products in Electronics?") that none of its current 3 tools handle well — `product_index` retrieves individual products, not counts. Not added here since it's a real architecture and behavior change to a deployed agent, not a documentation gap.

## Running It

1. Confirm `04_rag/notebooks/01_build_agent_tools.py` has been run (both UC functions exist — they already do, confirmed live) and `03_vector_database`'s `product_index` is healthy (confirmed via `02_verify_product_vector_index.py`).
2. Import both files in `notebooks/` into the same Databricks workspace folder (`agent.py` must be importable as a local module from `deploy_agent.py`).
3. Run `deploy_agent.py` top to bottom to reproduce the log → evaluate → register → deploy flow. Since `sai_agent_model` version 1 already exists and is deployed, re-running this will register a new version and redeploy — a real change, not a no-op, so only do this intentionally.
4. Query the live endpoint from AI Playground, or `POST /serving-endpoints/agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model/invocations`.

## Evidence

See [`screenshots/`](screenshots/) for the capture checklist.
