# Vector Database Evidence Screenshots

Genuine screenshots from the Databricks workspace, covering all 10 items.

| Filename | Evidence |
|---|---|
| `01-product-details-parsed.png` | `product_details` — 509 rows confirmed, sample rows shown (`AccuBooks Pro`, `AccountEase Pro`, ...). |
| `02-product-master-join.png` | `product_master` in Catalog Explorer, Sample Data tab — real rows including the `product_combined` embedding-source column. |
| `03-index-detail.png` | `product_index` Overview tab in Catalog Explorer — Index status `Online`, type `Delta Sync`, source table `product_master`, serving endpoint `ai_search_endpoint`, 553 rows indexed. |
| `04-source-health-check.png` | Health check output: row count 553, distinct categories 93, zero empty/null rows. |
| `05-sync-freshness-check.png` | Sync triggered (`HTTP 200`); indexed rows 553, live table rows 553, match `True`; last processed commit timestamp shown. |
| `06-retrieval-sanity-check.png` | Retrieval against `product_index` for "wireless noise-cancelling headphones" — real products and scores returned. |
| `07-freshness-test.png` | A test product inserted, sync triggered, polled until searchable — **found after 38 seconds**; test row deleted and re-sync triggered afterward. |
| `08-filtered-search.png` | Unfiltered vs. `product_category`-filtered results side by side (Electronics), with the assertion passing. |
| `09-index-type-comparison.png` | A real Direct Vector Access index (`product_direct_access_demo`) created via REST (`HTTP 200`, entered `PROVISIONING_INDEX`); the follow-up upsert call returned `HTTP 404` (index still provisioning) — the actual result of running this scenario against the live API, not a placeholder. |
| `10-query-tuning.png` | `top_k=3` vs `top_k=15` results and score ranges for "comfortable running shoes". |

`02`, `03`, and `06` were captured against this same live `product_index`/`product_master` via Catalog Explorer's own Sample Data and Query Index tools. Everything else was run via [`../../lightweight_evidence_batch2.py`](../../lightweight_evidence_batch2.py) (and its companion `lightweight_evidence_3_4_5.py`), the zero-install REST/SQL path used for this assignment's evidence.
