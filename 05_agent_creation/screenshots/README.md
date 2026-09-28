# Agent Creation Evidence Screenshots

Genuine screenshots from the Databricks workspace, 11 of 12 checklist items plus 3 bonus captures.

| Filename | Evidence | Status |
|---|---|---|
| `01-mlflow-run.png` | The MLflow run that logged `03_agent_evaluation.py`'s evaluation — eval dataset (10 questions) defined, 4 scorers configured, run logged to the experiment. | Done |
| `02-evaluation-results.png` | Evaluation console output — 10/10 evaluated, aggregate metrics printed (`relevance_to_query` 100%, `safety` 100%, `retrieval_groundedness` 100%, `retrieval_relevance` 93.3%), and the harness's own warning that `retrieval_groundedness`/`retrieval_relevance` failed to apply to 7 of 10 rows (see main README's "Evaluation Results" for why). | Done |
| `03-registered-model.png` | `uc_agentic_ai.agentic_ai_schema.sai_agent_model` Version 1 in Catalog Explorer, owned by Sai T S. | Done |
| `04-serving-endpoint.png` | The `agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model` endpoint overview — `Ready`, `CPU (4 GB/worker)`, scaled to zero, 100% traffic. | Done |
| `05-playground-tool-routing.png` | A real conversation against the deployed agent showing a tool call in progress: `uc_agentic_ai__agentic_ai_schema__product_index` called with `{"query": "list all products"}`, status `Completed`, real product data returned. | Done |
| `05-agent-product-question.png` | The deployed agent asked a product question, correctly calling `product_index` and recommending the AlpinePro Waterproof Jacket. | Done |
| `05-agent-policy-question.png` | The same agent asked a policy question, correctly calling `get_policy_details` and returning the real Return Policy. | Done |
| `05-agent-off-domain.png` | The same agent asked an off-domain question — answered "Paris" instead of declining, the real observed effect of the missing `SYSTEM_PROMPT` (see main README). | Done |
| `06-mlflow-trace.png` | The endpoint's Traces tab — 9 real traces, 100% pass on Relevance and Safety, including tool-calling traces (return policy, waterproof jacket) alongside the off-domain one. | Done |
| `07-broken-eval-rows.png` | The full evaluation-run detail page — per-turn breakdown for all 10 rows, showing Turn 2 (multi-tool composition test) failing `Retrieval relevance`, and Turns 3–6/8–10 showing `Error` on the two retrieval-specific scorers since those turns used UC functions, not vector search. | Done |
| `08-root-cause-trace.png` | The `VectorSearchRetrieverTool` construction failing immediately with a clear Unity Catalog error (index doesn't exist) — the root cause was found before the agent even ran, not by digging through a failed trace span. See main README's "Root Cause: What Actually Happened" for the more interesting follow-on finding (the agent then answered from ungrounded general knowledge instead of erroring). | Done |
| `09-endpoint-metrics.png` | The serving endpoint's Metrics tab — latency, request rate, error rate, CPU usage, all live. | Done |
| `10-live-request-latency.png` | `05_deployment_monitoring.py` §2 output — cold-start vs. warm request latencies. | Needed — run `05_deployment_monitoring.py` (already set to `RUN_LIVE_REQUESTS = True`, ready to go) |

Only mark evidence complete when the corresponding screenshot exists and shows the actual session result. Do not create placeholder images or invent evaluation scores.

`03`, `04`, `06`, `09` and the three `05-agent-*` files come from live UI browsing and REST calls (via `../../lightweight_evidence_3_4_5.py`) against the real deployed `sai_agent_model` endpoint. `01`, `02`, `07` come from an actual run of `03_agent_evaluation.py`. `08` comes from an actual run of `04_tracing_and_root_cause.py`. `10` is the only item left, from `05_deployment_monitoring.py`.
