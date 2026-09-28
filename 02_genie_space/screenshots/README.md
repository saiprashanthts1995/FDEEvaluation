# Genie Space Evidence Screenshots

Genuine screenshots from the Databricks workspace session, in workflow order.

| Filename | Evidence |
|---|---|
| `01-policy-question-answer.png` | NL question "What are the distinct policy names and their counts in the policies table?" answered correctly (6 distinct policies) against the `policies` table. |
| `02-product-category-sql.png` | Follow-up NL question ("list the products and count based on category and draw a visualisation") with the Genie-generated SQL shown and verified — a `GROUP BY product_category` query against `uc_agentic_ai.agentic_ai_schema.products`. |
| `03-product-category-summary.png` | Full result set and Genie's natural-language summary (93 distinct categories, 551 products, top 5 ranked). |
| `04-product-category-visualization.png` | Auto-generated bar chart visualization for the same query. |
| `05-genie-agents-list.png` | Genie Agents list showing the space ("Product Catalog and Customer Service") alongside pre-existing agents in the workspace, confirming it's saved and owned correctly. |
| `06-genie-one-table-summary.png` | Genie One (cross-agent assistant) asked "What tables are there and how are they connected?" and correctly describing the schema/joins across all 6 tables. |
| `07-space-instructions.png` | The Genie Space's **Configure → Instructions** panel showing table/column descriptions and sample instructions saved (closes the metadata gap noted in the main README). |
| `08-genie-api-conversation.png` | `notebooks/genie_api_conversation.py` run end-to-end — conversation started, SQL + results retrieved, follow-up answered in the same conversation, all via the API. |
| `09-break-and-fix-before.png` | An ambiguous question (e.g. "what's popular?") producing a wrong/confused answer, before any instruction was added. |
| `10-break-and-fix-after.png` | The same question after adding a defining instruction in Configure → Instructions, now answered correctly. |
| `11-row-filter-applied.png` | `row_level_security.py` run with `APPLY_ROW_FILTER = True` — the function created, the `ALTER TABLE ... SET ROW FILTER` succeeding, and Section 3's owner query still returning all rows. |
| `12-governance-full-access.png` | Your own (full-access) answer to a question touching `cust_service_data`, after the filter is applied. |
| `13-governance-restricted-access.png` | The same question asked by a restricted second identity — should return zero rows / fail, not silently return everything. **Optional** if a second identity isn't available to you; note in the PR/commit if skipped rather than leaving it silently unaddressed. |

Note: the browser address bar is visible in these screenshots and shows the workspace hostname and numeric org id — not a secret, but avoid capturing anything with an auth token or PAT in the URL or headers in future screenshots.
