# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Tracing and Root-Cause Analysis
# MAGIC
# MAGIC Deliberately breaks one tool (a nonexistent vector index name) and uses
# MAGIC MLflow Tracing to find exactly which tool call failed and why — without
# MAGIC reading through `agent.py`'s full tool-calling loop line by line.
# MAGIC
# MAGIC **Breaks a local copy only.** This builds a second `ToolCallingAgent`
# MAGIC instance in this notebook with one tool intentionally misconfigured — it never
# MAGIC touches the deployed `sai_agent_model` endpoint or any UC asset. Breaking the
# MAGIC actual production endpoint to test tracing would be a real outage for a
# MAGIC debugging exercise; that's not worth it when the same lesson is fully visible
# MAGIC on a local instance.

# COMMAND ----------

# MAGIC %pip install -U -qqqq backoff databricks-openai uv databricks-agents mlflow-skinny[databricks]
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import mlflow

mlflow.openai.autolog()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Build a deliberately broken agent
# MAGIC
# MAGIC Reuses `agent.py`'s `ToolCallingAgent` class and the two working UC function
# MAGIC tools, but points the vector search tool at an index name that doesn't exist.

# COMMAND ----------

from agent import ToolCallingAgent, TOOL_INFOS, LLM_ENDPOINT_NAME, create_tool_info
from databricks_openai import VectorSearchRetrieverTool

broken_tools = [t for t in TOOL_INFOS if "product_index" not in t.name and "vector" not in t.name.lower()]

try:
    broken_vs_tool = VectorSearchRetrieverTool(
        index_name="uc_agentic_ai.agentic_ai_schema.this_index_does_not_exist",
        tool_description="Semantic search over the product catalog.",
    )
    broken_tools.append(create_tool_info(broken_vs_tool.tool, broken_vs_tool.execute))
except Exception as e:
    print(f"Tool construction itself failed (some SDK versions validate the index at construction time): {e}")

broken_agent = ToolCallingAgent(llm_endpoint=LLM_ENDPOINT_NAME, tools=broken_tools)
print(f"Broken agent built with {len(broken_tools)} tools: {[t.name for t in broken_tools]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Trigger the failure
# MAGIC
# MAGIC Asks a question that should route to the (broken) vector search tool. With
# MAGIC `mlflow.trace` decorating `execute_tool` in `agent.py`, this produces a trace
# MAGIC with a clearly-failed span rather than a bare stack trace in a log.

# COMMAND ----------

with mlflow.start_span(name="root_cause_investigation") as root_span:
    try:
        result = broken_agent.predict(
            {"input": [{"role": "user", "content": "What's a good waterproof jacket for hiking?"}], "custom_inputs": {"session_id": "root-cause-demo"}}
        )
        print("Unexpected: no error raised.")
        print(result)
    except Exception as e:
        print(f"Failed as expected: {type(e).__name__}: {e}")
        root_span.set_status("ERROR", str(e))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Find the root cause from the trace, not the stack trace
# MAGIC
# MAGIC Open the MLflow experiment (the one this notebook's run is logged to — check
# MAGIC the run link printed above, or the workspace's Experiments page) and find the
# MAGIC trace for the request above. Expand its spans:
# MAGIC
# MAGIC 1. Top-level span: the `predict` call — status `ERROR`.
# MAGIC 2. Child span: `execute_tool` (the `@mlflow.trace(span_type=SpanType.TOOL)`
# MAGIC    decorator on `agent.py`'s `ToolCallingAgent.execute_tool`) — this is the
# MAGIC    one that actually failed, and its name tells you which tool without
# MAGIC    needing to guess from the exception message alone.
# MAGIC 3. The span's exception details show the underlying Vector Search API error
# MAGIC    (index not found) — the real root cause, two layers below where the
# MAGIC    exception first surfaced to the notebook.
# MAGIC
# MAGIC That's the point of tracing over log-reading: determining the root cause
# MAGIC without reviewing the entire codebase — the trace's span tree directly points
# MAGIC at `execute_tool` → the vector search tool, without needing to trace execution
# MAGIC through `call_and_run_tools`, `handle_tool_call`, and `call_llm` manually.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC - If §1's tool construction itself raised (rather than failing later at query
# MAGIC   time), that's actually a *better* failure mode — an invalid index name
# MAGIC   caught at agent-build time, before ever reaching a user, rather than at
# MAGIC   first query time in production. Worth noting which behavior your SDK
# MAGIC   version actually has.
# MAGIC - The live `sai_agent_model` endpoint has `ENABLE_MLFLOW_TRACING=true` and a
# MAGIC   fixed `MLFLOW_EXPERIMENT_ID` (confirmed via the serving-endpoints API when
# MAGIC   this repo's `05_agent_creation/README.md` was written) — so this same
# MAGIC   root-cause workflow applies directly to real production failures, not just
# MAGIC   this local demo.