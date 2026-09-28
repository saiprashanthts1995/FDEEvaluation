# Agent Creation Evidence Screenshots

Genuine screenshots from the Databricks workspace. All 12 checklist items, plus 3 bonus captures.

| Filename | Evidence |
|---|---|
| `01-mlflow-run.png` | The MLflow run that logged `03_agent_evaluation.py`'s evaluation — eval dataset (10 questions) defined, 4 scorers configured, run logged to the experiment. |
| `02-evaluation-results.png` | Evaluation console output — 10/10 evaluated, aggregate metrics printed (`relevance_to_query` 100%, `safety` 100%, `retrieval_groundedness` 100%, `retrieval_relevance` 93.3%), and the harness's own warning that `retrieval_groundedness`/`retrieval_relevance` failed to apply to 7 of 10 rows (see main README's "Evaluation Results" for why). |
| `03-registered-model.png` | `uc_agentic_ai.agentic_ai_schema.sai_agent_model` Version 1 in Catalog Explorer, owned by Sai T S. |
| `04-serving-endpoint.png` | The `agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model` endpoint overview — `Ready`, `CPU (4 GB/worker)`, scaled to zero, 100% traffic. |
| `05-playground-tool-routing.png` | A real conversation against the deployed agent showing a tool call in progress: `uc_agentic_ai__agentic_ai_schema__product_index` called with `{"query": "list all products"}`, status `Completed`, real product data returned. |
| `05-agent-product-question.png` | The deployed agent asked a product question, correctly calling `product_index` and recommending the AlpinePro Waterproof Jacket. |
| `05-agent-policy-question.png` | The same agent asked a policy question, correctly calling `get_policy_details` and returning the real Return Policy. |
| `05-agent-off-domain.png` | The same agent asked an off-domain question — answered "Paris" instead of declining, the real observed effect of the missing `SYSTEM_PROMPT` (see main README). |
| `06-mlflow-trace.png` | The endpoint's Traces tab — 15 real traces across multiple sessions, 100% pass on Relevance and Safety, including tool-calling traces (return policy, waterproof jacket) alongside off-domain ones. |
| `07-broken-eval-rows.png` | The full evaluation-run detail page — per-turn breakdown for all 10 rows, showing Turn 2 (multi-tool composition test) failing `Retrieval relevance`, and Turns 3–6/8–10 showing `Error` on the two retrieval-specific scorers since those turns used UC functions, not vector search. |
| `08-root-cause-trace.png` | The `VectorSearchRetrieverTool` construction failing immediately with a clear Unity Catalog error (index doesn't exist) — the root cause was found before the agent even ran, not by digging through a failed trace span. See main README's "Root Cause: What Actually Happened" for the more interesting follow-on finding (the agent then answered from ungrounded general knowledge instead of erroring). |
| `09-endpoint-metrics.png` | The serving endpoint's Metrics tab — latency, request rate, error rate, CPU usage, all live. |
| `10-live-request-latency.png` | 3 real requests sent to the live endpoint with **zero cold-start retries needed** — 4.53s (cold), 4.30s and 1.17s (warm) — plus the actual tool-call responses for each question. |

`03`, `04`, `06`, `09` and the three `05-agent-*` files come from live UI browsing and REST calls against the real deployed `sai_agent_model` endpoint. `01`/`02`/`07` come from `03_agent_evaluation.py`. `08` comes from `04_tracing_and_root_cause.py`. `10` comes from `05_deployment_monitoring.py`.
