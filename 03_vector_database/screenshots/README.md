# Vector Database Evidence Screenshots

Save genuine screenshots from the Databricks workspace session in this folder. Use the filenames below so the evidence is easy to review in workflow order.

| Filename | Evidence |
|---|---|
| `01-product-details-parsed.png` | `product_details` table in Catalog Explorer, or the notebook's Step 1 output showing 509 rows parsed via `ai_parse_document`. |
| `02-product-master-join.png` | `product_master` table / notebook Step 2 output — 553 rows, all with non-null `product_desc`. |
| `03-index-detail.png` | `uc_agentic_ai.agentic_ai_schema.product_index` in Catalog Explorer / Vector Search UI, showing status `ONLINE`, source table `product_master`, embedding column `product_combined`. |
| `04-source-health-check.png` | Verification notebook Step 1 output: row count, distinct categories, zero empty/null rows. |
| `05-sync-freshness-check.png` | Verification notebook Step 2 output: indexed row count vs. live table row count, last sync timestamp. |
| `06-retrieval-sanity-check.png` | Verification notebook Step 3 output: the product queries with returned products, categories, and similarity scores visible. |
| `07-freshness-test.png` | `03_advanced_scenarios.py` §1 output — the test row's insert-to-searchable latency measurement, and confirmation it was cleaned up. |
| `08-filtered-search.png` | §2 output — the unfiltered vs. `product_category`-filtered results side by side, with the assertion passing. |
| `09-index-type-comparison.png` | §3 output — the Direct Vector Access demo index created and queried, next to the Delta Sync `product_index` for comparison. |
| `10-query-tuning.png` | §4 output — `top_k=3` vs `top_k=15` results and score ranges for the same query. |

Only mark evidence complete when the corresponding screenshot exists and shows the actual session result. Do not create placeholder images or invent similarity scores.
