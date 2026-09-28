# Agent Creation Evidence Screenshots

Save genuine screenshots from the Databricks workspace session in this folder. Use the filenames below so the evidence is easy to review in workflow order.

| Filename | Evidence |
|---|---|
| Filename | Evidence | Status |
|---|---|---|
| `01-mlflow-run.png` | The MLflow run that logged the agent (`deploy_agent.py`'s "Log the agent" step) — run details, logged resources visible. | Needed |
| `02-evaluation-results.png` | `03_agent_evaluation.py`'s run in the MLflow UI — all 10 rows, all 4 scorers (`RelevanceToQuery`, `Safety`, `RetrievalRelevance`, `RetrievalGroundedness`). | Needed |
| `03-registered-model.png` | `uc_agentic_ai.agentic_ai_schema.sai_agent_model` version 1 in Catalog Explorer. | Needed |
| `04-serving-endpoint.png` | The Serving endpoints list — `agents_uc_agentic_...` showing State `Ready`, Task `Agent (Responses)`. | Done |
| `05-playground-tool-routing.png` | A real conversation against the deployed agent (via its chat app) showing a tool call in progress: `uc_agentic_ai__agentic_ai_schema__product_index` called with `{"query": "list all products"}`, status `Completed`, real product data returned. | Done |
| `05-agent-product-question.png` | `lightweight_evidence_3_4_5.py` §5.1 — the deployed agent asked a product question, correctly calling `product_index` and recommending the AlpinePro Waterproof Jacket. | Done |
| `05-agent-policy-question.png` | §5.2 — the same agent asked a policy question, correctly calling `get_policy_details` instead of the vector index, and returning the real Return Policy. | Done |
| `05-agent-off-domain.png` | §5.3 — the same agent asked an off-domain question. **Answered "Paris" instead of declining** — the real, observed effect of the empty `SYSTEM_PROMPT` gap documented in the main README. | Done |
| `06-mlflow-trace.png` | An MLflow trace for one request, showing the full tool-calling loop (LLM call → tool call → LLM call → final answer). | Needed |
| `07-broken-eval-rows.png` | The 2-3 eval rows from `03_agent_evaluation.py` most likely to fail (synonym policy question, partial-name lookup, no-matching-policy case) with their actual scores — whatever they turn out to be, not assumed. | Needed |
| `08-root-cause-trace.png` | `04_tracing_and_root_cause.py`'s trace in the MLflow UI, with the failed `execute_tool` span expanded showing the underlying error. | Needed |
| `09-endpoint-metrics.png` | The serving endpoint's **Metrics** tab in the workspace UI — request volume/latency/error rate. | Needed |
| `10-live-request-latency.png` | `05_deployment_monitoring.py` §2 output — cold-start vs. warm request latencies, if run. | Needed |

Only mark evidence complete when the corresponding screenshot exists and shows the actual session result. Do not create placeholder images or invent evaluation scores.

Notes:
- `04` and `05-playground-tool-routing` were captured against this same live `sai_agent_model` endpoint earlier in this project's work, rather than from `deploy_agent.py`/AI Playground directly in this session — still genuine screenshots of the real deployed agent actually calling its real tool, just captured via its chat app instead of Playground.
- `05-agent-*` (product/policy/off-domain) come from `lightweight_evidence_3_4_5.py`, run against the real deployed endpoint via plain REST calls — no notebook needed for `01`, `03`, `06` (those are pure Catalog Explorer / MLflow UI browsing per that notebook's own "zero-compute evidence" section).
