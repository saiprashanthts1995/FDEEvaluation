# Workforce Insights and HR Policy Assistant

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