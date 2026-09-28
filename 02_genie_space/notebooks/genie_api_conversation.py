# Databricks notebook source
# MAGIC %md
# MAGIC # Programmatic Access: Genie Conversation API
# MAGIC
# MAGIC Demonstrates using the Genie Space entirely through the REST API — no UI —
# MAGIC to start a conversation, ask a follow-up, and retrieve the generated SQL and
# MAGIC results. This is the read-only equivalent of the manual chat evidence in
# MAGIC `01-policy-question-answer.png` / `02-product-category-sql.png`, done
# MAGIC programmatically instead, which is what a real integration (an app, another
# MAGIC agent) would actually call.
# MAGIC
# MAGIC Space ID confirmed live via `GET /api/2.0/genie/spaces` before writing this —
# MAGIC not guessed.

# COMMAND ----------

import time

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

SPACE_ID = "01f1bae472291ce6bf70a6de27869978"  # "Product Catalog and Customer Service"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Start a conversation

# COMMAND ----------

def poll_until_complete(space_id: str, conversation_id: str, message_id: str, timeout_s: int = 60):
    start = time.time()
    while time.time() - start < timeout_s:
        msg = w.genie.get_message(space_id=space_id, conversation_id=conversation_id, message_id=message_id)
        if msg.status.value in ("COMPLETED", "FAILED", "CANCELLED"):
            return msg
        time.sleep(2)
    raise TimeoutError(f"Message {message_id} did not complete within {timeout_s}s")


first = w.genie.start_conversation_and_wait(
    space_id=SPACE_ID,
    content="What are the distinct policy names and their counts in the policies table?",
)

print(f"Conversation ID: {first.conversation_id}")
print(f"Message ID:      {first.message_id}")
print(f"Status:          {first.status.value}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Retrieve the generated SQL and results
# MAGIC
# MAGIC Genie attaches query results as message attachments — this pulls the SQL text
# MAGIC and the result rows, not just the natural-language summary, so the generated
# MAGIC query can actually be reviewed (same discipline as the manual UI evidence).

# COMMAND ----------

def extract_sql_and_results(message):
    for attachment in message.attachments or []:
        if attachment.query is not None:
            print("Generated SQL:")
            print(attachment.query.query)
            result = w.genie.get_message_query_result(
                space_id=SPACE_ID,
                conversation_id=message.conversation_id,
                message_id=message.id,
            )
            print("\nResult:")
            print(result.statement_response.result)
        elif attachment.text is not None:
            print("Text response:")
            print(attachment.text.content)


extract_sql_and_results(first)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Ask a follow-up in the same conversation
# MAGIC
# MAGIC Confirms conversational context carries over via the API the same way it does
# MAGIC in the UI — the follow-up doesn't repeat "in the policies table," relying on
# MAGIC the prior turn for that context.

# COMMAND ----------

follow_up = w.genie.create_message_and_wait(
    space_id=SPACE_ID,
    conversation_id=first.conversation_id,
    content="Now do the same thing but for products grouped by category.",
)

print(f"Status: {follow_up.status.value}")
extract_sql_and_results(follow_up)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Notes
# MAGIC
# MAGIC - Fully read-only — no space configuration, tables, or permissions were
# MAGIC   changed by this notebook.
# MAGIC - This is the mechanism `06_databricks_app/`'s chat UI (or any other custom
# MAGIC   application) would use to embed Genie rather than sending users to the
# MAGIC   Databricks workspace UI directly.
# MAGIC - If `start_conversation_and_wait` raises a permission error, that's exactly
# MAGIC   the governance behavior to screenshot for the "governance validation"
# MAGIC   scenario in this folder's README — a different user identity without
# MAGIC   access to the underlying tables should see a similar failure, not a partial
# MAGIC   or silently-wrong answer.
