# Workforce Insights and HR Policy Assistant

## Repository Scope

This repository hosts a series of standalone FDE assignment exercises, numbered as top-level folders (`01_claude_code/`, `02_genie_space/`, `03_vector_database/`, `04_rag/`, `05_agent_creation/`, `06_databricks_app/`, ...). This CLAUDE.md describes the **Workforce Insights and HR Policy Assistant** product — the primary use case, built on the synthetic HR data under `shared_data/`, and the one `01_claude_code/` implements end to end.

Starting with `02_genie_space/`, later assignments intentionally pivoted to a different use case: a pre-existing product-catalog/customer-service dataset already in Unity Catalog (`uc_agentic_ai.agentic_ai_schema` — `products`, `product_master`, `product_details`, `policies`, `cust_service_data`), rather than ingesting the workforce CSVs. That dataset's raw source files (CSVs and the 509 source PDFs behind `product_details`) live under `product_catalog_data/` — see its own README for row counts and provenance. `03_vector_database/`, `04_rag/`, `05_agent_creation/`, and `06_databricks_app/` continue on that same product-catalog dataset for consistency, rather than switching use cases per assignment. `05_agent_creation/` documents a tool-calling agent already built and deployed live in the workspace; `06_databricks_app/` documents a chat UI (its code lives in `06_databricks_app/app/`) that fronts that same deployed agent endpoint. When an assignment folder diverges from the Workforce Insights use case like this, its own `README.md` documents the use case and data source it actually used — treat that folder's README as authoritative for that folder, and this file as authoritative for the Workforce Insights use case and for engineering/collaboration standards that apply repo-wide.

## Product Purpose

Help HR analysts and department managers explore governed workforce information and find reliable answers in the company's HR procedures.

## Users and Capabilities

- HR analysts explore employee counts and distributions by department, location, and employment status.
- Department managers ask workforce questions using data they are authorized to access.
- HR staff search onboarding and leave-request procedures.
- Procedure answers cite the source document and relevant section. If the approved sources do not support an answer, say so clearly.
- The system supports information access; it does not make employment, leave-eligibility, or other personnel decisions.

## Data and Knowledge Sources

- `shared_data/tables/employees.csv` contains `employee_id`, `department_id`, `job_title`, `location`, `hire_date`, and `employment_status`.
- `shared_data/tables/departments.csv` contains `department_id` and `department_name`.
- `shared_data/documents/` contains the onboarding and leave-request guides in PDF and editable HTML form.
- Current workforce data is synthetic. Do not add real employee personal information, compensation data, or credentials.
- Employment-status values include `Active`, `On Leave`, and `Former`. Confirm the business definition of metrics such as active headcount before encoding it.

## Solution Architecture

- Unity Catalog and Delta tables provide governed workforce data.
- Databricks Genie supports natural-language workforce analytics.
- Databricks Vector Search retrieves relevant HR procedure content.
- Retrieval-Augmented Generation grounds procedure answers in retrieved source passages.
- An agent routes questions to analytics or document retrieval and reports tool failures clearly.
- A Databricks App provides the user interface and respects underlying access controls.

## Engineering Standards

- Inspect existing schemas and resources before proposing changes; do not guess workspace-specific identifiers.
- Validate files, schemas, identifiers, dates, status values, and employee-to-department references before ingestion.
- Define metrics explicitly and test edge cases, including employees on leave and former employees.
- Apply least-privilege access through the governed data layer. Do not treat application filtering as a substitute for data permissions.
- Keep source citations attached to policy answers and do not infer policy beyond the retrieved material.
- Handle errors explicitly. Logs and screenshots must not expose secrets or unnecessary employee-level data.
- Run focused checks after changes and distinguish verified results from assumptions.

## Collaboration

The project owner is an expert Data Engineer and AI Engineer. Communicate as a technical peer, explain relevant design trade-offs, and keep guidance concise. Make scoped changes when requested; obtain approval before cloud writes, data ingestion, deployment, permission changes, or external GitHub modifications.