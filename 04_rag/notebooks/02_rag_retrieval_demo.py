# Databricks notebook source
# /// script
# [tool.databricks.environment]
# base_environment = "databricks_ai_v5"
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # RAG Demo: Grounded Product Answers with Citations
# MAGIC
# MAGIC Demonstrates the retrieval-augmented-generation pattern on its own — retrieve,
# MAGIC then generate a grounded answer — separately from the full tool-calling agent
# MAGIC in [`05_agent_creation/`](../../05_agent_creation/). Useful for debugging
# MAGIC retrieval quality in isolation: if an answer is wrong, this notebook makes it
# MAGIC obvious whether the problem is retrieval (wrong chunks came back) or generation
# MAGIC (right chunks came back, but the LLM ignored or misread them).
# MAGIC
# MAGIC Uses the live `product_index` (verified in `03_vector_database/`) and a
# MAGIC Databricks Foundation Model API chat endpoint — no new infrastructure created.

# COMMAND ----------

# MAGIC %pip install -q databricks-vectorsearch
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

catalog = "uc_agentic_ai"
schema = "agentic_ai_schema"
endpoint_name = "ai_search_endpoint"
index_name = f"{catalog}.{schema}.product_index"
chat_model_endpoint = "databricks-gpt-oss-120b"  # matches the LLM used in 05_agent_creation's deployed agent

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Retrieve
# MAGIC
# MAGIC Top-k similarity search against the product index. This step alone is worth
# MAGIC inspecting before trusting anything downstream — if the wrong products come
# MAGIC back here, no amount of clever prompting fixes the final answer.

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()
index = vsc.get_index(endpoint_name=endpoint_name, index_name=index_name)


def retrieve(query: str, num_results: int = 4):
    results = index.similarity_search(
        query_text=query,
        columns=["product_id", "product_name", "product_category", "product_desc"],
        num_results=num_results,
    )
    return results["result"]["data_array"]


sample_hits = retrieve("a warm jacket for hiking in cold weather")
for product_id, product_name, product_category, product_desc, score in sample_hits:
    print(f"[{score:.3f}] {product_name}  ({product_category})  id={product_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Construct a grounded prompt
# MAGIC
# MAGIC The system prompt explicitly instructs the model to answer **only** from the
# MAGIC retrieved context and to say so plainly when the context doesn't support an
# MAGIC answer — the same grounding discipline this repo's CLAUDE.md requires for the
# MAGIC HR use case ("do not infer policy beyond the retrieved material"), applied here
# MAGIC to the product catalog.

# COMMAND ----------

SYSTEM_PROMPT = """You are a product catalog assistant. Answer the user's question \
using ONLY the product context provided below. Cite the product name for every \
claim you make. If the retrieved context does not contain enough information to \
answer the question, say so explicitly instead of guessing or using outside \
knowledge."""


def build_context_block(hits) -> str:
    lines = []
    for product_id, product_name, product_category, product_desc, score in hits:
        lines.append(
            f"- {product_name} (category: {product_category}, id: {product_id}): {product_desc[:400]}"
        )
    return "\n".join(lines)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Generate, grounded in the retrieved context
# MAGIC
# MAGIC Uses the workspace's own OpenAI-compatible client against a Foundation Model
# MAGIC API endpoint — the same pattern `05_agent_creation`'s deployed agent uses for
# MAGIC its LLM calls.

# COMMAND ----------

from databricks.sdk import WorkspaceClient

workspace_client = WorkspaceClient()
llm_client = workspace_client.serving_endpoints.get_open_ai_client()


def answer_grounded(query: str, num_results: int = 4) -> str:
    hits = retrieve(query, num_results=num_results)
    context_block = build_context_block(hits)

    response = llm_client.chat.completions.create(
        model=chat_model_endpoint,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Product context:\n{context_block}\n\nQuestion: {query}",
            },
        ],
    )
    return response.choices[0].message.content


print(answer_grounded("What's a good product for someone who hikes in cold weather?"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Grounding refusal check
# MAGIC
# MAGIC The real test of a RAG system isn't just "does it answer the easy question" —
# MAGIC it's "does it correctly decline when the retrieved context can't support an
# MAGIC answer," instead of falling back on the LLM's general knowledge and inventing a
# MAGIC plausible-sounding but ungrounded response. This query is deliberately outside
# MAGIC the product catalog's domain.

# COMMAND ----------

off_domain_answer = answer_grounded("What is the capital of France?")
print(off_domain_answer)

assert not any(
    marker in off_domain_answer for marker in ("Paris",)
), "The model answered from general knowledge instead of declining — grounding failed."
print("\nGrounding check passed: the model did not answer from outside knowledge.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC - No new infrastructure was created by this notebook — it's read-only against
# MAGIC   the existing `product_index` and calls an existing Foundation Model API
# MAGIC   endpoint.
# MAGIC - Step 4's assertion is a coarse check (string match on the obviously-correct
# MAGIC   answer), good enough to catch a clearly broken system prompt, not a
# MAGIC   substitute for the scorer-based evaluation in `05_agent_creation`
# MAGIC   (`RelevanceToQuery`, `Safety`, `RetrievalGroundedness`).
# MAGIC - `01_build_agent_tools.py` in this folder adds the structured-lookup half of
# MAGIC   retrieval (policies, customer history) that this vector-only demo doesn't
# MAGIC   cover — the deployed agent in `05_agent_creation` combines both.
