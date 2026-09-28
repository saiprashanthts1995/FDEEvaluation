# Databricks App: Product Assistant Chat UI

## Purpose

The final piece of CLAUDE.md's Solution Architecture — "A Databricks App provides the user interface and respects underlying access controls" — applied to the product-catalog use case. A chat UI (Next.js, deployed as a Databricks App) fronts the `sai_agent_model` serving endpoint from [`05_agent_creation/`](../05_agent_creation/), so an end user gets a normal chat experience instead of calling the Model Serving REST API directly.

The app code lives in [`app/`](app/) (`node_modules`/`.next`/build artifacts excluded). If the app changes going forward, edit it in place here.

## Architecture

```
PDF ──► Volumes ──► parse ──► product_details ──┐
                                                  ├──► product_master ──► product_index (Vector Search)
products (UC table) ─────────────────────────────┘
                                                                              │
policies, cust_service_data (UC tables) ──► UC functions ────────────────────┤
                                                                              ▼
                                                                  sai_agent_model (LLM + tools)
                                                                              │
                                                              MLflow: log → evaluate → register → deploy
                                                                              │
                                                                              ▼
                                                      agents_uc_agentic_ai-agentic_ai_schema-sai_agent_model
                                                                              │
                                                                              ▼
                                                    Databricks App (e2e-chatbot-app-next) ── chat UI for end users
```

This matches what was independently verified in `03_vector_database/`, `04_rag/`, and `05_agent_creation/` — same `product_index`, same two UC functions, same `sai_agent_model` endpoint. One naming note: the app's own README describes the join as `products` + `product_dimension`, whereas the live workspace (confirmed via the Unity Catalog API while building `03_vector_database/`) has `products` + `product_details` feeding `product_master` — likely just a naming drift in that README rather than a different pipeline, since the resulting `product_master`/`product_index` are the same objects referenced throughout this repo.

## What the App Adds Beyond the Raw Endpoint

- A normal chat interface instead of raw JSON requests to `/serving-endpoints/.../invocations`.
- Tool calls the agent makes (e.g., a `product_index` vector search) are shown inline with their parameters and raw results — so a user (or reviewer) can see exactly what the agent retrieved before trusting its answer, not just the final text.
- Deployed as a Databricks App, which is what makes "respects underlying access controls" (CLAUDE.md's phrasing) meaningful — auth and permissions run through the Databricks App framework rather than a standalone server holding its own credentials.

## Evidence

Screenshots captured directly against the live workspace and app. See [`screenshots/`](screenshots/) for the full set and what each one shows.
