# Databricks notebook source
# /// script
# [tool.databricks.environment]
# base_environment = "databricks_ai_v5"
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Structured Retrieval Tools: Policies and Customer Service History
# MAGIC
# MAGIC These were actually created and are live today — confirmed via
# MAGIC `GET /api/2.1/unity-catalog/functions?catalog_name=uc_agentic_ai&schema_name=agentic_ai_schema`,
# MAGIC which lists both `get_policy_details` and `get_customer_service_history`.
# MAGIC
# MAGIC These pair with the unstructured vector-search retrieval in
# MAGIC `02_rag_retrieval_demo.py`: the vector index answers "what product matches this
# MAGIC description," while these two Unity Catalog functions answer exact-match lookups
# MAGIC a semantic index is the wrong tool for — "what's our return policy" (keyword
# MAGIC match on a short, fixed list of six policies) and "what did this customer
# MAGIC contact us about" (an exact ID/email/name lookup, not a similarity search).

# COMMAND ----------

catalog = "uc_agentic_ai"
schema = "agentic_ai_schema"

spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## `get_policy_details`
# MAGIC
# MAGIC Case-insensitive substring match against the 6 policies in the `policies`
# MAGIC table (see `02_genie_space/` for how those were originally explored).

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION {catalog}.{schema}.get_policy_details(
  policy_name STRING COMMENT 'Name or keyword of the policy to search for, e.g. "return policy" or "warranty"'
)
RETURNS TABLE (policy STRING, policy_details STRING, last_updated DATE)
COMMENT 'Looks up company policy details by policy name or keyword.'
RETURN
  SELECT policy, policy_details, last_updated
  FROM {catalog}.{schema}.policies
  WHERE lower(policy) LIKE lower(concat('%', policy_name, '%'))
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## `get_customer_service_history`
# MAGIC
# MAGIC Looks up a customer's past interactions by id, email, or name. Recall from
# MAGIC `02_genie_space/README.md`: `cust_service_data` was confirmed synthetic/demo
# MAGIC data before being wired into any tool, since it has PII-shaped columns.

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION {catalog}.{schema}.get_customer_service_history(
  customer_identifier STRING COMMENT 'Customer id, email, or name to search for'
)
RETURNS TABLE (
  customer_id STRING,
  name STRING,
  email STRING,
  interaction_id STRING,
  date_time TIMESTAMP,
  issue_category STRING,
  issue_description STRING,
  agent_id BIGINT
)
COMMENT 'Looks up a customer''s past service interactions by customer id, email, or name.'
RETURN
  SELECT customer_id, name, email, interaction_id, date_time, issue_category, issue_description, agent_id
  FROM {catalog}.{schema}.cust_service_data
  WHERE customer_id = customer_identifier
     OR lower(email) = lower(customer_identifier)
     OR lower(name) LIKE lower(concat('%', customer_identifier, '%'))
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Quick tests

# COMMAND ----------

display(spark.sql(f"SELECT * FROM {catalog}.{schema}.get_policy_details('return')"))

# COMMAND ----------

display(spark.sql(f"SELECT * FROM {catalog}.{schema}.get_customer_service_history('Robert Butler')"))