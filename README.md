# Northstar Outfitters: Databricks AI Portfolio

A single, end-to-end project covering six Databricks and Claude Code assignments using a fictional outdoor-gear retailer. The use case is intentionally different from the HR examples in the reference repositories.

## Business Scenario

Northstar Outfitters wants to help its operations and customer-support teams answer two kinds of questions:

- **Analytics:** sales, product performance, returns, and regional trends, backed by governed tables.
- **Knowledge:** return, warranty, and equipment-care questions, grounded in approved policy documents.

All example transactions and documents will be synthetic. No customer personal data or production credentials belong in this repository.

## Assignment Sequence

| # | Folder | Focus | Depends on |
|---|---|---|---|
| 1 | [01_claude_code](01_claude_code/README.md) | Repeatable workflows, project standards, a catalog-onboarding skill, debugging, and MCP | Repository setup |
| 2 | `02_vector_search` | Governed document table, Vector Search index, filtered retrieval, freshness, and query tuning | Shared policy corpus |
| 3 | `03_rag` | Chunking, metadata filters, citations, groundedness, and hybrid retrieval | Vector Search |
| 4 | `04_genie` | Conversational sales analytics, metadata quality, permissions, and API access | Shared analytics tables |
| 5 | `05_agent` | Tool calling across Genie and policy retrieval, evaluation, tracing, and deployment | RAG and Genie |
| 6 | `06_databricks_app` | Streamlit interface, agent integration, access checks, and iterative improvements | Deployed agent |

## End-to-End Flow

```text
Synthetic sales + returns ----------------------> Unity Catalog analytics tables --> Genie
Approved return/warranty/care guides --> chunks --> Vector Search --> RAG
                                                                  Genie + RAG --> Agent
                                                                              Agent --> Databricks App
```

Each assignment folder will contain its own `README.md` with the goal, setup, execution flow, evidence checklist, and cleanup notes. Screenshots should be captured from the actual workspace after each scenario succeeds; do not present mock or reference-repository screenshots as project evidence.

## Prerequisites

- A Databricks workspace with Unity Catalog and permissions to create the required catalog/schema, compute or serverless resources, Vector Search endpoint/index, Genie Space, and App.
- Claude Code for Assignment 1.
- A configured GitHub MCP connection only if the MCP scenario is run; keep access tokens in environment variables, never in committed files.

Exact resource names and workspace-specific steps will be documented in each assignment README as the modules are built. Cloud resource availability and startup time can affect the three-hour schedule.