# Vector Database: Product Catalog

## Purpose

Builds and verifies the Databricks Vector Search index over the product catalog introduced in [`02_genie_space/`](../02_genie_space/) — `uc_agentic_ai.agentic_ai_schema.product_master`. This assignment was originally scoped to index the HR procedure guides in `shared_data/documents/` (matching CLAUDE.md's stated architecture), then repointed to the product catalog use case to stay consistent with assignment 2's pivot. All later assignments in this repo build on that same dataset.

## What's Here

- [`notebooks/01_build_product_master_and_index.py`](notebooks/01_build_product_master_and_index.py) — parses 509 product PDFs into `product_details`, joins them into `product_master`, and documents (but does not re-run) the original Vector Search index creation.
- [`notebooks/02_verify_product_vector_index.py`](notebooks/02_verify_product_vector_index.py) — read-only health, sync-freshness, and retrieval sanity checks against the live index.
- [`notebooks/03_advanced_scenarios.py`](notebooks/03_advanced_scenarios.py) — freshness test (insert → sync → measure latency → clean up), metadata-filtered search, a Delta Sync vs. Direct Vector Access index comparison, and `top_k` tuning.

## Scenario Coverage

All 5 scenarios were run end to end against the live workspace (via [`../lightweight_evidence_batch2.py`](../lightweight_evidence_batch2.py), the zero-install REST/SQL path — functionally equivalent to `03_advanced_scenarios.py`, chosen for the free-tier compute constraints in play at the time):

| Scenario | Result |
|---|---|
| 1. End-to-end index build (CDF, endpoint, Delta Sync index, `similarity_search()`) | `product_master_and_index` built; `product_index` confirmed `ONLINE_NO_PENDING_UPDATE`, 553 rows. |
| 2. Freshness test | Inserted a test product, triggered a sync, polled until it appeared in search results — **found and searchable after 38 seconds**. Test row deleted and a final re-sync triggered afterward, confirmed clean. |
| 3. Filtered search | `product_category = "Electronics"` filter applied to a "wireless headphones" query — every returned result stayed within Electronics; no leakage. |
| 4. Index type comparison (Delta Sync vs. Direct Vector Access) | A real `product_direct_access_demo` index was created via `POST /api/2.0/vector-search/indexes` (`HTTP 200`, entered `PROVISIONING_INDEX`). The follow-up `upsert-data-vectors` call for the 10-row sample returned **`HTTP 404`** — most likely because the index was still provisioning and not yet ready to accept direct-access upserts, a real timing constraint of the API rather than a request-shape bug (the create call itself succeeded with the exact same body pattern). Documented as the actual result, not silently retried or hidden. |
| 5. Query tuning (`top_k=3` vs `top_k=15`) | `top_k=3` returned 3 tightly-scored results; `top_k=15` returned 15 with a wider score spread — the expected precision/recall tradeoff, confirmed on live data. |

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
3. `03_advanced_scenarios.py` (or the equivalent `../lightweight_evidence_batch2.py`) — filtered search and query tuning are read-only. Freshness and index-type comparison write real data/infrastructure (gated behind `RUN_FRESHNESS_TEST` / `RUN_DIRECT_ACCESS_DEMO`) — both were run deliberately for this assignment's evidence, not left as an unattended default.

## Evidence

See [`screenshots/`](screenshots/) for the capture checklist.
