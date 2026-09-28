# Databricks notebook source
# MAGIC %md
# MAGIC # Tool-Calling Agent: Log, Evaluate, Register, Deploy
# MAGIC
# MAGIC This agent was actually logged, evaluated, registered, and deployed
# MAGIC (originally an AI Playground export). **This is not a proposal** — the model
# MAGIC it produces is live today:
# MAGIC
# MAGIC | | |
# MAGIC |---|---|
# MAGIC | UC registered model | `uc_agentic_ai.agentic_ai_schema.sai_agent_model`, version 1 |
# MAGIC | Serving endpoint | `agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model` |
# MAGIC | Status | `READY` (scaled to zero) |
# MAGIC | Task | `agent/v1/responses` |
# MAGIC
# MAGIC All confirmed via `GET /api/2.0/serving-endpoints/...` and the Unity Catalog
# MAGIC model registry API before writing this notebook — not assumed.
# MAGIC
# MAGIC `agent.py` in this same folder is the tool-calling agent this notebook logs —
# MAGIC see [`05_agent_creation/README.md`](../README.md) for its architecture and the
# MAGIC one real gap found while porting it (empty `SYSTEM_PROMPT`).

# COMMAND ----------

# MAGIC %pip install -U -qqqq backoff databricks-openai uv databricks-agents mlflow-skinny[databricks]
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md ## Test the agent
# MAGIC Interact with the agent to test its output. Since `agent.py` manually traces
# MAGIC methods within `ResponsesAgent`, you can view the trace for each step the agent
# MAGIC takes, with any LLM calls made via the OpenAI SDK automatically traced by
# MAGIC autologging.

# COMMAND ----------

from agent import AGENT

AGENT.predict(
    {"input": [{"role": "user", "content": "What's a good waterproof jacket for hiking?"}], "custom_inputs": {"session_id": "test-session-123"}},
)

# COMMAND ----------

for chunk in AGENT.predict_stream(
    {"input": [{"role": "user", "content": "What's our return policy?"}], "custom_inputs": {"session_id": "test-session-123"}}
):
    print(chunk.model_dump(exclude_none=True))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Log the `agent` as an MLflow model
# MAGIC Logs the agent as code from `agent.py` (MLflow Models-from-Code), and declares
# MAGIC every Databricks resource the agent depends on (the LLM endpoint, the vector
# MAGIC search index, both UC functions) for automatic auth passthrough at deployment
# MAGIC time — the serving endpoint gets scoped credentials for exactly these
# MAGIC resources, nothing broader.

# COMMAND ----------

import mlflow
from agent import LLM_ENDPOINT_NAME, VECTOR_SEARCH_TOOLS, uc_toolkit
from mlflow.models.resources import DatabricksFunction, DatabricksServingEndpoint
from pkg_resources import get_distribution

resources = [DatabricksServingEndpoint(endpoint_name=LLM_ENDPOINT_NAME)]
for tool in VECTOR_SEARCH_TOOLS:
    resources.extend(tool.resources)
for tool in uc_toolkit.tools:
    udf_name = tool.get("function", {}).get("name", "").replace("__", ".")
    resources.append(DatabricksFunction(function_name=udf_name))

input_example = {
    "input": [
        {
            "role": "user",
            "content": "What is an LLM agent?"
        }
    ],
    "custom_inputs": {
        "session_id": "test-session"
    }
}

with mlflow.start_run():
    logged_agent_info = mlflow.pyfunc.log_model(
        name="agent",
        python_model="agent.py",
        input_example=input_example,
        pip_requirements=[
            "databricks-openai",
            "backoff",
            f"databricks-connect=={get_distribution('databricks-connect').version}",
        ],
        resources=resources,
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Evaluate the agent with Agent Evaluation
# MAGIC
# MAGIC `RelevanceToQuery` and `Safety` are the two scorers actually used in the run
# MAGIC that produced the live model. `RetrievalGroundedness` and `RetrievalRelevance`
# MAGIC (imported but unused in the original) would meaningfully strengthen this —
# MAGIC they specifically check whether the agent's answer is actually supported by
# MAGIC what the vector index retrieved, which `RelevanceToQuery`/`Safety` alone don't
# MAGIC catch. Left as a genuine gap rather than silently "fixed" here, since adding
# MAGIC scorers changes what "passing evaluation" means for this agent and that's worth
# MAGIC a deliberate decision, not a drive-by edit.
# MAGIC
# MAGIC The single-row eval dataset below is also worth expanding before trusting this
# MAGIC agent broadly — one example with no `expected_response` mostly checks "does it
# MAGIC run," not "does it answer correctly."

# COMMAND ----------

import mlflow
from mlflow.genai.scorers import RelevanceToQuery, Safety, RetrievalRelevance, RetrievalGroundedness

eval_dataset = [
    {
        "inputs": {
            "input": [
                {
                    "role": "user",
                    "content": "What is an LLM agent?"
                }
            ]
        },
        "expected_response": None
    }
]

eval_results = mlflow.genai.evaluate(
    data=eval_dataset,
    predict_fn=lambda input: AGENT.predict({"input": input, "custom_inputs": {"session_id": "evaluation-session"}}),
    scorers=[RelevanceToQuery(), Safety()],  # RetrievalRelevance()/RetrievalGroundedness() imported above but not used — see note
)

# Review the evaluation results in the MLflow UI (see console output)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pre-deployment validation

# COMMAND ----------

mlflow.models.predict(
    model_uri=f"runs:/{logged_agent_info.run_id}/agent",
    input_data={"input": [{"role": "user", "content": "Hello!"}], "custom_inputs": {"session_id": "validation-session"}},
    env_manager="uv",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register the model to Unity Catalog

# COMMAND ----------

mlflow.set_registry_uri("databricks-uc")

catalog = "uc_agentic_ai"
schema = "agentic_ai_schema"
model_name = "sai_agent_model"
UC_MODEL_NAME = f"{catalog}.{schema}.{model_name}"

uc_registered_model_info = mlflow.register_model(
    model_uri=logged_agent_info.model_uri, name=UC_MODEL_NAME
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deploy the agent
# MAGIC
# MAGIC `scale_to_zero=True` matches the live deployment — cost-efficient for a demo
# MAGIC agent, at the cost of a cold-start delay on the first request after idle time.
# MAGIC Not recommended if this were a production workload with latency SLAs.

# COMMAND ----------

from databricks import agents

agents.deploy(UC_MODEL_NAME, uc_registered_model_info.version, tags={"endpointSource": "playground"}, scale_to_zero=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next steps
# MAGIC
# MAGIC Query the live endpoint from the AI Playground, or programmatically via
# MAGIC `POST /serving-endpoints/agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model/invocations`.
# MAGIC See `05_agent_creation/README.md` for the architecture summary and known gaps.
