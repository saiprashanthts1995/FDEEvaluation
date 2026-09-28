# Databricks notebook source
# MAGIC %md
# MAGIC # Vector Search: Freshness, Filtering, Index Types, and Query Tuning
# MAGIC
# MAGIC Covers four scenarios not covered by `01_build_product_master_and_index.py`
# MAGIC (which builds the source data) or `02_verify_product_vector_index.py` (which
# MAGIC verifies the already-live index): freshness, metadata-filtered search, Delta
# MAGIC Sync vs. Direct Vector Access, and `top_k` tuning.
# MAGIC
# MAGIC All against the live `product_index` unless noted — the freshness test is the
# MAGIC one cell that writes (and cleans up after itself).

# COMMAND ----------

# MAGIC %pip install -q databricks-vectorsearch
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

catalog = "uc_agentic_ai"
schema = "agentic_ai_schema"
endpoint_name = "ai_search_endpoint"
index_name = f"{catalog}.{schema}.product_index"
source_table = f"{catalog}.{schema}.product_master"

from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()
index = vsc.get_index(endpoint_name=endpoint_name, index_name=index_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Freshness test
# MAGIC
# MAGIC Inserts one clearly-fake test product, triggers a sync, polls until it's
# MAGIC actually searchable, and measures how long that took — then deletes the test
# MAGIC row and re-syncs so the live index isn't left with junk data.
# MAGIC
# MAGIC **This cell writes to `product_master`.** It's self-cleaning, but it's a real
# MAGIC write to a table other assignments depend on — run it deliberately, not as
# MAGIC part of an unattended "run all."

# COMMAND ----------

import time

RUN_FRESHNESS_TEST = False  # set True deliberately — this writes and deletes a test row

if RUN_FRESHNESS_TEST:
    test_product_id = "TEST-FRESHNESS-9999"
    test_product_name = "Freshness Test Product Zzzyx"

    spark.sql(f"""
        INSERT INTO {source_table}
        (product_id, product_name, product_category, product_sub_category, product_desc, product_combined)
        VALUES (
            '{test_product_id}',
            '{test_product_name}',
            'Test',
            'Test',
            'A product that exists only to test vector index sync latency.',
            '<product_name>{test_product_name}</product_name>\\n<product_category>Test</product_category>\\n<product_sub_category>Test</product_sub_category>\\n<product_desc>A product that exists only to test vector index sync latency.</product_desc>'
        )
    """)

    index.sync()
    sync_triggered_at = time.time()

    found = False
    timeout_s = 300
    while time.time() - sync_triggered_at < timeout_s:
        results = index.similarity_search(
            query_text=test_product_name,
            columns=["product_id", "product_name"],
            num_results=5,
        )
        hit_ids = [row[0] for row in results["result"]["data_array"]]
        if test_product_id in hit_ids:
            found = True
            break
        time.sleep(5)

    latency_s = time.time() - sync_triggered_at
    if found:
        print(f"New row became searchable after {latency_s:.0f}s")
    else:
        print(f"New row NOT found within {timeout_s}s — check pipeline_type is TRIGGERED and sync() was accepted")

    # Clean up regardless of outcome
    spark.sql(f"DELETE FROM {source_table} WHERE product_id = '{test_product_id}'")
    index.sync()
    print("Test row deleted and re-sync triggered.")
else:
    print("RUN_FRESHNESS_TEST is False. Flip to True to run this scenario deliberately.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Filtered search
# MAGIC
# MAGIC Restricts retrieval to a specific `product_category` using the `filters`
# MAGIC parameter, rather than relying on the query text alone to steer results —
# MAGIC useful when the caller already knows the category (e.g. a category-scoped
# MAGIC page in an app) and wants to guarantee results don't leak from other
# MAGIC categories.

# COMMAND ----------

unfiltered = index.similarity_search(
    query_text="wireless headphones",
    columns=["product_name", "product_category"],
    num_results=5,
)
print("Unfiltered:")
for name, category, score in unfiltered["result"]["data_array"]:
    print(f"  [{score:.3f}] {name}  ({category})")

filtered = index.similarity_search(
    query_text="wireless headphones",
    columns=["product_name", "product_category"],
    filters={"product_category": "Electronics"},
    num_results=5,
)
print("\nFiltered to Electronics only:")
for name, category, score in filtered["result"]["data_array"]:
    print(f"  [{score:.3f}] {name}  ({category})")
    assert category == "Electronics", f"Filter leaked a non-Electronics result: {name} ({category})"

print("\nFilter check passed: every result was in the requested category.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Index type comparison: Delta Sync vs. Direct Vector Access
# MAGIC
# MAGIC `product_index` is a `DELTA_SYNC` index — Databricks computes embeddings and
# MAGIC keeps the index in sync with `product_master` automatically via Change Data
# MAGIC Feed. The alternative, a **Direct Vector Access** index, takes manually-computed
# MAGIC embeddings via explicit `upsert()`/`delete()` calls — no source Delta table
# MAGIC required, full control over what's indexed and when, at the cost of owning the
# MAGIC embedding pipeline yourself.
# MAGIC
# MAGIC This builds a small Direct Access index over a 10-row sample to demonstrate
# MAGIC the mechanics side-by-side — not a replacement for `product_index`.
# MAGIC
# MAGIC | | Delta Sync (`product_index`) | Direct Vector Access (this demo) |
# MAGIC |---|---|---|
# MAGIC | Embeddings | Computed automatically by the embedding model endpoint | Computed manually, passed to `upsert()` |
# MAGIC | Sync | Automatic via CDF, `TRIGGERED` or `CONTINUOUS` | Manual — you call `upsert()`/`delete()` yourself |
# MAGIC | Source | Must be a UC Delta table | No source table required — any data you can embed |
# MAGIC | Operational effort | Lower | Higher, but more flexible (e.g. embeddings from a custom model, non-tabular sources) |

# COMMAND ----------

RUN_DIRECT_ACCESS_DEMO = False  # creates a small second index — disabled by default

if RUN_DIRECT_ACCESS_DEMO:
    direct_index_name = f"{catalog}.{schema}.product_direct_access_demo"

    existing_indexes = [i["name"] for i in vsc.list_indexes(endpoint_name).get("vector_indexes", [])]
    if direct_index_name not in existing_indexes:
        vsc.create_direct_access_index(
            endpoint_name=endpoint_name,
            index_name=direct_index_name,
            primary_key="product_id",
            embedding_dimension=1024,  # matches databricks-qwen3-embedding-0-6b's output dimension
            embedding_vector_column="embedding",
            schema={
                "product_id": "string",
                "product_name": "string",
                "product_category": "string",
                "embedding": "array<float>",
            },
        )

    sample_rows = spark.sql(f"""
        SELECT product_id, product_name, product_category, product_combined
        FROM {source_table}
        LIMIT 10
    """).collect()

    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()

    def embed(text: str) -> list[float]:
        response = w.serving_endpoints.query(
            name="databricks-qwen3-embedding-0-6b",
            input=[text],
        )
        return response.data[0].embedding

    direct_index = vsc.get_index(endpoint_name, direct_index_name)
    upsert_payload = [
        {
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "product_category": row["product_category"],
            "embedding": embed(row["product_combined"]),
        }
        for row in sample_rows
    ]
    direct_index.upsert(upsert_payload)
    print(f"Upserted {len(upsert_payload)} rows into {direct_index_name}")
else:
    print("RUN_DIRECT_ACCESS_DEMO is False. This would create a second, small demo index — not required for anything downstream.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Query tuning: `top_k` tradeoffs
# MAGIC
# MAGIC A small `top_k` (e.g. 3) favors precision — every result is highly relevant,
# MAGIC but a genuinely useful match ranked 4th never reaches the caller. A large
# MAGIC `top_k` (e.g. 15) favors recall at the cost of the caller (or the downstream
# MAGIC LLM) having to sift through weaker matches. For a RAG agent specifically,
# MAGIC `top_k` also directly controls how much context gets stuffed into the prompt —
# MAGIC too high risks diluting the LLM's attention across marginally-relevant chunks
# MAGIC (see `04_rag/`'s grounded-generation demo, which uses `num_results=4` as a
# MAGIC middle ground).

# COMMAND ----------

query = "comfortable running shoes"

for k in (3, 15):
    results = index.similarity_search(
        query_text=query,
        columns=["product_name", "product_category"],
        num_results=k,
    )
    hits = results["result"]["data_array"]
    scores = [row[-1] for row in hits]
    print(f"\ntop_k={k}: {len(hits)} results, score range {min(scores):.3f}–{max(scores):.3f}")
    for name, category, score in hits[:5]:
        print(f"  [{score:.3f}] {name}  ({category})")
    if k == 15 and len(hits) > 5:
        print(f"  ... plus {len(hits) - 5} more, including weaker matches not shown above")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC - Sections 2 and 4 are fully read-only. Section 1 writes and cleans up after
# MAGIC   itself but is disabled by default. Section 3 creates a small second index
# MAGIC   and is disabled by default — it's a demo of the mechanics, not something
# MAGIC   this project needs going forward.
# MAGIC - Recommended production default for this catalog's RAG use: `top_k` in the
# MAGIC   4–8 range — enough to cover near-duplicate products (many products here
# MAGIC   have multiple close variants) without diluting the grounded-generation
# MAGIC   prompt in `04_rag/`.
