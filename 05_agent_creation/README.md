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
- [`../lightweight_evidence_3_4_5.py`](../lightweight_evidence_3_4_5.py) — a minimal-footprint alternative covering the core evidence for this assignment (and 3/4) with zero `%pip install` cells, written for free-tier serverless quota constraints. Its Assignment 5 section calls the real deployed endpoint directly via REST — no `agent.py` import, no heavy SDK — and is what actually produced the screenshots in this folder, including the off-domain finding above.

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
| 1. First Tool-Calling Agent (single UC function tool) | Not rebuilt as a separate step — the ported `agent.py` is the actual final multi-tool version, not a from-scratch progression. Confirmed the agent decides when to call a tool vs. answer directly: it correctly routed a product question to `product_index`, a policy question to `get_policy_details`, and answered an off-domain question with neither (see the three `05-agent-*.png` screenshots). |
| 2. Multi-Tool Composition | Confirmed live — the MLflow Traces tab on the deployed endpoint shows real requests using different tools (`return policy` question, `waterproof jacket` question), each traced end to end (`predict` → `predict_stream` → `Completions`), 9/9 traces passing Relevance and Safety. See the Genie gap below for a fourth tool that isn't wired in. |
| 3. Evaluation Before Trust | Run — `03_agent_evaluation.py`, 10 questions, 4 scorers, real MLflow evaluation run logged. See "Evaluation Results" below for what actually happened, including a genuine scorer-applicability finding on 7 of 10 rows. |
| 4. Tracing and Root Cause Analysis | Run — `04_tracing_and_root_cause.py`. Found something more interesting than the notebook was designed to demonstrate; see "Root Cause: What Actually Happened" below. |
| 5. Deployment and Monitoring | Confirmed — endpoint status (`READY`), Metrics tab, and Traces tab all captured directly from the live endpoint. `05_deployment_monitoring.py`'s live-latency measurement (`10`) is the last item, ready to run (`RUN_LIVE_REQUESTS = True` already set). |

## Confirmed From the Live Endpoint

Captured directly from Catalog Explorer and the Serving endpoint's own UI — no notebook needed:

- **Registered model**: `uc_agentic_ai.agentic_ai_schema.sai_agent_model`, Version 1, owned by Sai T S, linked to the live serving endpoint.
- **Endpoint status**: `Ready`, `CPU (4 GB/worker)`, scaled to zero between requests, 100% traffic to `sai_agent_model_1`.
- **Metrics tab**: latency, request rate, error rate, and CPU usage graphs all live and populated.
- **Traces tab**: 9 real traces, **100% pass rate on both Relevance and Safety** assessments. Includes the off-domain "What is the capital of France?" call (441 tokens, answered directly, no tool call — this is the trace behind the `05-agent-off-domain.png` / empty-`SYSTEM_PROMPT` finding below) alongside genuine tool-calling traces: "What's our return policy?" (1,133–1,138 tokens) and "What's a good waterproof jacket for hiking?" (5,700 tokens) — both clearly involving a tool round-trip given the token counts. One trace was drilled into span-by-span (`predict` → `predict_stream` → `Completions`, model `gpt-oss-120b-080525`, 3 tools declared), confirming the full tool-calling loop structure end to end.

## Evaluation Results

`03_agent_evaluation.py` was run against the local `AGENT` object with all 4 scorers. Aggregate metrics: `relevance_to_query` 100%, `safety` 100%, `retrieval_groundedness` 100%, `retrieval_relevance` 93.3% — but those last two numbers are only meaningful for the rows they actually apply to, which is the real finding here:

**`RetrievalGroundedness`/`RetrievalRelevance` only scored cleanly on the 3 turns that used the vector search tool** (the waterproof-jacket question and its variants, headphones question) — Turn 1 passed 3/3 groundedness and 14/15 relevance checks, Turn 7 similarly. **The other 7 turns — every one that routed to a UC function instead (`get_policy_details`, `get_customer_service_history`) or correctly declined (off-domain, unsafe, no-match) — show `Error`, not `Pass` or `Fail`, on those two scorers**, because there's no retrieval span for a UC-function or no-tool-call turn to evaluate against. The evaluation harness's own log confirms this isn't a crash: *"Some scorer invocations failed during evaluation. Failure summary: 'retrieval_groundedness': 7/10 failed, 'retrieval_relevance': 7/10 failed."*

