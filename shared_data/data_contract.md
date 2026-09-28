# Workforce Data Contract

Governs `shared_data/tables/employees.csv` and `shared_data/tables/departments.csv`. Synthetic data only — no real employee PII, compensation, or credentials. This contract is the reference for any Unity Catalog table definition, Genie question, or metric built on top of these sources.

## Schemas

### `departments`

| Column | Type | Constraints |
|---|---|---|
| `department_id` | string | Primary key, non-null, unique |
| `department_name` | string | Non-null |

Current rows: 4 (`D001` People Operations, `D002` Engineering, `D003` Sales, `D004` Customer Support).

### `employees`

| Column | Type | Constraints |
|---|---|---|
| `employee_id` | string | Primary key, non-null, unique |
| `department_id` | string | Non-null, foreign key → `departments.department_id` |
| `job_title` | string | Non-null |
| `location` | string | Non-null |
| `hire_date` | date | Non-null, ISO 8601 (`YYYY-MM-DD`) |
| `employment_status` | string | Non-null, enum: `Active`, `On Leave`, `Former` |

Current rows: 12. Validated: no duplicate IDs, no empty required fields, every `department_id` resolves, all dates are ISO, all statuses are in the enum. Locations (5: Austin, Chicago, Denver, Portland, Seattle) and job titles (11 distinct) have no duplicate/variant spellings.

## Key Relationship

`employees.department_id` is a many-to-one foreign key to `departments.department_id`. Every department currently has employees (3 each); no orphaned employee rows.

## Employment Status Semantics (confirmed with data owner, 2026-09-27)

- **`Active`** — currently employed and working.
- **`On Leave`** — currently employed, temporarily away (e.g., medical, parental).
- **`Former`** — no longer employed.

## Metric Definitions

- **Active headcount** = `count(employment_status == 'Active')`. **`On Leave` is excluded from this metric** — it is reported as its own separate count, not folded into "active."
- **On Leave count** = `count(employment_status == 'On Leave')`, reported as a distinct metric alongside active headcount, not merged into it.
- **Former employees** remain queryable through analytics (e.g., for tenure/attrition analysis) rather than being excluded from the governed dataset. Every query result or UI surface that includes `Former` records must label `employment_status` explicitly so they are never mistaken for current staff.
- **Headcount by department / location** — use the same status-based breakdown (Active, On Leave, Former reported distinctly) rather than a single blended count, unless a specific question calls for a defined combination.

## Open Items for Later Phases

- Governed analytics (Unity Catalog table DDL, Genie question set) has not been proposed yet — requires this contract plus explicit approval before any workspace write.
- Document retrieval and grounded-answer phases are out of scope for this contract and covered separately under `shared_data/documents/`.
