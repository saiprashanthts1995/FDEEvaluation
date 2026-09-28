# Databricks notebook source
# MAGIC %md
# MAGIC # Hybrid Retrieval: Exact References vs. Pure Semantic Search
# MAGIC
# MAGIC `product_index` was built as a `HYBRID` index (confirmed in
# MAGIC `03_vector_database/README.md` — subtype `HYBRID`), meaning it already blends
# MAGIC keyword and vector search. This notebook makes that concrete by comparing it
# MAGIC against pure semantic search (`query_type="ANN"`) on exact-reference queries —
# MAGIC the case where a pure embedding match can blur past an acronym or exact model
# MAGIC number that a keyword match would catch directly.
# MAGIC
# MAGIC No infrastructure change here — `product_index` already is hybrid; this
# MAGIC notebook demonstrates why that was the right choice rather than building
# MAGIC anything new.

# COMMAND ----------

# MAGIC %pip install -q databricks-vectorsearch
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

catalog = "uc_agentic_ai"
schema = "agentic_ai_schema"
endpoint_name = "ai_search_endpoint"
index_name = f"{catalog}.{schema}.product_index"

from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()
index = vsc.get_index(endpoint_name=endpoint_name, index_name=index_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Find a real exact-reference case in this catalog
# MAGIC
# MAGIC Rather than assuming a good test query, pull a genuinely distinctive product
# MAGIC name/model-number-shaped term straight from the live data — the same
# MAGIC discipline as the other notebooks in this repo (verify before demonstrating).

# COMMAND ----------

sample_names = [
    row["product_name"]
    for row in spark.sql(f"""
        SELECT product_name
        FROM {catalog}.{schema}.products
        WHERE product_name RLIKE '[0-9]'
        LIMIT 5
    """).collect()
]
print("Sample exact-reference-shaped product names (contain a model number):")
for name in sample_names:
    print(f"  {name}")

exact_query = sample_names[0] if sample_names else "Alpha Z10"
print(f"\nUsing as the exact-reference test query: {exact_query!r}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Compare `HYBRID` vs pure `ANN` (semantic-only) retrieval

# COMMAND ----------

hybrid_results = index.similarity_search(
    query_text=exact_query,
    columns=["product_name", "product_category"],
    num_results=5,
    query_type="HYBRID",
)
ann_results = index.similarity_search(
    query_text=exact_query,
    columns=["product_name", "product_category"],
    num_results=5,
    query_type="ANN",
)

print(f"Query: {exact_query!r}\n")
print("HYBRID (keyword + vector):")
for i, (name, category, score) in enumerate(hybrid_results["result"]["data_array"]):
    marker = " <-- exact match" if name == exact_query else ""
    print(f"  {i+1}. [{score:.3f}] {name}  ({category}){marker}")

print("\nANN (pure semantic):")
for i, (name, category, score) in enumerate(ann_results["result"]["data_array"]):
    marker = " <-- exact match" if name == exact_query else ""
    print(f"  {i+1}. [{score:.3f}] {name}  ({category}){marker}")

hybrid_names = [row[0] for row in hybrid_results["result"]["data_array"]]
ann_names = [row[0] for row in ann_results["result"]["data_array"]]
hybrid_rank = hybrid_names.index(exact_query) + 1 if exact_query in hybrid_names else None
ann_rank = ann_names.index(exact_query) + 1 if exact_query in ann_names else None
print(f"\nExact match rank — HYBRID: {hybrid_rank}, ANN: {ann_rank}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. A genuinely semantic query, for contrast
# MAGIC
# MAGIC Hybrid isn't strictly better on every query — on a query with no exact
# MAGIC keyword overlap in the catalog, keyword scoring contributes nothing useful and
# MAGIC results should look similar between the two modes. Worth checking both
# MAGIC directions rather than only the case that favors hybrid.

# COMMAND ----------

semantic_query = "something to keep my drinks cold while hiking"

hybrid_semantic = index.similarity_search(
    query_text=semantic_query, columns=["product_name", "product_category"], num_results=3, query_type="HYBRID"
)
ann_semantic = index.similarity_search(
    query_text=semantic_query, columns=["product_name", "product_category"], num_results=3, query_type="ANN"
)

print(f"Query: {semantic_query!r}\n")
print("HYBRID:")
for name, category, score in hybrid_semantic["result"]["data_array"]:
    print(f"  [{score:.3f}] {name}  ({category})")
print("\nANN:")
for name, category, score in ann_semantic["result"]["data_array"]:
    print(f"  [{score:.3f}] {name}  ({category})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC - Fully read-only.
# MAGIC - If §2 shows the exact match ranking higher (or only appearing) under
# MAGIC   `HYBRID`, that's the concrete justification for `product_index` being built
# MAGIC   as hybrid rather than pure-vector — catalog and support-agent queries
# MAGIC   plausibly include exact model numbers or product names, not just natural
# MAGIC   language descriptions.
