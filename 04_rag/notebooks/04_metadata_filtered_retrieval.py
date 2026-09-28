# Databricks notebook source
# /// script
# [tool.databricks.environment]
# base_environment = "databricks_ai_v5"
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Metadata-Filtered Retrieval
# MAGIC
# MAGIC Demonstrates retrieval scoped by a metadata/topic field — the general pattern
# MAGIC of restricting results to a known category rather than relying on the query
# MAGIC text alone (e.g. a GDPR question should only ever surface GDPR documents, a
# MAGIC Travel question only Travel Policy documents). Applied here to
# MAGIC `product_category` as the topic field, and separately to `policies` via
# MAGIC `get_policy_details` from `01_build_agent_tools.py` — the same underlying
# MAGIC mechanics as `03_vector_database/notebooks/03_advanced_scenarios.py` §2, shown
# MAGIC here in the RAG-answer context rather than as a raw retrieval scenario.

# COMMAND ----------

# MAGIC %pip install -q databricks-vectorsearch
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

catalog = "uc_agentic_ai"
schema = "agentic_ai_schema"
endpoint_name = "ai_search_endpoint"
index_name = f"{catalog}.{schema}.product_index"

from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient

vsc = VectorSearchClient()
index = vsc.get_index(endpoint_name=endpoint_name, index_name=index_name)
workspace_client = WorkspaceClient()
llm_client = workspace_client.serving_endpoints.get_open_ai_client()
chat_model_endpoint = "databricks-gpt-oss-120b"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Same question, with and without a topic filter
# MAGIC
# MAGIC A category-ambiguous query ("something for staying organized" could mean
# MAGIC office supplies, software, or furniture) shows the filter actually changing
# MAGIC which products are even eligible to be retrieved — not just re-ranking the
# MAGIC same set.

# COMMAND ----------

query = "something for staying organized"

unfiltered = index.similarity_search(
    query_text=query, columns=["product_name", "product_category"], num_results=5
)
print("No filter:")
for name, category, score in unfiltered["result"]["data_array"]:
    print(f"  [{score:.3f}] {name}  ({category})")

software_only = index.similarity_search(
    query_text=query,
    columns=["product_name", "product_category"],
    filters={"product_category": "Software"},
    num_results=5,
)
print("\nFiltered to Software only:")
for name, category, score in software_only["result"]["data_array"]:
    print(f"  [{score:.3f}] {name}  ({category})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Grounded answer, scoped by topic
# MAGIC
# MAGIC Passes the category filter through to the same grounded-generation pattern as
# MAGIC `02_rag_retrieval_demo.py`, so the final answer is guaranteed to only discuss
# MAGIC products from the requested category — useful for, e.g., a category-scoped
# MAGIC page in an app where cross-category suggestions would be wrong regardless of
# MAGIC how semantically close they score.

# COMMAND ----------

SYSTEM_PROMPT = """You are a product catalog assistant. Answer using ONLY the \
product context provided below, which has already been filtered to the \
category the user asked about. Cite the product name for every claim."""


def answer_scoped(query: str, category: str, num_results: int = 4) -> str:
    hits = index.similarity_search(
        query_text=query,
        columns=["product_name", "product_category", "product_desc"],
        filters={"product_category": category},
        num_results=num_results,
    )
    rows = hits["result"]["data_array"]
    if not rows:
        return f"No products found in category '{category}' matching this query."

    context_block = "\n".join(
        f"- {name} ({category}): {desc[:300]}" for name, category, desc, score in rows
    )
    response = llm_client.chat.completions.create(
        model=chat_model_endpoint,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Product context (category: {category}):\n{context_block}\n\nQuestion: {query}"},
        ],
    )
    return response.choices[0].message.content


print(answer_scoped("something for staying organized", "Software"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Policy retrieval is already topic-scoped by construction
# MAGIC
# MAGIC `get_policy_details` (from `01_build_agent_tools.py`) doesn't need a separate
# MAGIC metadata filter demo — it's already scoped to a single topic table
# MAGIC (`policies`, 6 rows total) by its own `WHERE lower(policy) LIKE ...` clause.
# MAGIC That's the structured-lookup equivalent of what a vector-index metadata filter
# MAGIC does for unstructured content: guarantee the result set can't cross into an
# MAGIC unrelated topic.

# COMMAND ----------

display(spark.sql(f"SELECT * FROM {catalog}.{schema}.get_policy_details('warranty')"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC - Fully read-only against existing infrastructure.
# MAGIC - `product_sub_category` is also available as a filter column if
# MAGIC   `product_category` alone is too coarse for a given use case.
