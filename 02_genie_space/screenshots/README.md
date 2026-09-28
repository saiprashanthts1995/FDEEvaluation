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

Note: the browser address bar is visible in these screenshots and shows the workspace hostname and numeric org id — not a secret, but avoid capturing anything with an auth token or PAT in the URL or headers in future screenshots.
