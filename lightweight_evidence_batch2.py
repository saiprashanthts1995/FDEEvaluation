# Databricks notebook source
# MAGIC %md
# MAGIC # Lightweight Evidence, Batch 2
# MAGIC
# MAGIC Covers everything left over after `lightweight_evidence_3_4_5.py`: the
# MAGIC remaining screenshots for `03_vector_database/` and `04_rag/`. Same rules as
# MAGIC before — **zero `%pip install` cells**, just `spark.sql(...)` and `requests`
# MAGIC against the REST APIs directly.
# MAGIC
# MAGIC **Not covered here** (still needs the heavier notebooks or a UI-only visit,
# MAGIC not because they're hard, but because they need real package installs or
# MAGIC aren't notebook tasks at all):
# MAGIC - `05_agent_creation/01, 02, 07` (MLflow run + evaluation) — needs
# MAGIC   `deploy_agent.py` / `03_agent_evaluation.py` directly (heavy installs:
# MAGIC   `databricks-agents`, `mlflow-skinny[databricks]`). Try them now if you have
# MAGIC   quota — the agent endpoint itself is confirmed healthy again.
# MAGIC - `05_agent_creation/03, 06, 09` — pure UI browsing (Catalog Explorer,
# MAGIC   MLflow Experiment, Serving endpoint Metrics tab), no notebook needed at all.
# MAGIC - `05_agent_creation/08` (root-cause trace) — needs `04_tracing_and_root_cause.py`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup — no installs

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


def vector_search(query_text, num_results=5, filters=None, columns=None, query_type=None):
    body = {
        "columns": columns or ["product_name", "product_category", "product_desc"],
        "query_text": query_text,
        "num_results": num_results,
    }
    if filters:
        body["filters_json"] = str(filters).replace("'", '"')
    if query_type:
        body["query_type"] = query_type
    resp = requests.post(
        f"{DATABRICKS_HOST}/api/2.0/vector-search/indexes/{index_name}/query",
        headers=HEADERS,
        json=body,
    )
    return resp.json()["result"]["data_array"]


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


print("Ready.")

# COMMAND ----------

# MAGIC %md
# MAGIC # Assignment 3 — remaining items

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.1 `product_details` parsed (SQL — screenshot as `01-product-details-parsed.png`)

# COMMAND ----------

