# FDE Evaluation

Six assignments building a Databricks-based agentic AI solution end to end: Claude Code workflows, conversational analytics, vector search, retrieval-augmented generation, a tool-calling agent, and a chat UI in front of it.

**[Open `architecture.html`](architecture.html) for the full end-to-end flow diagram** (download/clone and open in a browser — it's a self-contained page, no build step, dark-mode aware).

## Two Use Cases, By Design

**Assignment 1** implements a Workforce Insights and HR Policy Assistant over synthetic HR data (`shared_data/`) — see the root [`CLAUDE.md`](CLAUDE.md) for that product's full spec.

**Assignments 2–6** pivot to a product-catalog and customer-service dataset that already existed in the Databricks workspace (`uc_agentic_ai.agentic_ai_schema`), rather than ingesting the HR data into Unity Catalog. This was a deliberate choice, made and documented at the start of assignment 2: the workspace already had a ready-made dataset (`products`, `product_master`, `product_details`, `policies`, `cust_service_data`) worth demonstrating discovery and governed analytics over, instead of provisioning new tables from scratch. Every later assignment builds on that same dataset for consistency. `CLAUDE.md`'s "Repository Scope" section has the full explanation.

## Assignments

| Folder | What it covers |
|---|---|
| [`01_claude_code/`](01_claude_code/) | Claude Code workflows: slash commands, subagents, skills, MCP integration, and a real reproduce → diagnose → fix → verify bug fix (a silently-dropping SQL join, found by code review, fixed, and verified against synthetic edge-case data). |
| [`02_genie_space/`](02_genie_space/) | A Genie Space for natural-language analytics over the product/customer-service tables, programmatic access via the Genie Conversation API, a break-and-fix cycle on an ambiguous business term, and row-level governance (a real Unity Catalog row filter, applied live). |
| [`03_vector_database/`](03_vector_database/) | The Vector Search index behind the whole pipeline: how `product_master` was built from 509 parsed PDFs, health/freshness verification, filtered search, a Delta Sync vs. Direct Vector Access comparison, and `top_k` tuning — all run against the live index. |
| [`04_rag/`](04_rag/) | Retrieval-augmented generation: structured UC-function tools alongside unstructured vector retrieval, grounded answer generation, chunking-strategy tradeoffs, metadata-filtered retrieval, and hybrid vs. pure-semantic search — with a measured case where hybrid search meaningfully outperforms. |
| [`05_agent_creation/`](05_agent_creation/) | A deployed tool-calling agent (`sai_agent_model`) combining the vector index and both UC functions, evaluated with 4 scorers, traced end to end, and monitored live — including two real, documented findings about ungrounded answers when the agent's system prompt is empty. |
| [`06_databricks_app/`](06_databricks_app/) | A chat UI (Next.js, deployed as a Databricks App) fronting the deployed agent, with tool calls shown inline so a user can see what the agent retrieved before trusting its answer. |

Each folder's own `README.md` documents what was actually built, why, and any known gaps or design decisions — those are the authoritative source for that assignment, not this file.

## Repository Layout

```
architecture.html              End-to-end flow diagram — open in a browser
CLAUDE.md                      Product spec for the Workforce Insights use case + repo-wide standards
shared_data/                   Synthetic HR tables and documents (assignment 1's data)
product_catalog_data/          Raw source data behind uc_agentic_ai.agentic_ai_schema (assignments 2–6's data)
lightweight_evidence_3_4_5.py  Zero-install REST/SQL notebook covering core evidence for assignments 3–5
lightweight_evidence_batch2.py Companion notebook covering the remaining assignment 3/4 scenarios
01_claude_code/                Claude Code workflow evidence
02_genie_space/                Genie Space + notebooks + evidence
03_vector_database/            Vector Search notebooks + evidence
04_rag/                        RAG notebooks + evidence
05_agent_creation/             Agent notebooks + evidence
06_databricks_app/             Chat UI app code + evidence
```

Every assignment folder follows the same internal pattern: a `README.md` explaining what was built and how, a `notebooks/` folder (where applicable) with the actual Databricks notebooks, and a `screenshots/` folder with a checklist README plus the captured evidence.

The two `lightweight_evidence_*.py` notebooks at the repo root exist because of a real constraint worth being upfront about: this was built against a free-tier Databricks workspace with limited serverless compute quota, where the standard `%pip install`-heavy notebooks repeatedly hit capacity limits. Both notebooks produce the same evidence using only `spark.sql(...)` and direct REST calls — no package installs — and are what actually generated most of the assignment 3/4/5 screenshots in this repo. The heavier, fully-featured notebooks (`03_vector_database/notebooks/03_advanced_scenarios.py`, `04_rag/notebooks/03_chunking_tradeoffs.py`, etc.) still exist and are the "proper" versions; the lightweight ones were the pragmatic path to real evidence under real constraints.

## Working Conventions

- **Nothing is guessed.** Every catalog, schema, table, index, endpoint, and model name referenced anywhere in this repo was confirmed against the live Databricks workspace via read-only API calls before being used — not assumed from documentation or memory.
- **Cloud writes are gated.** Anything that creates or modifies workspace state (schemas, tables, indexes, permissions, deployments) is either already-approved and documented as such, or disabled by default in its notebook (an explicit flag like `RUN_INDEX_CREATION = False`) pending deliberate review.
- **Gaps are flagged, not hidden.** Where something is thin, missing, or a real discrepancy between what was planned and what's actually live, it's called out directly in the relevant README rather than glossed over — including genuine findings discovered while running notebooks (e.g. the deployed agent's missing system prompt, or an evaluation scorer that doesn't apply to every row).
- **Screenshots are evidence, not decoration.** Each `screenshots/README.md` maps exact filenames to exact evidence; only genuine session results go in, no placeholders.
