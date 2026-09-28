# Product Catalog Source Data

The raw data behind `uc_agentic_ai.agentic_ai_schema` — the Unity Catalog schema every assignment from `02_genie_space/` onward builds on. Previously only inspected live in the Databricks workspace; copied here so the pipeline's actual source data is preserved in this repo, not just its outputs.

## Contents

```
tables/
  products.csv            553 rows — product_id, product_name, product_category, product_sub_category
  policies.csv             6 rows  — policy, policy_details, last_updated
  cust_service_data.csv 1,023 rows — customer_id, name, email, phone_number, address, interaction_id, date_time, issue_category, issue_description, agent_id
documents/
  product_docs/           509 PDFs — one per product, parsed by 03_vector_database/notebooks/01_build_product_master_and_index.py via ai_parse_document into product_details
```

Row counts here match what was independently confirmed against the live workspace throughout this project (553 products, 6 policies, 1,023 customer service records, 509 PDFs) — this is the actual source, not a re-export.

## `cust_service_data.csv`: synthetic, not real customer data

Names, emails (`@example.com`/`@example.net`), phone numbers, and addresses are Faker-style generated values, not real people — confirmed before this data was ever used in `02_genie_space/`, `04_rag/`, or `05_agent_creation/`. Still handled with the same care as if it weren't: the row filter in `02_genie_space/notebooks/row_level_security.py` restricts `cust_service_data` to the table owner in the live workspace regardless of the underlying data being synthetic, since least-privilege access shouldn't depend on trusting that every dataset stays synthetic forever.

## What Actually Used This

- `03_vector_database/` — `product_docs/` → `ai_parse_document` → `product_details`; joined with `products.csv`'s live table counterpart into `product_master`.
- `02_genie_space/`, `04_rag/` — `policies.csv` and `cust_service_data.csv`'s live table counterparts, queried directly and via `get_policy_details`/`get_customer_service_history`.
- `05_agent_creation/` — all of the above, through the deployed agent's three tools.

This folder is the data at rest; the live Unity Catalog tables are the governed, queryable version every notebook in this repo actually reads from.
