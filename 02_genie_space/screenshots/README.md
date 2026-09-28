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
| `08-genie-api-start-conversation.png` | `notebooks/genie_api_conversation.py` §1 — conversation started via the SDK, conversation/message IDs and `COMPLETED` status printed. |
| `09-genie-api-sql-and-results.png` | §2 — the generated SQL and result pulled from the message attachment (not just the natural-language summary), confirming the API returns a reviewable query, same discipline as the manual UI evidence. |
| `10-genie-api-followup.png` | §3 — a follow-up asked in the same conversation ("now do the same thing but for products grouped by category"), correctly carrying context without repeating "in the policies table." |
| `11-row-filter-applied.png` | `row_level_security.py` run with `APPLY_ROW_FILTER = True` — the function created, the `ALTER TABLE ... SET ROW FILTER` succeeding, and the owner's query still returning all rows. |
| `12-break-and-fix.png` | Both halves of the ambiguity fix in one conversation: asking "What's popular?" without the instruction produces a response that can't commit to a data-backed answer ("Without the query results, I cannot provide a data-backed answer... would you like me to wait, or a different approach?"); after the `'Top'/'popular'` instruction was saved (see `07-space-instructions.png`), re-asking produces a definitive, correctly-grounded breakdown by `cust_service_data` interaction count (Billing 213, Account Management 205, Product Inquiry 202, ...). |
| `13-governance-full-access.png` | Your own (full-access) answer to "tell me how much record count in cust_service_data" — correctly returns all 1,023 records post-filter. |

That's all 13 screenshots this workspace can produce. A 14th ("restricted second identity") isn't achievable here — this is a single-identity Databricks workspace with no second user/service principal to test against — and is documented as a known open item in the main `README.md` rather than silently left off this list.

Note: the browser address bar is visible in these screenshots and shows the workspace hostname and numeric org id — not a secret, but avoid capturing anything with an auth token or PAT in the URL or headers in future screenshots.
