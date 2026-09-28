# Retrieval-Augmented Generation: Product Catalog Assistant

## Purpose

Builds the structured-lookup half of the agent's retrieval layer (Unity Catalog functions over `policies` and `cust_service_data`) and demonstrates the unstructured half — vector retrieval + grounded generation — on its own, separately from the full tool-orchestrating agent in [`05_agent_creation/`](../05_agent_creation/). Splitting these apart makes debugging tractable: if the final agent gives a wrong answer, you can isolate whether retrieval or generation (or tool routing) is at fault.

## What's Here

- [`notebooks/01_build_agent_tools.py`](notebooks/01_build_agent_tools.py) — creates `get_policy_details` and `get_customer_service_history`, two Unity Catalog functions used as structured-lookup agent tools. Both functions already exist live, confirmed via the Unity Catalog API before writing this.
- [`notebooks/02_rag_retrieval_demo.py`](notebooks/02_rag_retrieval_demo.py) — a standalone retrieve-then-generate demo against the `product_index` from `03_vector_database/`, with an explicit grounding-refusal check (an off-domain question should be declined, not answered from the LLM's general knowledge).
- [`notebooks/03_chunking_tradeoffs.py`](notebooks/03_chunking_tradeoffs.py) — compares 200/50 vs. 800/100 token chunking on real product descriptions (392–4,575 chars, median ~690 tokens — long enough that chunk size genuinely changes chunk counts).
- [`notebooks/04_metadata_filtered_retrieval.py`](notebooks/04_metadata_filtered_retrieval.py) — scopes both raw retrieval and grounded answers to a `product_category` filter, plus a callout for why `get_policy_details` doesn't need a separate filter demo.
- [`notebooks/05_hybrid_retrieval_demo.py`](notebooks/05_hybrid_retrieval_demo.py) — compares `HYBRID` vs. pure `ANN` retrieval on an exact-reference query (a real product name pulled from the live catalog, not assumed) and a purely semantic one.

## Scenario Coverage

All 5 scenarios were run end to end against the live workspace (via [`../lightweight_evidence_3_4_5.py`](../lightweight_evidence_3_4_5.py) and [`../lightweight_evidence_batch2.py`](../lightweight_evidence_batch2.py), the zero-install REST/SQL path — functionally equivalent to notebooks 02–05, chosen for the free-tier compute constraints in play at the time):

| Scenario | Result |
|---|---|
| 1. Baseline RAG pipeline (chunk, embed, index, retrieve + cite) | Retrieved products for "a good product for someone who hikes in cold weather" and generated an answer citing Arctic Shield 360° Winter Jacket and SummitShield Thermal Jacket by name from the retrieved context. |
| 2. Chunking Tradeoffs (200/50 vs 800/100) | On 5 long product descriptions (>3,000 chars each): ~200-word-equivalent chunking produced 21 chunks total (4.2/product); ~800-word-equivalent produced 5 (1.0/product) — confirming most descriptions fit a single large chunk but need several small ones. |
| 3. Metadata-Filtered Retrieval | "something for staying organized" filtered to `product_category = "Software"` — every result stayed in-category (TaskFlow Pro, ProTasker Suite, StreamEase, ...), and the scoped grounded answer cited only those two as the top recommendations. |
| 4. Groundedness Failure Hunt | Off-domain question ("What is the capital of France?") correctly declined: *"does not contain information about the capital of France."* Assertion passed. |
| 5. Hybrid Retrieval | Exact-reference query (a real product name with a model number, "BrownBox SwiftWatch X500") ranked **#1 with score 1.000 under `HYBRID`**, vs. **#1 with only 0.624 under pure `ANN`** — a concrete, measured case where hybrid search's keyword component meaningfully outperforms pure semantic search on exact references. |

## Why Two Kinds of Retrieval

A single vector index doesn't cover every retrieval need well:

| Question type | Right tool | Why |
|---|---|---|
| "What's a good waterproof jacket?" | Vector search (`product_index`) | Semantic — no exact keyword match required |
| "What's our return policy?" | `get_policy_details` (UC function) | Exact/substring match against a fixed list of 6 policies — a semantic index adds noise here, not value |
| "What did customer Robert Butler contact us about?" | `get_customer_service_history` (UC function) | Exact identifier lookup, not a similarity search |

This is also exactly why the deployed agent in `05_agent_creation/` is a **tool-calling** agent rather than a single RAG pipeline — it picks the right retrieval mechanism per question instead of forcing every question through one index.

## Grounding Discipline

`02_rag_retrieval_demo.py`'s system prompt requires the model to answer only from retrieved context and explicitly decline when the context doesn't support an answer — the same standard this repo's root CLAUDE.md sets for the HR use case ("do not infer policy beyond the retrieved material"), applied here to the product catalog. The notebook's Step 4 tests this directly with an off-domain question ("What is the capital of France?") and asserts the model didn't fall back on outside knowledge.

## Running It

All five notebooks are read-only against existing infrastructure except `01_build_agent_tools.py`'s `CREATE OR REPLACE FUNCTION` calls, which are idempotent and safe to re-run (both functions already exist with this exact definition). None of 02–05 create persistent tables or indexes.

1. `01_build_agent_tools.py` — confirmed both UC functions live with real query results (Return Policy row; 2 real Robert Butler interaction rows).
2. `02_rag_retrieval_demo.py` — retrieval, grounded generation, and the refusal check, all confirmed above.
3. `03_chunking_tradeoffs.py`, `04_metadata_filtered_retrieval.py`, `05_hybrid_retrieval_demo.py` — each independent, all confirmed above.

## Evidence

See [`screenshots/`](screenshots/) for the capture checklist.
