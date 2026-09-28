# Agent Creation Evidence Screenshots

Genuine screenshots from the Databricks workspace, 8 of 10 checklist items plus 3 bonus captures.

| Filename | Evidence | Status |
|---|---|---|
| `01-mlflow-run.png` | The MLflow run that logged the agent (`deploy_agent.py`'s "Log the agent" step) — run details, logged resources visible. | Needed — run `03_agent_evaluation.py` |
| `02-evaluation-results.png` | `03_agent_evaluation.py`'s run in the MLflow UI — all 10 rows, all 4 scorers (`RelevanceToQuery`, `Safety`, `RetrievalRelevance`, `RetrievalGroundedness`). | Needed — run `03_agent_evaluation.py` |
| `03-registered-model.png` | `uc_agentic_ai.agentic_ai_schema.sai_agent_model` Version 1 in Catalog Explorer, owned by Sai T S. | Done |
| `04-serving-endpoint.png` | The `agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model` endpoint overview — `Ready`, `CPU (4 GB/worker)`, scaled to zero, 100% traffic. | Done |
| `05-playground-tool-routing.png` | A real conversation against the deployed agent showing a tool call in progress: `uc_agentic_ai__agentic_ai_schema__product_index` called with `{"query": "list all products"}`, status `Completed`, real product data returned. | Done |
| `05-agent-product-question.png` | The deployed agent asked a product question, correctly calling `product_index` and recommending the AlpinePro Waterproof Jacket. | Done |
| `05-agent-policy-question.png` | The same agent asked a policy question, correctly calling `get_policy_details` and returning the real Return Policy. | Done |
| `05-agent-off-domain.png` | The same agent asked an off-domain question — answered "Paris" instead of declining, the real observed effect of the missing `SYSTEM_PROMPT` (see main README). | Done |
| `06-mlflow-trace.png` | The endpoint's Traces tab — 9 real traces, 100% pass on Relevance and Safety, including tool-calling traces (return policy, waterproof jacket) alongside the off-domain one. | Done |
| `07-broken-eval-rows.png` | The 2-3 eval rows from `03_agent_evaluation.py` most likely to fail (synonym policy question, partial-name lookup, no-matching-policy case) with their actual scores. | Needed — run `03_agent_evaluation.py` |
| `08-root-cause-trace.png` | `04_tracing_and_root_cause.py`'s trace in the MLflow UI, with the failed `execute_tool` span expanded showing the underlying error. | Needed — run `04_tracing_and_root_cause.py` |
| `09-endpoint-metrics.png` | The serving endpoint's Metrics tab — latency, request rate, error rate, CPU usage, all live. | Done |
| `10-live-request-latency.png` | `05_deployment_monitoring.py` §2 output — cold-start vs. warm request latencies. | Needed — run `05_deployment_monitoring.py` with `RUN_LIVE_REQUESTS = True` |

Only mark evidence complete when the corresponding screenshot exists and shows the actual session result. Do not create placeholder images or invent evaluation scores.

`03`, `04`, `06`, `09` and the three `05-agent-*` files come from live UI browsing and REST calls (via `../../lightweight_evidence_3_4_5.py`) against the real deployed `sai_agent_model` endpoint — no notebook install needed. `01`, `02`, `07`, `08`, `10` need the three heavier notebooks in `notebooks/`, unblocked now that the missing second `restartPython()` cell (needed before `from agent import AGENT` on Serverless) has been fixed in all three.
