# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Lightweight Evidence: Assignments 3, 4, 5
# MAGIC
# MAGIC A single, minimal-footprint notebook covering the core evidence for Vector
# MAGIC Search (`03_vector_database/`), RAG (`04_rag/`), and the deployed Agent
# MAGIC (`05_agent_creation/`) — written specifically for a free-tier workspace with
# MAGIC very limited serverless compute quota.
# MAGIC
# MAGIC **Zero `%pip install` cells.** Every heavier notebook elsewhere in this repo
# MAGIC uses `databricks-vectorsearch`, `databricks-openai`, `mlflow-skinny[databricks]`,
# MAGIC etc. — real packages, but installing them burns quota and time, which is
# MAGIC exactly what's failing right now. This notebook instead uses only:
# MAGIC - `spark.sql(...)` — already available, no install.
# MAGIC - `requests` — already available, no install. Used to call the Vector Search
# MAGIC   Query REST API, the chat LLM's REST API, and the deployed agent's REST API
# MAGIC   directly, instead of going through `VectorSearchClient` / `agent.py` /
# MAGIC   `databricks_openai`, which pull in the heavy dependency chains that were
# MAGIC   timing out.
# MAGIC
# MAGIC Each cell runs in a few seconds (except the agent cells, which wake a
# MAGIC scaled-to-zero endpoint on first call — expect ~1-2 minutes for that one call
# MAGIC only, then fast after).
# MAGIC
# MAGIC **What this intentionally skips** (heavier scenarios from the full notebooks,
# MAGIC not required to prove the core capability, safe to skip under quota pressure):
# MAGIC freshness test, Direct Vector Access index comparison, chunking-tradeoffs
# MAGIC token analysis, the full 10-question scored evaluation, and local
# MAGIC break-a-tool tracing. Each assignment's own README marks these as skipped for
# MAGIC this reason, not silently dropped.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — no installs, just get a token for REST calls

# COMMAND ----------

import requests

ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
DATABRICKS_HOST = ctx.apiUrl().get()
DATABRICKS_TOKEN = ctx.apiToken().get()
HEADERS = {"Authorization": f"Bearer {DATABRICKS_TOKEN}", "Content-Type": "application/json"}

catalog = "uc_agentic_ai"
schema = "agentic_ai_schema"
index_name = f"{catalog}.{schema}.product_index"
chat_endpoint = "databricks-gpt-oss-120b"
agent_endpoint = "agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model"

print("Ready — no packages installed, using spark.sql + requests only.")

# COMMAND ----------

# MAGIC %md
# MAGIC # Assignment 3 — Vector Search

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.1 Source table health (SQL only — screenshot as `04-source-health-check.png`)

# COMMAND ----------