This is expected behavior for retrieval-specific scorers applied to a mixed-tool agent, not a bug in the eval set or the agent — but it does mean the 93.3%/100% aggregate numbers are effectively computed over an n of 3, not 10, and shouldn't be read as "the agent is 93% grounded across all its capabilities." A more complete evaluation would need separate scorers (or a custom one) for the UC-function turns — checking that the *answer* matches the *tool result*, not that a retrieval happened — which these 4 stock scorers don't cover. Worth adding before leaning on this eval set as a regression gate.

One real per-row result, not just an aggregate artifact: **Turn 2** ("I want a waterproof jacket — what's the return policy if it doesn't fit?", the multi-tool-composition test) passed Relevance and Groundedness but **failed Retrieval Relevance** — worth a closer look at that specific trace before trusting multi-tool answers generally.

## Root Cause: What Actually Happened

`04_tracing_and_root_cause.py` builds a second agent instance with its vector-search tool pointed at a nonexistent index, expecting the failure to surface as a failed `execute_tool` span partway through a trace. **That's not what happened, and the real result is more informative:**

The `VectorSearchRetrieverTool` constructor itself raised immediately — *"Tool construction itself failed: Unity Catalog entity `uc_agentic_ai.agentic_ai_schema.this_index_does_not_exist` does not exist."* This SDK version validates the index at construction time, before the agent is even built. Caught by the notebook's own `try/except`, so `broken_agent` ended up built with only 2 tools (the working UC functions) — the broken vector-search tool was never added at all, not added-then-failing.

With no vector-search tool available, asking *"What's a good waterproof jacket for hiking?"* **did not error.** The agent answered anyway — a long, well-formatted recommendation citing Patagonia, Marmot, Outdoor Research, and Arc'teryx, none of which exist in the actual product catalog. The trace confirms this: `status: OK`, 2,012 tokens, 7.92s latency, no failed span anywhere in `predict` → `predict_stream` → `Completions`. The agent silently fell back to the LLM's general knowledge instead of declining or reporting a missing capability.

This is the same root issue as the empty-`SYSTEM_PROMPT` finding above, showing up a second way: it's not just that off-domain questions get answered from outside knowledge — a **missing tool** produces the identical failure mode, an answer that looks correct but cites brands this catalog doesn't sell. A production version of this agent needs either a system-prompt instruction to decline when a needed tool is unavailable, or explicit tool-failure handling in `call_and_run_tools` that surfaces "I couldn't search the catalog right now" instead of letting the LLM improvise. Neither is fixed here, per the same policy as the `SYSTEM_PROMPT` gap — it's a real behavior change to a deployed agent.

## Known Gaps (found while porting, not fixed silently)

1. **Empty `SYSTEM_PROMPT` — confirmed, not just theoretical.** The live agent has no system prompt at all. Tested directly: asked the real deployed endpoint *"What is the capital of France?"* — it answered **"The capital of France is Paris"** instead of declining. The equivalent question run through `04_rag/notebooks/02_rag_retrieval_demo.py`'s standalone RAG demo (which *does* have an explicit grounding system prompt) correctly declined to answer from outside knowledge. Same underlying model, same kind of off-domain question — the only difference is the system prompt, and it visibly changes whether the agent stays grounded (see `screenshots/05-agent-off-domain.png` vs. `04_rag/screenshots/04-grounding-refusal-check.png`). Worth adding before this agent is treated as production-ready; not changed here without your review since it changes deployed behavior.
2. **No Genie tool.** This agent uses vector search + two UC functions, with no Genie integration at all, even though `02_genie_space/` has a working Genie Space on the same data. Wiring Genie in as a fourth tool (e.g. via the Genie Conversation API, similar to `02_genie_space/notebooks/genie_api_conversation.py`, wrapped as a callable tool) would let the agent answer aggregate/analytical questions ("how many products in Electronics?") that none of its current 3 tools handle well — `product_index` retrieves individual products, not counts. Not added here since it's a real architecture and behavior change to a deployed agent, not a documentation gap.

## Running It

Both UC functions (`04_rag/notebooks/01_build_agent_tools.py`) and the vector index (`03_vector_database`'s `product_index`) are confirmed live and healthy — this agent already depends on working infrastructure.

`deploy_agent.py` is **not** meant to be re-run casually: `sai_agent_model` version 1 already exists and is deployed, so re-running the log/register/deploy flow would register a new version and redeploy — a real production change, only do this intentionally.

What's left to capture:
1. `05_deployment_monitoring.py` (already set to `RUN_LIVE_REQUESTS = True`) — for `10-live-request-latency.png`.

That's the only item remaining. `04_tracing_and_root_cause.py` has been run — see "Root Cause: What Actually Happened" above.

## Evidence

See [`screenshots/`](screenshots/) for the capture checklist.
