# Vector Database Evidence Screenshots

Save genuine screenshots from the Databricks workspace session in this folder. Use the filenames below so the evidence is easy to review in workflow order.

| Filename | Evidence | Status |
|---|---|---|
| `01-product-details-parsed.png` | `product_details` table in Catalog Explorer, or the notebook's Step 1 output showing 509 rows parsed via `ai_parse_document`. | Needed |
| `02-product-master-join.png` | `product_master` in Catalog Explorer, Sample Data tab — real rows including the `product_combined` embedding-source column. | Done |
| `03-index-detail.png` | `product_index` Overview tab in Catalog Explorer — Index status `Online`, type `Delta Sync`, source table `product_master`, serving endpoint `ai_search_endpoint`, 553 rows indexed. | Done |
| `04-source-health-check.png` | Health check output: row count 553, distinct categories 93, zero empty/null rows. | Done |
| `05-sync-freshness-check.png` | Verification notebook Step 2 output: indexed row count vs. live table row count, last sync timestamp. | Needed |
| `06-retrieval-sanity-check.png` | Retrieval against `product_index` for "wireless noise-cancelling headphones" — real products and scores returned. | Done |
| `07-freshness-test.png` | `03_advanced_scenarios.py` §1 output — the test row's insert-to-searchable latency measurement, and confirmation it was cleaned up. | Needed — skipped by the lightweight path since it writes a test row; run deliberately if you want this scenario covered. |
| `08-filtered-search.png` | Unfiltered vs. `product_category`-filtered results side by side (Electronics), with the assertion passing. | Done |
| `09-index-type-comparison.png` | §3 output — the Direct Vector Access demo index created and queried, next to the Delta Sync `product_index` for comparison. | Needed — skipped by the lightweight path since it creates a second index; optional. |
| `10-query-tuning.png` | `top_k=3` vs `top_k=15` results and score ranges for "comfortable running shoes". | Done |

Only mark evidence complete when the corresponding screenshot exists and shows the actual session result. Do not create placeholder images or invent similarity scores.

Notes:
- `02`, `03`, and `06`'s current images were captured against this same live `product_index`/`product_master` earlier in this project's work (Catalog Explorer's own Sample Data and Query Index tools) rather than from a notebook in this folder — still genuine screenshots of the real objects.
- `04`, `06`, `08`, `10` come from [`../lightweight_evidence_3_4_5.py`](../../lightweight_evidence_3_4_5.py), run via plain REST calls (no `%pip install`, written for free-tier serverless quota constraints). `01`, `05`, `07`, `09` weren't covered by that lightweight path — `01` and `05` need the full `01_build_product_master_and_index.py`/`02_verify_product_vector_index.py` notebooks; `07` and `09` are intentionally-skipped heavier scenarios (see `03_vector_database/README.md`'s Scenario Coverage).