display(spark.sql(f"""
    SELECT
        COUNT(*) AS row_count,
        COUNT(DISTINCT product_category) AS distinct_categories,
        SUM(CASE WHEN product_combined IS NULL OR trim(product_combined) = '' THEN 1 ELSE 0 END) AS empty_combined_text
    FROM {catalog}.{schema}.product_master
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.2 Index status (REST, no SDK — screenshot as `03-index-detail.png`)

# COMMAND ----------

resp = requests.get(
    f"{DATABRICKS_HOST}/api/2.0/vector-search/indexes/{index_name}",
    headers=HEADERS,
)
info = resp.json()
print(f"Index: {info['name']}")
print(f"State: {info['status']['detailed_state']}")
print(f"Indexed rows: {info['status']['indexed_row_count']}")
print(f"Source table: {info['delta_sync_index_spec']['source_table']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.3 Retrieval sanity check (REST — screenshot as `06-retrieval-sanity-check.png`)

# COMMAND ----------

def vector_search(query_text, num_results=5, filters=None, columns=None):
    body = {
        "columns": columns or ["product_name", "product_category", "product_desc"],
        "query_text": query_text,
        "num_results": num_results,
    }
    if filters:
        body["filters_json"] = str(filters).replace("'", '"')
    resp = requests.post(
        f"{DATABRICKS_HOST}/api/2.0/vector-search/indexes/{index_name}/query",
        headers=HEADERS,
        json=body,
    )
    return resp.json()["result"]["data_array"]


for name, category, desc, score in vector_search("wireless noise-cancelling headphones", num_results=3):
    print(f"  [{score:.3f}] {name}  ({category})")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.4 Filtered search (REST — screenshot as `08-filtered-search.png`)

# COMMAND ----------

unfiltered = vector_search("wireless headphones", num_results=5, columns=["product_name", "product_category"])
print("Unfiltered:")
for name, category, score in unfiltered:
    print(f"  [{score:.3f}] {name}  ({category})")

filtered = vector_search(
    "wireless headphones", num_results=5, columns=["product_name", "product_category"],
    filters={"product_category": "Electronics"},
)
print("\nFiltered to Electronics:")
for name, category, score in filtered:
    print(f"  [{score:.3f}] {name}  ({category})")
    assert category == "Electronics", f"Filter leaked: {name} ({category})"
print("\nFilter check passed.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.5 `top_k` tuning (REST — screenshot as `10-query-tuning.png`)

# COMMAND ----------

for k in (3, 15):
    hits = vector_search("comfortable running shoes", num_results=k, columns=["product_name", "product_category"])
    scores = [row[-1] for row in hits]
    print(f"top_k={k}: {len(hits)} results, score range {min(scores):.3f}-{max(scores):.3f}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Assignment 4 — RAG

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.1 UC function tools (SQL only — screenshot as `01-uc-functions.png`)

# COMMAND ----------

display(spark.sql(f"SELECT * FROM {catalog}.{schema}.get_policy_details('return')"))
display(spark.sql(f"SELECT * FROM {catalog}.{schema}.get_customer_service_history('Robert Butler')"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.2 Retrieve + grounded generation (REST — screenshot as `03-grounded-answer.png`)

# COMMAND ----------

def extract_text(content):
    if isinstance(content, str):
        return content
    for part in content:
        if part.get("type") == "text":
            return part["text"]
    return str(content)


def chat(system_prompt, user_content, max_tokens=400):
    resp = requests.post(
        f"{DATABRICKS_HOST}/serving-endpoints/{chat_endpoint}/invocations",
        headers=HEADERS,
        json={
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": max_tokens,
        },
    )
    return extract_text(resp.json()["choices"][0]["message"]["content"])


SYSTEM_PROMPT = (
    "You are a product catalog assistant. Answer ONLY from the product context "
    "provided below. Cite the product name for every claim. If the context "
    "doesn't support an answer, say so explicitly instead of guessing."
)

query = "What's a good product for someone who hikes in cold weather?"
hits = vector_search(query, num_results=4)
context_block = "\n".join(f"- {name} ({cat}): {desc[:300]}" for name, cat, desc, score in hits)

answer = chat(SYSTEM_PROMPT, f"Product context:\n{context_block}\n\nQuestion: {query}")
print(answer)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.3 Grounding refusal check (REST — screenshot as `04-grounding-refusal-check.png`)

# COMMAND ----------

off_domain_answer = chat(SYSTEM_PROMPT, f"Product context:\n{context_block}\n\nQuestion: What is the capital of France?")
print(off_domain_answer)
assert "Paris" not in off_domain_answer, "Model answered from outside knowledge instead of declining."
print("\nGrounding check passed — model did not answer from outside knowledge.")

# COMMAND ----------

# MAGIC %md
# MAGIC # Assignment 5 — Deployed Agent
# MAGIC
# MAGIC First call wakes the scaled-to-zero endpoint (~1-2 min). Subsequent calls are fast.

# COMMAND ----------

def ask_agent(question, session_id="lightweight-evidence-session"):
    resp = requests.post(
        f"{DATABRICKS_HOST}/serving-endpoints/{agent_endpoint}/invocations",
        headers=HEADERS,
        json={
            "input": [{"role": "user", "content": question}],
            "custom_inputs": {"session_id": session_id},
        },
        timeout=180,
    )
    return resp.json()

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5.1 Product question — should trigger the vector search tool (screenshot as `05-agent-product-question.png`)

# COMMAND ----------

def print_agent_result(result):
    """Best-effort parse of the ResponsesAgent output format agent.py produces.
    Falls back to printing the raw JSON if the shape doesn't match, so this
    never silently shows nothing."""
    output = result.get("output")
    if not output:
        print("(Raw response — parsing found no 'output' field:)")
        print(result)
        return
    printed_anything = False
    for item in output:
        item_type = item.get("type")
        if item_type == "function_call":
            print(f"[TOOL CALL] {item.get('name')}  args={item.get('arguments')}")
            printed_anything = True
        elif item_type == "message":
            for c in item.get("content", []):
                if c.get("type") in ("output_text", "text"):
                    print(f"[ANSWER] {c.get('text')}")
                    printed_anything = True
    if not printed_anything:
        print("(Parsing matched no known item type — raw output:)")
        print(output)


result = ask_agent("What's a good waterproof jacket for hiking?")
print_agent_result(result)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5.2 Policy question — should trigger `get_policy_details` instead (screenshot as `05-agent-policy-question.png`)

# COMMAND ----------

result = ask_agent("What's our return policy?")
print_agent_result(result)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5.3 Off-domain question — groundedness check on the real deployed agent (screenshot as `05-agent-off-domain.png`)

# COMMAND ----------

result = ask_agent("What is the capital of France?")
print_agent_result(result)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Zero-compute evidence — no notebook needed at all
# MAGIC
# MAGIC The three agent calls above already produced real MLflow traces on the
# MAGIC server side (the endpoint has tracing enabled). These are pure UI
# MAGIC screenshots, no compute required:
# MAGIC
# MAGIC - **Serving endpoint page** → status `READY`, request count now includes
# MAGIC   these 3 calls → screenshot as `04-serving-endpoint.png`.
# MAGIC - **MLflow Experiment** (linked from the endpoint page) → the traces for
# MAGIC   these exact 3 calls, showing the tool-calling loop → screenshot as
# MAGIC   `06-mlflow-trace.png`.
# MAGIC - **Catalog Explorer** → `uc_agentic_ai.agentic_ai_schema.sai_agent_model` →
# MAGIC   registered model version → screenshot as `03-registered-model.png`.
# MAGIC
# MAGIC None of these need this notebook or any compute — just browse the workspace
# MAGIC UI.