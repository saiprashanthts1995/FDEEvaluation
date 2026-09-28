# Databricks notebook source
# MAGIC %md
# MAGIC # Build `product_master` and the Product Vector Search Index
# MAGIC
# MAGIC This is the actual pipeline that built the live data — not reconstructed
# MAGIC from guesswork. Re-verified read-only against the live workspace before
# MAGIC writing this notebook:
# MAGIC
# MAGIC | Claim | Verified |
# MAGIC |---|---|
# MAGIC | 509 PDFs at `/Volumes/uc_agentic_ai/agentic_ai_schema/data_files/01_Data_Files/product_docs/` | `SELECT COUNT(*) FROM READ_FILES(...)` → **509** |
# MAGIC | `product_details` table exists with `(product_name, product_desc)` | Confirmed via Unity Catalog API |
# MAGIC | `product_master` exists, 553 rows, all with non-null `product_desc` | Confirmed in `03_vector_database`'s verification notebook |
# MAGIC
# MAGIC **One real discrepancy, not silently papered over:** this script's Step 3
# MAGIC targets index `uc_agentic_ai.agentic_ai_schema.product_master_index` on a new
# MAGIC endpoint `agentic_ai_vs_endpoint`, embedding via `databricks-gte-large-en`. The
# MAGIC index actually **live** in the workspace today is
# MAGIC `uc_agentic_ai.agentic_ai_schema.product_index` on the existing
# MAGIC `ai_search_endpoint`, embedding via `databricks-qwen3-embedding-0-6b` (confirmed
# MAGIC via `GET /api/2.0/vector-search/indexes/...`). Most likely this script was an
# MAGIC earlier draft, and the index was later (re)created through the UI with a
# MAGIC different name/endpoint/embedding model. Both are valid `DELTA_SYNC` indexes
# MAGIC over the same `product_master.product_combined` column — this notebook is kept
# MAGIC as-is for provenance of *how the source data was built* (the PDF parsing and
# MAGIC join logic), and the index-creation cell is left disabled by default so running
# MAGIC this notebook can't create a second, conflicting index.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Config

# COMMAND ----------

catalog = "uc_agentic_ai"
schema = "agentic_ai_schema"
volume_path = f"/Volumes/{catalog}/{schema}/data_files/01_Data_Files/product_docs/"

# Step 3 config — disabled by default; see the discrepancy note above.
RUN_INDEX_CREATION = False
vs_endpoint_name = "agentic_ai_vs_endpoint"          # the script's original target; the LIVE index is on "ai_search_endpoint" instead
vs_index_name = f"{catalog}.{schema}.product_master_index"  # the LIVE index is instead named "product_index"
embedding_model_endpoint = "databricks-gte-large-en"  # the LIVE index instead uses "databricks-qwen3-embedding-0-6b"

spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — `product_details` from the PDFs
# MAGIC
# MAGIC Uses the built-in `ai_parse_document` SQL function to parse each PDF, then
# MAGIC concatenates all parsed elements into one text field. `product_name` is the
# MAGIC filename without the `.pdf` extension.
# MAGIC
# MAGIC Already run — `product_details` exists live with 509 rows. Re-running is safe
# MAGIC (`CREATE OR REPLACE TABLE`) but will re-parse all 509 PDFs.

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {catalog}.{schema}.product_details AS
SELECT
  regexp_replace(element_at(split(path, '/'), -1), '\\\\.pdf$', '') AS product_name,
  array_join(
    transform(
      CAST(parsed:document:elements AS ARRAY<VARIANT>),
      x -> CAST(x:content AS STRING)
    ),
    '\\n\\n'
  ) AS product_desc
FROM (
  SELECT path, ai_parse_document(content) AS parsed
  FROM READ_FILES('{volume_path}', format => 'binaryFile')
)
""")

# COMMAND ----------

display(spark.sql(f"SELECT COUNT(*) AS row_count FROM {catalog}.{schema}.product_details"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — `product_master`
# MAGIC
# MAGIC Joins `products` with `product_details` on a normalized `product_name` (colon
# MAGIC replaced with underscore, matching how the PDF filenames were saved — e.g. the
# MAGIC product *"Advanced Algebra: Concepts and Applications"* has the file
# MAGIC *"Advanced Algebra_ Concepts and Applications.pdf"*). Adds `product_id` as the
# MAGIC primary key (required by Vector Search) and a `product_combined` column
# MAGIC formatted as pseudo-XML tags for embedding.

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {catalog}.{schema}.product_master AS
SELECT
  p.product_id,
  p.product_name,
  p.product_category,
  p.product_sub_category,
  d.product_desc,
  concat(
    '<product_name>', coalesce(p.product_name, ''), '</product_name>\\n',
    '<product_category>', coalesce(p.product_category, ''), '</product_category>\\n',
    '<product_sub_category>', coalesce(p.product_sub_category, ''), '</product_sub_category>\\n',
    '<product_desc>', coalesce(d.product_desc, ''), '</product_desc>'
  ) AS product_combined
FROM {catalog}.{schema}.products p
INNER JOIN {catalog}.{schema}.product_details d
  ON regexp_replace(p.product_name, ':', '_') = d.product_name
""")

spark.sql(f"""
ALTER TABLE {catalog}.{schema}.product_master
SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
""")

# COMMAND ----------

display(spark.sql(f"""
SELECT COUNT(*) AS total_rows, COUNT(product_desc) AS rows_with_desc
FROM {catalog}.{schema}.product_master
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — Vector Search index (disabled — already exists as `product_index`)
# MAGIC
# MAGIC See the discrepancy note at the top. Flip `RUN_INDEX_CREATION = True` above
# MAGIC only if you intentionally want a second index under a different name/endpoint.

# COMMAND ----------

if RUN_INDEX_CREATION:
%pip install -q databricks-vectorsearch
dbutils.library.restartPython()
    from databricks.vector_search.client import VectorSearchClient

    vsc = VectorSearchClient()

    existing_endpoints = [e["name"] for e in vsc.list_endpoints().get("endpoints", [])]
    if vs_endpoint_name not in existing_endpoints:
        vsc.create_endpoint(name=vs_endpoint_name, endpoint_type="STANDARD")

    existing_indexes = [i["name"] for i in vsc.list_indexes(vs_endpoint_name).get("vector_indexes", [])]
    if vs_index_name not in existing_indexes:
        vsc.create_delta_sync_index(
            endpoint_name=vs_endpoint_name,
            source_table_name=f"{catalog}.{schema}.product_master",
            index_name=vs_index_name,
            pipeline_type="TRIGGERED",
            primary_key="product_id",
            embedding_source_column="product_combined",
            embedding_model_endpoint_name=embedding_model_endpoint,
        )
    else:
        vsc.get_index(vs_endpoint_name, vs_index_name).sync()
else:
    print("RUN_INDEX_CREATION is False. The live index (product_index on ai_search_endpoint) already exists.")
    print("See 02_verify_product_vector_index.py in this folder to check its health instead of creating a new one.")