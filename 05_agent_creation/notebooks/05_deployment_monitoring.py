# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# dependencies = [
#   "databricks-sdk[openai]",
# ]
# ///
# MAGIC %md
# MAGIC # Deployment Status and Monitoring
# MAGIC
# MAGIC Sends live requests to the deployed `sai_agent_model` endpoint and pulls back
# MAGIC what production monitoring actually looks like for this agent: endpoint
# MAGIC status/config, per-request MLflow traces (latency, tool calls, errors), and
# MAGIC where to find the live dashboards in the workspace UI.
# MAGIC
# MAGIC **Cost/latency note:** the endpoint is `scale_to_zero_enabled=True`
# MAGIC (confirmed via the serving-endpoints API). Section 2's live requests will
# MAGIC trigger a cold start (extra latency on the first request, real compute cost
# MAGIC while it's warm) — `RUN_LIVE_REQUESTS = True` below, so running this
# MAGIC notebook top to bottom sends 3 real requests. Set it back to `False` first
# MAGIC if you just want Sections 1/3/4 (all read-only).

# COMMAND ----------

import mlflow

catalog = "uc_agentic_ai"
schema = "agentic_ai_schema"
endpoint_name = "agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model"
mlflow_experiment_id = "2179939438147551"  # confirmed live via GET /api/2.0/serving-endpoints/{endpoint_name}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Endpoint status and config (read-only)

# COMMAND ----------

# MAGIC %pip install databricks-sdk[openai]

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
endpoint = w.serving_endpoints.get(endpoint_name)

print(f"Endpoint:  {endpoint.name}")
print(f"Ready:     {endpoint.state.ready}")
print(f"Config update: {endpoint.state.config_update}")
served = endpoint.config.served_entities[0]
print(f"Model:     {served.entity_name} v{served.entity_version}")
print(f"Scale to zero: {served.scale_to_zero_enabled}")
print(f"Deployment state: {served.state.deployment}")
print(f"Deployment message: {served.state.deployment_state_message}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Send live requests (enabled — wakes a scaled-to-zero endpoint)

# COMMAND ----------

RUN_LIVE_REQUESTS = True  # sends real requests to the live endpoint — incurs cold-start latency and real compute cost

if RUN_LIVE_REQUESTS:
    import time

    test_questions = [
        "What's a good waterproof jacket for hiking?",
        "What's our return policy?",
        "What's the capital of France?",  # should decline — same groundedness check as 04_rag/
    ]

    client = w.serving_endpoints.get_open_ai_client()
    latencies = []

    for q in test_questions:
        start = time.time()
        response = client.responses.create(
            model=endpoint_name,
            input=[{"role": "user", "content": q}],
            extra_body={"custom_inputs": {"session_id": "monitoring-demo"}},
        )
        elapsed = time.time() - start
        latencies.append(elapsed)
        print(f"[{elapsed:.2f}s] Q: {q}")
        print(f"  A: {str(response.output)[:200]}...")

    print(f"\nLatencies: {[f'{l:.2f}s' for l in latencies]}")
    print(f"First request (cold start likely included): {latencies[0]:.2f}s")
    if len(latencies) > 1:
        print(f"Subsequent requests (warm): {[f'{l:.2f}s' for l in latencies[1:]]}")
else:
    print("RUN_LIVE_REQUESTS is False. Flip to True to send real requests and measure cold-start vs warm latency.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Pull traces from the endpoint's MLflow experiment
# MAGIC
# MAGIC Every request to this endpoint (from Section 2 above, from AI Playground, or
# MAGIC from the Databricks App in `06_databricks_app/`) logs a trace to this
# MAGIC experiment, since `ENABLE_MLFLOW_TRACING=true` is set in the endpoint's
# MAGIC environment vars. This is read-only regardless of whether Section 2 ran.

# COMMAND ----------

traces = mlflow.search_traces(experiment_ids=[mlflow_experiment_id], max_results=10, order_by=["timestamp_ms DESC"])

if len(traces) == 0:
    print("No traces yet — run Section 2, or query the live endpoint from AI Playground first.")
else:
    print(f"Most recent {len(traces)} traces:\n")
    for _, trace in traces.iterrows():
        print(f"  {trace['timestamp_ms']}  status={trace['status']}  duration_ms={trace.get('execution_time_ms', 'n/a')}")

# COMMAND ----------



# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Where to watch this in the UI, ongoing
# MAGIC
# MAGIC - **Serving endpoint page** (`Serving` in the left nav → `agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model`) —
# MAGIC   the **Metrics** tab shows request volume, latency percentiles, and error
# MAGIC   rate over time; the **Logs** tab shows per-request logs including cold
# MAGIC   starts.
# MAGIC - **MLflow Experiment** (`2179939438147551`, or via the endpoint's own
# MAGIC   "View traces" link) — every request's full trace: which tools were called,
# MAGIC   in what order, with what latency each, and the final LLM response. This is
# MAGIC   the same view Section 3 above pulls programmatically.
# MAGIC - **AI Playground** — the fastest way to send an ad-hoc test request and see
# MAGIC   its trace immediately, without writing code.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC - Section 1 and 3 are fully read-only and safe to run any time. Section 2 is
# MAGIC   the only part that costs money or wakes the endpoint — enabled here since
# MAGIC   this run is specifically to capture live-latency evidence.
# MAGIC - The endpoint's config has no AI Gateway block (rate limits, guardrails, usage
# MAGIC   tracking) attached — confirmed from the raw `GET /api/2.0/serving-endpoints/...`
# MAGIC   response, which has no `ai_gateway` key. Whether any separate alerting is
# MAGIC   configured (e.g. via Lakehouse Monitoring) wasn't checked by this notebook —
# MAGIC   verify directly in the workspace before assuming either way. For a real
# MAGIC   production deployment, a latency or error-rate alert would be a reasonable
# MAGIC   next step.