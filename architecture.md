# End-to-End Architecture

Two tracks, six assignments. Track A (assignment 1) demonstrates Claude Code workflow practices against the Workforce Insights HR data. Track B (assignments 2–6) is one continuous pipeline: raw product data becomes governed tables, a vector index, a retrieval-augmented agent, and a chat UI, over the same live Unity Catalog objects throughout.

## Track A — Assignment 1: Claude Code Workflows

Slash commands, subagents, skills, and MCP integration applied to `shared_data/` (synthetic employees/departments CSVs, HR onboarding & leave-request guides) — the Workforce Insights product this repo's [`CLAUDE.md`](CLAUDE.md) describes. Independent of Track B; establishes the working practices (verify before writing, flag gaps, reproduce → diagnose → fix → verify) carried through the rest of the repo.

| Step | What happened |
|---|---|
| Onboarding validation | CSV/schema checks via a packaged skill |
| Metric clarified | Active headcount definition confirmed before encoding |
| Data contract + UC proposal | Proposal only — not executed against a workspace |
| Code review → real fix | Silent-drop JOIN bug found and fixed, verified with a synthetic test |
| GitHub MCP | Connected, read-only query confirmed working |

## Track B — Assignments 2–6: Product Catalog Pipeline

All on `uc_agentic_ai.agentic_ai_schema` — a pre-existing dataset discovered read-only before assignment 2 began, reused instead of ingesting new data. Raw source files (509 PDFs, the 3 CSVs) are preserved locally in [`product_catalog_data/`](product_catalog_data/).

```mermaid
flowchart TD
    subgraph SRC["Source data"]
        PDF["509 product PDFs<br/>UC Volume + product_catalog_data/documents/"]
        TBL["products, policies, cust_service_data<br/>553 products · 6 policies · 1,023 interactions"]
    end

    subgraph A3["Assignment 3 — parsed and joined"]
        PD["product_details<br/>ai_parse_document · 509 rows"]
        PM["product_master<br/>joined on normalized name · 553 rows · product_combined"]
    end

    PDF --> PD
    TBL --> PM
    PD --> PM

    subgraph A2["Assignment 2 — Genie"]
        GS["Genie Space<br/>NL → SQL over all 5 tables"]
        GA["Genie Conversation API<br/>programmatic, no UI"]
        RF["Row filter<br/>cust_service_data, owner-only, applied live"]
    end

    subgraph A34["Assignments 3–4 — Retrieval"]
        VI["product_index<br/>Delta Sync · Hybrid · ai_search_endpoint"]
        UCF["UC functions<br/>get_policy_details, get_customer_service_history"]
        RAG["Grounded RAG demo<br/>databricks-gpt-oss-120b · explicit refusal check"]
    end

    subgraph A5["Assignment 5 — Agent"]
        AGT["ToolCallingAgent<br/>3 tools: vector index + 2 UC functions"]
        DEP["sai_agent_model<br/>registered, evaluated, deployed to Model Serving"]
    end

    subgraph A6["Assignment 6 — App"]
        APP["Databricks App<br/>Next.js chat UI · tool calls shown inline"]
    end

    PM --> GS
    TBL --> GS
    GS --> GA
    GS -.governed by.-> RF

    PM --> VI
    TBL --> UCF
    VI --> RAG
    UCF --> RAG

    VI --> AGT
    UCF --> AGT
    AGT --> DEP
    DEP --> APP
```

### Real findings, documented not silently patched

> **Missing system prompt.** The deployed agent has no system prompt. An off-domain question got answered ("Paris") instead of declined, and with its vector-search tool unavailable it answered a product question from general LLM knowledge instead of erroring. The standalone RAG demo (assignment 4), which does have a grounding prompt, declines correctly in both cases. See [`05_agent_creation/README.md`](05_agent_creation/README.md).

> **Evaluation scorer applicability.** Agent evaluation's `RetrievalGroundedness`/`RetrievalRelevance` scorers only apply cleanly to the 3 of 10 test questions that hit the vector index — the 7 that used UC functions show `Error`, not pass/fail, since there's no retrieval span to score. See [`05_agent_creation/README.md`](05_agent_creation/README.md#evaluation-results).

> **Scope note.** The agent has no Genie tool — it can't answer aggregate questions ("how many products in Electronics?") that `product_index` alone can't serve.

## Where Each Piece Lives

| Stage | Folder |
|---|---|
| Source data | [`product_catalog_data/`](product_catalog_data/) |
| Genie Space, row governance | [`02_genie_space/`](02_genie_space/) |
| Vector index build & verification | [`03_vector_database/`](03_vector_database/) |
| Retrieval tools & grounded generation | [`04_rag/`](04_rag/) |
| Deployed agent, evaluation, tracing, monitoring | [`05_agent_creation/`](05_agent_creation/) |
| Chat UI | [`06_databricks_app/`](06_databricks_app/) |

See each assignment's own `README.md` for full detail, screenshots, and scenario coverage.
