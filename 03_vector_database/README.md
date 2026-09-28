# Vector Database: Product Catalog

## Purpose

Builds and verifies the Databricks Vector Search index over the product catalog introduced in [`02_genie_space/`](../02_genie_space/) — `uc_agentic_ai.agentic_ai_schema.product_master`. This assignment was originally scoped to index the HR procedure guides in `shared_data/documents/` (matching CLAUDE.md's stated architecture), then repointed to the product catalog use case to stay consistent with assignment 2's pivot. All later assignments in this repo build on that same dataset.

## What's Here

- [`notebooks/01_build_product_master_and_index.py`](notebooks/01_build_product_master_and_index.py) — parses 509 product PDFs into `product_details`, joins them into `product_master`, and documents (but does not re-run) the original Vector Search index creation. Ported from the notebook that actually built this: [`saiprashanthts1995/databricks_agentic_ai/02_Notebooks/Build_RAG_Agent_Tables.py`](https://github.com/saiprashanthts1995/databricks_agentic_ai/blob/main/02_Notebooks/Build_RAG_Agent_Tables.py).
- [`notebooks/02_verify_product_vector_index.py`](notebooks/02_verify_product_vector_index.py) — read-only health, sync-freshness, and retrieval sanity checks against the live index.
- [`notebooks/03_advanced_scenarios.py`](notebooks/03_advanced_scenarios.py) — freshness test (insert → sync → measure latency → clean up), metadata-filtered search, a Delta Sync vs. Direct Vector Access index comparison, and `top_k` tuning.

## Scenario Coverage

| Scenario | Status |
|---|---|
| 1. End-to-end index build (CDF, endpoint, Delta Sync index, `similarity_search()`) | Done — `01_build_product_master_and_index.py` + the live `product_index` verified in `02_verify_product_vector_index.py`. |
| 2. Freshness test | Done — `03_advanced_scenarios.py` §1. Disabled by default (`RUN_FRESHNESS_TEST = False`) since it writes a test row, even though it cleans up after itself. |
| 3. Filtered search | Done — `03_advanced_scenarios.py` §2, filters to `product_category = "Electronics"` with an assertion that no other category leaked through. |
| 4. Index type comparison (Delta Sync vs. Direct Vector Access) | Done — `03_advanced_scenarios.py` §3, a real 10-row Direct Access index built for comparison. Disabled by default (`RUN_DIRECT_ACCESS_DEMO = False`) since it creates a second index. |
| 5. Query tuning (`top_k=3` vs `top_k=15`) | Done — `03_advanced_scenarios.py` §4. |

## What's Actually Live (verified read-only before writing any of this)

| | |
|---|---|
| Source PDFs | 509 files at `/Volumes/uc_agentic_ai/agentic_ai_schema/data_files/01_Data_Files/product_docs/` — confirmed via `SELECT COUNT(*) FROM READ_FILES(...)` |
| `product_details` | 509 rows, `(product_name, product_desc)`, parsed via `ai_parse_document` |
| `product_master` | 553 rows, `product_details` joined on a normalized `product_name` (colon → underscore, matching how PDF filenames were saved) |
| Index | `uc_agentic_ai.agentic_ai_schema.product_index` |
| Endpoint | `ai_search_endpoint` (STANDARD, ONLINE) |
| Embedding column / model | `product_combined` / `databricks-qwen3-embedding-0-6b` |
| Index type | `DELTA_SYNC`, `TRIGGERED`, subtype `HYBRID` (keyword + vector) |
| Status | `ONLINE_NO_PENDING_UPDATE`, 553 rows indexed — matches the live `product_master` row count |

## A Real Discrepancy (documented, not hidden)

The original notebook's Step 3 targets a **different** index name/endpoint/embedding model than what's actually deployed:

| | Original script | Actually live |
|---|---|---|
| Endpoint | `agentic_ai_vs_endpoint` (new) | `ai_search_endpoint` (existing) |
| Index name | `product_master_index` | `product_index` |
| Embedding model | `databricks-gte-large-en` | `databricks-qwen3-embedding-0-6b` |

Most likely this script was an earlier draft and the index was later (re)created through the Catalog Explorer UI with different settings. Both approaches produce a valid `DELTA_SYNC` index over the same `product_master.product_combined` column, so this isn't a functional problem — but pretending they matched would have been wrong. `01_build_product_master_and_index.py` keeps the original Step 3 code for reference (disabled by default, `RUN_INDEX_CREATION = False`) rather than silently rewriting it to match reality.

## Running It

1. `01_build_product_master_and_index.py` — Steps 1–2 (`product_details`, `product_master`) are safe to re-run (`CREATE OR REPLACE TABLE`); Step 3 (index creation) is disabled by default since the index already exists live.
2. `02_verify_product_vector_index.py` — fully read-only; run any time to confirm the live index is healthy and retrieving correctly.
3. `03_advanced_scenarios.py` — §2 (filtered search) and §4 (query tuning) are read-only and safe to run any time. §1 (freshness) and §3 (index type comparison) are disabled by default (`RUN_FRESHNESS_TEST` / `RUN_DIRECT_ACCESS_DEMO`) since they write — flip them on deliberately, not as part of an unattended run.

## Evidence

See [`screenshots/`](screenshots/) for the capture checklist.
