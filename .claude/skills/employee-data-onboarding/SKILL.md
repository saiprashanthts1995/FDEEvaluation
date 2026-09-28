---
name: employee-data-onboarding
description: "Validate the synthetic employees and departments CSV files and prepare a safe, traceable handoff for governed ingestion. Use when reviewing employee data, schemas, data quality, or onboarding these tables."
---

# Employee Data Onboarding

1. Inspect `shared_data/tables/employees.csv` and `shared_data/tables/departments.csv`. Treat them as synthetic inputs and do not print full employee rows.
2. Verify the required columns:
   - Employees: `employee_id`, `department_id`, `job_title`, `location`, `hire_date`, `employment_status`.
   - Departments: `department_id`, `department_name`.
3. Check non-empty required values, unique employee and department IDs, valid employee-to-department references, ISO-formatted hire dates, and known status values. Report row numbers and field names without echoing unnecessary row data.
4. Summarize record counts and validation issues. Do not silently drop, rewrite, or infer missing data.
5. Before creating or loading Databricks tables, present the target catalog/schema, proposed table definitions, access model, and validation results. Wait for explicit approval before any workspace write.
6. After an approved load, verify table schema, row counts, key constraints, and permissions. Record the actual commands and results in the relevant project README.

Never use real employee data, expose credentials, or treat app-level filtering as a replacement for Unity Catalog permissions.