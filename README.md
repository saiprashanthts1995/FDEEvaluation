# FDE Evaluation

Six assignments building a Databricks-based agentic AI solution end to end: Claude Code workflows, conversational analytics, vector search, retrieval-augmented generation, a tool-calling agent, and a chat UI in front of it.

## Two Use Cases, By Design

**Assignment 1** implements a Workforce Insights and HR Policy Assistant over synthetic HR data (`shared_data/`) — see the root [`CLAUDE.md`](CLAUDE.md) for that product's full spec.

**Assignments 2–6** pivot to a product-catalog and customer-service dataset that already existed in the Databricks workspace (`uc_agentic_ai.agentic_ai_schema`), rather than ingesting the HR data into Unity Catalog. This was a deliberate choice, made and documented at the start of assignment 2: the workspace already had a ready-made dataset (`products`, `product_master`, `product_details`, `policies`, `cust_service_data`) worth demonstrating discovery and governed analytics over, instead of provisioning new tables from scratch. Every later assignment builds on that same dataset for consistency. `CLAUDE.md`'s "Repository Scope" section has the full explanation.

## Assignments

| Folder | What it covers | Status |
|---|---|---|
| [`01_claude_code/`](01_claude_code/) | Claude Code workflows: slash commands, subagents, skills, MCP integration, a real reproduce → diagnose → fix → verify bug fix | Complete, 9/9 screenshots |
| [`02_genie_space/`](02_genie_space/) | Genie Space for natural-language analytics, programmatic API access, row-level governance | Core build done; some evidence still pending (see folder README) |
| [`03_vector_database/`](03_vector_database/) | Vector Search index build/verification, freshness, filtering, index-type comparison, query tuning | Notebooks written, screenshots pending |
| [`04_rag/`](04_rag/) | Structured + unstructured retrieval tools, grounded generation, chunking tradeoffs, metadata filtering, hybrid retrieval | Notebooks written, screenshots pending |
| [`05_agent_creation/`](05_agent_creation/) | A deployed tool-calling agent, evaluation, tracing/root-cause analysis, deployment monitoring | Agent live; evaluation/tracing/monitoring notebooks written, screenshots pending |
| [`06_databricks_app/`](06_databricks_app/) | A chat UI (Next.js, deployed as a Databricks App) fronting the deployed agent | Complete, 13/13 screenshots |

Each folder's own `README.md` documents what was actually built, why, and any known gaps or design decisions — those are the authoritative source for that assignment, not this file.

## Repository Layout

```
CLAUDE.md                      Product spec for the Workforce Insights use case + repo-wide standards
shared_data/                   Synthetic HR tables and documents (assignment 1's data)
01_claude_code/                Claude Code workflow evidence
02_genie_space/                Genie Space + notebooks + evidence
03_vector_database/            Vector Search notebooks + evidence
04_rag/                        RAG notebooks + evidence
05_agent_creation/             Agent notebooks + evidence
06_databricks_app/             Chat UI app code + evidence
```

Every assignment folder follows the same internal pattern: a `README.md` explaining what was built and how, a `notebooks/` folder (where applicable) with the actual Databricks notebooks, and a `screenshots/` folder with a checklist README plus the captured evidence.

## Working Conventions

- **Nothing is guessed.** Every catalog, schema, table, index, endpoint, and model name referenced anywhere in this repo was confirmed against the live Databricks workspace via read-only API calls before being used — not assumed from documentation or memory.
- **Cloud writes are gated.** Anything that creates or modifies workspace state (schemas, tables, indexes, permissions, deployments) is either already-approved and documented as such, or disabled by default in its notebook (an explicit flag like `RUN_INDEX_CREATION = False`) pending deliberate review.
- **Gaps are flagged, not hidden.** Where something is thin, missing, or a real discrepancy between what was planned and what's actually live, it's called out directly in the relevant README rather than glossed over.
- **Screenshots are evidence, not decoration.** Each `screenshots/README.md` maps exact filenames to exact evidence; only genuine session results go in, no placeholders.
