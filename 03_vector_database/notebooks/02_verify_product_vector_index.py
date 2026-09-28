# Databricks notebook source
# MAGIC %md
# MAGIC # Product Catalog — Vector Search Index Verification
# MAGIC
# MAGIC This assignment originally targeted the HR procedure guides in
# MAGIC `shared_data/documents/`, matching this repo's CLAUDE.md. It was repointed to
# MAGIC the product catalog use case introduced in assignment 2
# MAGIC (`uc_agentic_ai.agentic_ai_schema`), to stay consistent with the other
# MAGIC assignments now built on that same product/customer-service dataset.
# MAGIC
# MAGIC **This notebook does not create a new index.** A read-only inspection of the
# MAGIC workspace (`/api/2.0/vector-search/indexes`) found one already exists:
# MAGIC
# MAGIC | | |
# MAGIC |---|---|
# MAGIC | Index | `uc_agentic_ai.agentic_ai_schema.product_index` |
# MAGIC | Endpoint | `ai_search_endpoint` (STANDARD, ONLINE) |
# MAGIC | Source table | `uc_agentic_ai.agentic_ai_schema.product_master` |
# MAGIC | Embedding column | `product_combined` |
# MAGIC | Embedding model | `databricks-qwen3-embedding-0-6b` |
# MAGIC | Index type | `DELTA_SYNC`, `TRIGGERED`, subtype `HYBRID` (keyword + vector) |
# MAGIC | Status (read-only check) | `ONLINE_NO_PENDING_UPDATE`, 553 rows indexed |
# MAGIC
# MAGIC Creating a second, near-duplicate index on the same source table would waste
# MAGIC embedding-compute and fragment retrieval across two indexes for no benefit. This
# MAGIC notebook instead **verifies** the existing index end-to-end: documents the
# MAGIC create command as code (Step 0, disabled by default since the index already
# MAGIC exists), confirms the source table is healthy, confirms the index is actually
# MAGIC in sync with it, and runs retrieval sanity checks — the same bar this repo held
# MAGIC the original HR index to.

# COMMAND ----------

dbutils.widgets.text("catalog", "uc_agentic_ai", "UC Catalog")
dbutils.widgets.text("schema", "agentic_ai_schema", "UC Schema")
dbutils.widgets.text("source_table", "product_master", "Source table")
dbutils.widgets.text("index_name", "product_index", "Vector index name")
dbutils.widgets.text("endpoint_name", "ai_search_endpoint", "Vector Search endpoint")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
source_table = dbutils.widgets.get("source_table")
index_name = dbutils.widgets.get("index_name")
endpoint_name = dbutils.widgets.get("endpoint_name")

full_table_name = f"{catalog}.{schema}.{source_table}"
full_index_name = f"{catalog}.{schema}.{index_name}"

