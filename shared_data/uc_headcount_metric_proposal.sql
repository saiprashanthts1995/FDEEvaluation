-- Unity Catalog / Delta proposal for governed workforce tables and the active-headcount metric.
-- PROPOSAL ONLY — not executed. Requires explicit approval and confirmed catalog/schema
-- identifiers from the target Databricks workspace before any of this is run.
--
-- <catalog> and <schema> are placeholders (see CLAUDE.md: "do not guess workspace-specific
-- identifiers"). Replace them after inspecting the actual workspace with the account owner.
--
-- Source of truth for schema and metric semantics: shared_data/data_contract.md
-- (confirmed with data owner 2026-09-27: Active headcount excludes On Leave).

-- 1. Governed base tables (sourced from shared_data/tables/*.csv during ingestion)

CREATE TABLE IF NOT EXISTS <catalog>.<schema>.departments (
  department_id   STRING NOT NULL COMMENT 'Primary key.',
  department_name STRING NOT NULL
)
USING DELTA
COMMENT 'Governed department reference table. Synthetic data only.';

CREATE TABLE IF NOT EXISTS <catalog>.<schema>.employees (
  employee_id       STRING NOT NULL COMMENT 'Primary key.',
  department_id     STRING NOT NULL COMMENT 'References departments.department_id.',
  job_title         STRING NOT NULL,
  location          STRING NOT NULL,
  hire_date         DATE   NOT NULL,
  employment_status STRING NOT NULL COMMENT 'One of: Active, On Leave, Former.'
)
USING DELTA
COMMENT 'Governed employee table. Synthetic data only — no real PII or compensation data.';

-- Delta does not enforce FOREIGN KEY constraints by default; document the relationship
-- and validate it at ingestion time instead (see .claude/skills/employee-data-onboarding).
ALTER TABLE <catalog>.<schema>.employees
  ADD CONSTRAINT employees_department_id_fk
  FOREIGN KEY (department_id) REFERENCES <catalog>.<schema>.departments (department_id)
  NOT ENFORCED;

-- 2. Headcount metric view
--
-- Reports Active, On Leave, and Former as distinct counts per the confirmed contract —
-- never blended into a single "active" number. `active_headcount` = Active only.

CREATE OR REPLACE VIEW <catalog>.<schema>.v_workforce_headcount AS
SELECT
  d.department_id,
  d.department_name,
  e.location,
  COUNT(*) FILTER (WHERE e.employment_status = 'Active')   AS active_headcount,
  COUNT(*) FILTER (WHERE e.employment_status = 'On Leave') AS on_leave_count,
  COUNT(*) FILTER (WHERE e.employment_status = 'Former')   AS former_count,
  COUNT(*)                                                 AS total_records
FROM <catalog>.<schema>.employees e
JOIN <catalog>.<schema>.departments d
  ON e.department_id = d.department_id
GROUP BY d.department_id, d.department_name, e.location;

-- Notes for Genie / downstream consumers:
-- - "Active headcount" in natural-language questions should map to active_headcount,
--   never to total_records or active_headcount + on_leave_count.
-- - Former employees remain queryable (e.g. for attrition analysis) via the base
--   employees table, not through this headcount view, and must stay labeled by
--   employment_status wherever surfaced.