display(spark.sql(f"""
    SELECT COUNT(*) AS row_count
    FROM {catalog}.{schema}.product_details
"""))
display(spark.sql(f"""
    SELECT product_name, LEFT(product_desc, 200) AS product_desc_preview
    FROM {catalog}.{schema}.product_details
    LIMIT 5
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.2 Sync freshness check (REST + SQL — screenshot as `05-sync-freshness-check.png`)
# MAGIC
# MAGIC Compares the index's `indexed_row_count` against the live table row count,
# MAGIC and shows the last processed commit timestamp — this also **triggers a real
# MAGIC sync** (harmless; a no-op if nothing changed since the last one).

# COMMAND ----------

live_count = spark.sql(f"SELECT COUNT(*) AS c FROM {catalog}.{schema}.product_master").collect()[0]["c"]

sync_resp = requests.post(
    f"{DATABRICKS_HOST}/api/2.0/vector-search/indexes/{index_name}/sync",
    headers=HEADERS,
)
print(f"Sync triggered: HTTP {sync_resp.status_code}")

info = requests.get(f"{DATABRICKS_HOST}/api/2.0/vector-search/indexes/{index_name}", headers=HEADERS).json()
indexed_count = info["status"]["indexed_row_count"]
last_sync = info["status"]["triggered_update_status"]["last_processed_commit_timestamp"]

print(f"Indexed rows: {indexed_count}")
print(f"Live table rows: {live_count}")
print(f"Last processed commit: {last_sync}")
print(f"Match: {indexed_count == live_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.3 Freshness test — insert, sync, measure (disabled by default — writes a test row)
# MAGIC
# MAGIC Set `RUN_FRESHNESS_TEST = True` to actually run it. Self-cleaning: deletes
# MAGIC the test row and re-syncs at the end regardless of outcome.

# COMMAND ----------

import time

RUN_FRESHNESS_TEST = False  # flip deliberately — writes and deletes a test row

if RUN_FRESHNESS_TEST:
    test_id = "TEST-FRESHNESS-9999"
    test_name = "Freshness Test Product Zzzyx"

    spark.sql(f"""
        INSERT INTO {catalog}.{schema}.product_master
        (product_id, product_name, product_category, product_sub_category, product_desc, product_combined)
        VALUES (
            '{test_id}', '{test_name}', 'Test', 'Test',
            'A product that exists only to test vector index sync latency.',
            '<product_name>{test_name}</product_name><product_category>Test</product_category><product_sub_category>Test</product_sub_category><product_desc>A product that exists only to test vector index sync latency.</product_desc>'
        )
    """)

    requests.post(f"{DATABRICKS_HOST}/api/2.0/vector-search/indexes/{index_name}/sync", headers=HEADERS)
    start = time.time()

    found = False
    while time.time() - start < 300:
        hits = vector_search(test_name, num_results=5, columns=["product_id", "product_name"])
        if any(row[0] == test_id for row in hits):
            found = True
            break
        time.sleep(5)

    elapsed = time.time() - start
    print(f"{'Found' if found else 'NOT found'} after {elapsed:.0f}s")

    spark.sql(f"DELETE FROM {catalog}.{schema}.product_master WHERE product_id = '{test_id}'")
    requests.post(f"{DATABRICKS_HOST}/api/2.0/vector-search/indexes/{index_name}/sync", headers=HEADERS)
    print("Test row deleted, re-sync triggered.")
else:
    print("RUN_FRESHNESS_TEST is False. Flip to True to run this deliberately.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.4 Index type comparison (disabled by default — creates a second index)
# MAGIC
# MAGIC Direct Vector Access index over a 10-row sample, built and queried via plain
# MAGIC REST (`POST /api/2.0/vector-search/indexes` with `direct_access_index_spec`,
# MAGIC then `POST .../upsert-data-vectors`) — no SDK needed, but this is real extra
# MAGIC infrastructure, so it stays off by default.

# COMMAND ----------

RUN_DIRECT_ACCESS_DEMO = False  # flip deliberately — creates a small second index

if RUN_DIRECT_ACCESS_DEMO:
    direct_index_name = f"{catalog}.{schema}.product_direct_access_demo"

    create_resp = requests.post(
        f"{DATABRICKS_HOST}/api/2.0/vector-search/indexes",
        headers=HEADERS,
        json={
            "name": direct_index_name,
            "endpoint_name": "ai_search_endpoint",
            "primary_key": "product_id",
            "index_type": "DIRECT_ACCESS",
            "direct_access_index_spec": {
                "embedding_vector_columns": [
                    {"name": "embedding", "embedding_dimension": 1024}
                ],
                "schema_json": '{"product_id": "string", "product_name": "string", "embedding": "array<float>"}',
            },
        },
    )
    print(f"Create index: HTTP {create_resp.status_code}")
    print(create_resp.json())

    sample = spark.sql(f"""
        SELECT product_id, product_name, product_combined
        FROM {catalog}.{schema}.product_master
        LIMIT 10
    """).collect()

    def embed(text):
        resp = requests.post(
            f"{DATABRICKS_HOST}/serving-endpoints/databricks-qwen3-embedding-0-6b/invocations",
            headers=HEADERS,
            json={"input": [text]},
        )
        return resp.json()["data"][0]["embedding"]

    vectors = [
        {"product_id": row["product_id"], "product_name": row["product_name"], "embedding": embed(row["product_combined"])}
        for row in sample
    ]
    upsert_resp = requests.post(
        f"{DATABRICKS_HOST}/api/2.0/vector-search/indexes/{direct_index_name}/upsert-data-vectors",
        headers=HEADERS,
        json={"inputs_json": str(vectors).replace("'", '"')},
    )
    print(f"Upsert: HTTP {upsert_resp.status_code}, {len(vectors)} rows")
else:
    print("RUN_DIRECT_ACCESS_DEMO is False. This scenario is optional — flip on only if you want it covered.")

# COMMAND ----------

# MAGIC %md
# MAGIC # Assignment 4 — remaining items

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.1 Retrieval output (REST — screenshot as `02-retrieval-output.png`)

# COMMAND ----------

for name, category, desc, score in vector_search("comfortable waterproof hiking boots", num_results=5):
    print(f"[{score:.3f}] {name}  ({category})")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.2 Metadata-filtered retrieval + scoped answer (REST — screenshot as `06-filtered-retrieval.png`)

# COMMAND ----------

query = "something for staying organized"

print("No filter:")
for name, category, score in vector_search(query, num_results=5, columns=["product_name", "product_category"]):
    print(f"  [{score:.3f}] {name}  ({category})")

print("\nFiltered to Software:")
software_hits = vector_search(
    query, num_results=5, columns=["product_name", "product_category"],
    filters={"product_category": "Software"},
)
for name, category, score in software_hits:
    print(f"  [{score:.3f}] {name}  ({category})")

scoped_hits = vector_search(
    query, num_results=4, columns=["product_name", "product_category", "product_desc"],
    filters={"product_category": "Software"},
)
context_block = "\n".join(f"- {n} ({c}): {d[:300]}" for n, c, d, s in scoped_hits)
SCOPED_PROMPT = "You are a product catalog assistant. Answer ONLY from the product context below, already filtered to the requested category. Cite product names."
answer = chat(SCOPED_PROMPT, f"Product context (category: Software):\n{context_block}\n\nQuestion: {query}")
print(f"\nScoped answer:\n{answer}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.3 Hybrid vs. ANN (REST — screenshot as `07-hybrid-vs-ann.png`)

# COMMAND ----------

sample_names = [
    row["product_name"]
    for row in spark.sql(f"""
        SELECT product_name FROM {catalog}.{schema}.products
        WHERE product_name RLIKE '[0-9]' LIMIT 5
    """).collect()
]
exact_query = sample_names[0] if sample_names else "Alpha Z10"
print(f"Exact-reference query: {exact_query!r}\n")

hybrid = vector_search(exact_query, num_results=5, columns=["product_name", "product_category"], query_type="HYBRID")
ann = vector_search(exact_query, num_results=5, columns=["product_name", "product_category"], query_type="ANN")

print("HYBRID:")
for i, (name, category, score) in enumerate(hybrid):
    marker = " <-- exact match" if name == exact_query else ""
    print(f"  {i+1}. [{score:.3f}] {name}  ({category}){marker}")

print("\nANN:")
for i, (name, category, score) in enumerate(ann):
    marker = " <-- exact match" if name == exact_query else ""
    print(f"  {i+1}. [{score:.3f}] {name}  ({category}){marker}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.4 Chunking tradeoffs — word-count approximation (no `tiktoken` install)
# MAGIC
# MAGIC Uses a word-count proxy for "tokens" (roughly `words * 1.3`) instead of a
# MAGIC real tokenizer, purely to avoid a `%pip install tiktoken` under tight quota.
# MAGIC This is an approximation, not exact token counts — good enough to see the
# MAGIC same structural tradeoff (small vs. large chunks), not precise enough to
# MAGIC quote the exact chunk boundaries a real tokenizer would produce.

# COMMAND ----------

sample = spark.sql(f"""
    SELECT product_name, product_desc
    FROM {catalog}.{schema}.product_details
    WHERE LENGTH(product_desc) > 3000
    LIMIT 5
""").collect()


def chunk_by_words(text, approx_tokens, overlap_tokens):
    words = text.split()
    words_per_chunk = int(approx_tokens / 1.3)
    overlap_words = int(overlap_tokens / 1.3)
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + words_per_chunk, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += words_per_chunk - overlap_words
    return chunks


small_total, large_total = 0, 0
for row in sample:
    small_total += len(chunk_by_words(row["product_desc"], 200, 50))
    large_total += len(chunk_by_words(row["product_desc"], 800, 100))

print(f"Sample: {len(sample)} long product descriptions")
print(f"~200-word-equivalent chunks: {small_total} total ({small_total/len(sample):.1f}/product)")
print(f"~800-word-equivalent chunks: {large_total} total ({large_total/len(sample):.1f}/product)")
print("\n(See 04_rag/notebooks/03_chunking_tradeoffs.py for the exact-tokenizer version, if you have quota to install tiktoken.)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC - Section 3.2 triggers a real (harmless) index sync. Sections 3.3 and 3.4
# MAGIC   write real data/infrastructure and are disabled by default.
# MAGIC - Everything else here is fully read-only.
