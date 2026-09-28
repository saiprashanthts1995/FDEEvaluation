# Databricks notebook source
# MAGIC %md
# MAGIC # Row-Level Security on `cust_service_data`
# MAGIC
# MAGIC Builds the row filter half of the "Governance Validation" scenario for this
# MAGIC Genie Space: a Unity Catalog function keyed on `current_user()`, applied to a
# MAGIC table via `ALTER TABLE ... SET ROW FILTER`. Applied here to `cust_service_data`,
# MAGIC which is the one table in this project with PII-shaped columns (name, email,
# MAGIC phone, address — confirmed synthetic in `02_genie_space/README.md`, but still
# MAGIC the right table to actually demonstrate governance on).
# MAGIC
# MAGIC **This is a real permission change to a live table.** Per this repo's
# MAGIC CLAUDE.md ("obtain approval before... permission changes"), it is **not
# MAGIC applied automatically** — every cell that alters `cust_service_data` is
# MAGIC disabled by default (`APPLY_ROW_FILTER = False`). Review the filter logic
# MAGIC below and flip it on deliberately.
# MAGIC
# MAGIC **What this notebook can't do on its own:** actually *testing* the filter
# MAGIC requires a second Databricks identity without full access — that's still your
# MAGIC job, same as noted in `02_genie_space/README.md`'s "Still Needs Your Hands"
# MAGIC section. This notebook gets the filter built and gives you the exact query to
# MAGIC run as that second identity.

# COMMAND ----------

catalog = "uc_agentic_ai"
schema = "agentic_ai_schema"
owner_email = "saiprashanthts@gmail.com"  # confirmed via Unity Catalog API — the owner of every table in this schema

APPLY_ROW_FILTER = False  # set True deliberately after reviewing the filter logic below

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. The row filter function
# MAGIC
# MAGIC The owner sees everything. Anyone else sees only their own name's rows —
# MAGIC deliberately restrictive rather than permissive-by-default, so a
# MAGIC misconfigured or newly-granted principal fails closed (sees nothing) instead
# MAGIC of accidentally failing open (sees everything). Adjust the `ELSE` branch if a
# MAGIC broader access tier (e.g. "all support agents see all rows, everyone else
# MAGIC sees none") fits your actual access model better — this is a starting
# MAGIC pattern, not the only correct one.

# COMMAND ----------

if APPLY_ROW_FILTER:
    spark.sql(f"""
    CREATE OR REPLACE FUNCTION {catalog}.{schema}.cust_service_row_filter(row_name STRING)
    RETURNS BOOLEAN
    RETURN
      CASE
        WHEN current_user() = '{owner_email}' THEN TRUE
        ELSE FALSE
      END
    """)
    print(f"Created {catalog}.{schema}.cust_service_row_filter")
else:
    print("APPLY_ROW_FILTER is False — no function created. Flip to True to apply.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Apply it to `cust_service_data`

# COMMAND ----------

if APPLY_ROW_FILTER:
    spark.sql(f"""
    ALTER TABLE {catalog}.{schema}.cust_service_data
    SET ROW FILTER {catalog}.{schema}.cust_service_row_filter
    ON (name)
    """)
    print(f"Row filter applied to {catalog}.{schema}.cust_service_data")
else:
    print("APPLY_ROW_FILTER is False — no table altered.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Verify as the owner (should see all rows)

# COMMAND ----------

if APPLY_ROW_FILTER:
    display(spark.sql(f"SELECT COUNT(*) AS visible_rows FROM {catalog}.{schema}.cust_service_data"))
else:
    print("Run Sections 1-2 first.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. What to run as a second, restricted identity
# MAGIC
# MAGIC Grant a second user/service principal `SELECT` on
# MAGIC `{catalog}.{schema}.cust_service_data` (and `USE CATALOG`/`USE SCHEMA` on the
# MAGIC parents), have them run the same query as Section 3, and screenshot both
# MAGIC results side by side:
# MAGIC
# MAGIC ```sql
# MAGIC SELECT COUNT(*) AS visible_rows FROM uc_agentic_ai.agentic_ai_schema.cust_service_data;
# MAGIC ```
# MAGIC
# MAGIC Expected: the owner sees all rows; the second identity sees 0 (since the
# MAGIC filter's `ELSE` branch returns `FALSE` for anyone whose email doesn't match
# MAGIC any `name` value in the table — which, realistically, is everyone but the
# MAGIC owner, since `name` holds customer names, not employee emails). That's the
# MAGIC actual governance proof: Unity Catalog enforcing the restriction, not the
# MAGIC application pretending to filter results it already fetched.
# MAGIC
# MAGIC Then repeat through the Genie Space in `02_genie_space/` itself — ask it a
# MAGIC question touching `cust_service_data` as both identities, and confirm Genie's
# MAGIC answer reflects the same restriction rather than bypassing it (this is the
# MAGIC actual test CLAUDE.md's "respects underlying access controls" principle
# MAGIC requires — application-layer filtering is not a substitute for this).

# COMMAND ----------

# MAGIC %md
# MAGIC ## To remove the filter later

# COMMAND ----------

# MAGIC %md
# MAGIC ```sql
# MAGIC ALTER TABLE uc_agentic_ai.agentic_ai_schema.cust_service_data DROP ROW FILTER;
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC - Every write in this notebook is gated behind `APPLY_ROW_FILTER` — nothing
# MAGIC   executes just by running the cells top to bottom without flipping it.
# MAGIC - This changes real access to `cust_service_data` for every future query
# MAGIC   against it, including from `04_rag/`'s `get_customer_service_history`
# MAGIC   function and `05_agent_creation/`'s deployed agent — expect those to also
# MAGIC   start seeing restricted results once this filter is live, since Unity
# MAGIC   Catalog enforcement applies regardless of the calling path (that's the
# MAGIC   point).
