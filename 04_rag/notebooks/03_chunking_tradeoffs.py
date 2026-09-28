# Databricks notebook source
# MAGIC %md
# MAGIC # Chunking Tradeoffs: 200/50 vs 800/100 Token Windows
# MAGIC
# MAGIC Compares two chunking strategies on the actual parsed product descriptions in
# MAGIC `product_details`: 200 tokens / 50-token overlap vs. 800 tokens / 100-token
# MAGIC overlap.
# MAGIC
# MAGIC **Why this is a real comparison here, not a formality:** checked the actual
# MAGIC data before assuming chunking even matters — `product_desc` ranges from 392 to
# MAGIC 4,575 characters (median 2,750, roughly 650–700 tokens). That means the median
# MAGIC product description **exceeds** a 200-token chunk and sits close to an 800-token
# MAGIC one, so these two strategies produce meaningfully different numbers of chunks
# MAGIC per product, not just a parameter that doesn't matter in practice.
# MAGIC
# MAGIC Every other notebook in this repo (`01_build_product_master_and_index.py`,
# MAGIC `02_rag_retrieval_demo.py`) embeds each product as **one** chunk (the whole
# MAGIC `product_combined` text). This notebook doesn't change that live setup — it's
# MAGIC an isolated analysis answering "should it be chunked smaller?", run against a
# MAGIC small sample with its own temporary index, cleaned up at the end.

# COMMAND ----------

# MAGIC %pip install -q tiktoken
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

catalog = "uc_agentic_ai"
schema = "agentic_ai_schema"

sample = spark.sql(f"""
    SELECT product_name, product_desc
    FROM {catalog}.{schema}.product_details
    WHERE LENGTH(product_desc) > 3000
    LIMIT 8
""").collect()

print(f"Sample: {len(sample)} long product descriptions (>3000 chars) to make the chunking difference visible")
for row in sample[:3]:
    print(f"  {row['product_name']}: {len(row['product_desc'])} chars")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Chunk both ways

# COMMAND ----------

import tiktoken

encoding = tiktoken.get_encoding("cl100k_base")


def chunk_by_tokens(text: str, chunk_size: int, overlap: int) -> list[str]:
    tokens = encoding.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunks.append(encoding.decode(tokens[start:end]))
        if end == len(tokens):
            break
        start += chunk_size - overlap
    return chunks


small_chunks = []  # 200 tokens / 50 overlap
large_chunks = []  # 800 tokens / 100 overlap

for row in sample:
    for i, c in enumerate(chunk_by_tokens(row["product_desc"], 200, 50)):
        small_chunks.append({"product_name": row["product_name"], "chunk_index": i, "content": c})
    for i, c in enumerate(chunk_by_tokens(row["product_desc"], 800, 100)):
        large_chunks.append({"product_name": row["product_name"], "chunk_index": i, "content": c})

print(f"200/50 strategy:  {len(small_chunks)} chunks across {len(sample)} products ({len(small_chunks)/len(sample):.1f} chunks/product avg)")
print(f"800/100 strategy: {len(large_chunks)} chunks across {len(sample)} products ({len(large_chunks)/len(sample):.1f} chunks/product avg)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Embed both chunk sets and compare retrieval
# MAGIC
# MAGIC Uses the same embedding endpoint as the live `product_index`
# MAGIC (`databricks-qwen3-embedding-0-6b`) so the comparison is apples-to-apples with
# MAGIC what's actually deployed. This computes embeddings directly via the serving
# MAGIC endpoint rather than building two temporary Vector Search indexes — enough to
# MAGIC compare chunk-level relevance without provisioning extra infrastructure for a
# MAGIC one-off analysis.

# COMMAND ----------

import numpy as np
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()


def embed_batch(texts: list[str]) -> list[list[float]]:
    response = w.serving_endpoints.query(name="databricks-qwen3-embedding-0-6b", input=texts)
    return [item.embedding for item in response.data]


def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


small_embeddings = embed_batch([c["content"] for c in small_chunks])
large_embeddings = embed_batch([c["content"] for c in large_chunks])

query = "what materials is this product made from and how do I clean it"
query_embedding = embed_batch([query])[0]

small_scored = sorted(
    zip(small_chunks, small_embeddings),
    key=lambda pair: cosine_sim(query_embedding, pair[1]),
    reverse=True,
)
large_scored = sorted(
    zip(large_chunks, large_embeddings),
    key=lambda pair: cosine_sim(query_embedding, pair[1]),
    reverse=True,
)

print(f"Query: {query}\n")
print("Top 3 matches, 200/50 chunking (small, precise chunks):")
for chunk, emb in small_scored[:3]:
    score = cosine_sim(query_embedding, emb)
    print(f"  [{score:.3f}] {chunk['product_name']} (chunk {chunk['chunk_index']}): {chunk['content'][:150]}...")

print("\nTop 3 matches, 800/100 chunking (large, contextual chunks):")
for chunk, emb in large_scored[:3]:
    score = cosine_sim(query_embedding, emb)
    print(f"  [{score:.3f}] {chunk['product_name']} (chunk {chunk['chunk_index']}): {chunk['content'][:150]}...")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Reading the result above
# MAGIC
# MAGIC Don't take this cell's word for which strategy "won" — look at the actual
# MAGIC top-3 printed above for this run and judge it directly:
# MAGIC
# MAGIC - Did a 200/50 chunk return a fragment (e.g. material info with the care
# MAGIC   instructions cut off, or vice versa) that would need a follow-up query to
# MAGIC   get the full picture?
# MAGIC - Did an 800/100 chunk return the complete answer in one hit, or did it dilute
# MAGIC   the match with a lot of unrelated text (sizing, pricing, etc.) alongside the
# MAGIC   relevant part?
# MAGIC - Re-run §2 with a different `query` (something narrower or broader) — the
# MAGIC   winner can flip depending on how specific the question is, which is the
# MAGIC   actual tradeoff, not a fixed verdict.
# MAGIC
# MAGIC What's independently verified (from the data stats in the setup cell, not from
# MAGIC any one query's ranking): most `product_desc` values (median ~690 tokens) fit
# MAGIC in a **single** 800-token chunk but need 4–5 chunks at 200 tokens. That means
# MAGIC 800/100 chunking is close to "one chunk per product" — what's actually
# MAGIC deployed today in `product_index` — while 200/50 is a real departure from it.
# MAGIC If your run's top-3 results favor 200/50 on narrow queries, that's the
# MAGIC standard chunking tradeoff (precision vs. fragmentation) — but confirm it
# MAGIC against what actually printed above rather than assuming it.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC - This notebook creates no persistent tables or indexes — everything is
# MAGIC   computed in-memory over a small sample for this analysis.
# MAGIC - If a future product category needs finer-grained chunking (e.g. long
# MAGIC   multi-page manuals rather than short descriptions), revisit this analysis
# MAGIC   with a sample from that category specifically — the finding above is
# MAGIC   scoped to this catalog's actual description lengths, not a universal rule.