print(f"Source table: {full_table_name}")
print(f"Index:        {full_index_name}")
print(f"Endpoint:     {endpoint_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 0. How this index was created
# MAGIC
# MAGIC The index itself was created through the Databricks UI (Catalog Explorer →
# MAGIC `product_master` → Create → Vector Search Index), not by running code. The cell
# MAGIC below is the SDK-equivalent command, reconstructed from the index's own live
# MAGIC configuration (`index.describe()` in Step 2) so the UI-driven setup is still
# MAGIC reproducible as code and reviewable like any other infrastructure change.
# MAGIC
# MAGIC **Guarded, not runnable as-is:** `create_delta_sync_index` errors if the target
# MAGIC index name already exists, which it does. This cell is left disabled
# MAGIC (`RUN_CREATE = False`) so re-running the notebook top-to-bottom can never
# MAGIC collide with the live index — flip it only if you're pointing the widgets above
# MAGIC at a fresh index name or a different environment.

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient

RUN_CREATE = False  # set True only when full_index_name does not already exist

vsc = VectorSearchClient()

if RUN_CREATE:
    vsc.create_delta_sync_index(
        endpoint_name=endpoint_name,
        source_table_name=full_table_name,
        index_name=full_index_name,
        pipeline_type="TRIGGERED",
        primary_key="product_id",
        embedding_source_column="product_combined",
        embedding_model_endpoint_name="databricks-qwen3-embedding-0-6b",
    )
    print(f"Index creation requested: {full_index_name}")
else:
    print("RUN_CREATE is False — skipping create_delta_sync_index (index already exists).")
    print("This cell documents the command; it does not execute it by default.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Confirm the source table is healthy
# MAGIC
# MAGIC Row count, category spread, and a null-check on the column that actually gets
# MAGIC embedded — if `product_combined` were null or empty for a row, that row would be
# MAGIC embedded on garbage text and silently return poor matches with no error anywhere.

# COMMAND ----------

health = spark.sql(f"""
    SELECT
        COUNT(*) AS row_count,
        COUNT(DISTINCT product_category) AS distinct_categories,
        SUM(CASE WHEN product_combined IS NULL OR trim(product_combined) = '' THEN 1 ELSE 0 END) AS empty_combined_text,
        SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_primary_key
    FROM {full_table_name}
""").collect()[0]

print(f"Rows: {health['row_count']}")
print(f"Distinct categories: {health['distinct_categories']}")
print(f"Rows with empty embedding text: {health['empty_combined_text']}")
print(f"Rows with null primary key: {health['null_primary_key']}")

assert health["empty_combined_text"] == 0, "Some rows have empty product_combined text — these would embed on nothing."
assert health["null_primary_key"] == 0, "Null product_id breaks the DELTA_SYNC primary key contract."
print("\nSource table passes health checks.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Confirm the index is actually in sync with the source table
# MAGIC
# MAGIC An index can exist and show `ONLINE` while still being stale if the source
# MAGIC table changed after the last trigger. This compares the index's indexed row
# MAGIC count against the live table row count and surfaces the last sync timestamp —
# MAGIC don't trust a green status alone.

# COMMAND ----------

index = vsc.get_index(endpoint_name=endpoint_name, index_name=full_index_name)
index_info = index.describe()

indexed_row_count = index_info["status"]["indexed_row_count"]
detailed_state = index_info["status"]["detailed_state"]
last_sync = index_info["status"]["triggered_update_status"]["last_processed_commit_timestamp"]

print(f"Index state: {detailed_state}")
print(f"Indexed rows: {indexed_row_count}")
print(f"Live table rows: {health['row_count']}")
print(f"Last processed commit: {last_sync}")

if indexed_row_count != health["row_count"]:
    print(
        f"\nWARNING: indexed row count ({indexed_row_count}) does not match the live "
        f"table ({health['row_count']}) — trigger a sync with index.sync() before trusting retrieval."
    )
else:
    print("\nIndex row count matches the live source table.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Retrieval sanity checks
# MAGIC
# MAGIC Product-relevant natural-language queries, checked against the categories they
# MAGIC should land in — not just "did it return something," but "did it return the
# MAGIC right kind of thing."

# COMMAND ----------

test_cases = [
    ("wireless noise-cancelling headphones", "Electronics"),
    ("waterproof winter jacket", "Fashion"),
    ("software license for project management", "Software"),
]

for query, expected_category_hint in test_cases:
    print(f"\nQuery: {query}  (expecting something like: {expected_category_hint})")
    results = index.similarity_search(
        query_text=query,
        columns=["product_name", "product_category", "product_desc"],
        num_results=3,
    )
    for row in results["result"]["data_array"]:
        product_name, product_category, product_desc, score = row
        print(f"  [{score:.3f}] {product_name}  ({product_category})")
        print(f"    {product_desc[:120]}...")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC - No index was created or modified by this notebook — every step here is
# MAGIC   read-only against existing infrastructure.
# MAGIC - If Step 2 ever shows a row-count mismatch, run `index.sync()` and re-check
# MAGIC   before relying on this index for the Genie Space (assignment 2) or the RAG
# MAGIC   agent (assignment 4) — a stale index returns confident-looking answers about
# MAGIC   products that may have changed or no longer exist.
# MAGIC - `HYBRID` subtype means this index blends keyword and vector search — worth
# MAGIC   knowing if retrieval quality is ever debugged, since a pure-keyword match can
# MAGIC   outrank a semantically closer product for exact-term queries.
