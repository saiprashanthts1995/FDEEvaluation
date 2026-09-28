# Agent Creation Evidence Screenshots

Save genuine screenshots from the Databricks workspace session in this folder. Use the filenames below so the evidence is easy to review in workflow order.

| Filename | Evidence |
|---|---|
| `01-mlflow-run.png` | The MLflow run that logged the agent (`deploy_agent.py`'s "Log the agent" step) — run details, logged resources visible. |
| `02-evaluation-results.png` | `03_agent_evaluation.py`'s run in the MLflow UI — all 10 rows, all 4 scorers (`RelevanceToQuery`, `Safety`, `RetrievalRelevance`, `RetrievalGroundedness`). |
| `03-registered-model.png` | `uc_agentic_ai.agentic_ai_schema.sai_agent_model` version 1 in Catalog Explorer. |
| `04-serving-endpoint.png` | The `agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model` serving endpoint page showing status `READY`. |
| `05-playground-tool-routing.png` | A conversation in AI Playground (or the endpoint's query UI) showing the agent picking different tools for different questions — e.g. a product question triggering the vector search tool, and a policy question triggering `get_policy_details`, with the tool call visible in the trace. |
| `06-mlflow-trace.png` | An MLflow trace for one request, showing the full tool-calling loop (LLM call → tool call → LLM call → final answer). |
| `07-broken-eval-rows.png` | The 2-3 eval rows from `03_agent_evaluation.py` most likely to fail (synonym policy question, partial-name lookup, no-matching-policy case) with their actual scores — whatever they turn out to be, not assumed. |
| `08-root-cause-trace.png` | `04_tracing_and_root_cause.py`'s trace in the MLflow UI, with the failed `execute_tool` span expanded showing the underlying error. |
| `09-endpoint-metrics.png` | The serving endpoint's **Metrics** tab in the workspace UI — request volume/latency/error rate. |
| `10-live-request-latency.png` | `05_deployment_monitoring.py` §2 output — cold-start vs. warm request latencies, if run. |

Only mark evidence complete when the corresponding screenshot exists and shows the actual session result. Do not create placeholder images or invent evaluation scores.
