# Databricks App Evidence Screenshots

Copied from [`saiprashanthts1995/databricks-app-ui-agent`](https://github.com/saiprashanthts1995/databricks-app-ui-agent), where they were originally captured against the live workspace and app.

| Filename | Evidence |
|---|---|
| `01-architecture-overview.png` | End-to-end architecture diagram, PDF → Vector Search → Agent → Model Serving → Databricks App. |
| `02-product-master-pipeline.png` | The data pipeline building `product_master` from source tables. |
| `03-uc-function-tools-partial.png` | UC function tools, partial view. |
| `04-uc-function-tools.png` | Both UC function tools (`get_policy_details`, `get_customer_service_history`) in full. |
| `05-claude-code-mcp-integration.png` | Claude Code connected to a Databricks MCP server for ad-hoc read-only querying during development. |
| `06-app-overview.png` | The deployed Databricks App's chat UI, overview. |
| `07-agents-list.png` | The Genie Agents / Agents list showing `sai_agent`. |
| `08-serving-endpoints.png` | The Model Serving endpoints page showing `agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model`. |
| `09-catalog-schema.png` | Catalog Explorer view of `uc_agentic_ai.agentic_ai_schema`. |
| `10-product-master-sample-data.png` | Sample rows from `product_master`. |
| `11-product-master-combined-column.png` | The `product_combined` embedding-source column. |
| `12-vector-index-overview-and-query.png` | `product_index` overview and a direct query against it. |
| `13-chat-ui-tool-call-output.png` | The chat UI showing a tool call's parameters and raw result inline with the conversation. |

These were not captured in this session — see the source repo for the original context. Only replace or add screenshots here that show genuine session results, consistent with every other assignment folder in this repo.
