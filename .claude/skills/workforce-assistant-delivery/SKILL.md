---
name: workforce-assistant-delivery
description: "Plan, implement, evaluate, or operate the end-to-end Workforce Insights and HR Policy Assistant across governed analytics, document retrieval, an agent, and an app. Use when working across multiple solution components or tracing a user question end to end."
disable-model-invocation: true
argument-hint: "[component or end-to-end task]"
---

# Workforce Assistant Delivery

Work on the requested component or on `$ARGUMENTS`. Keep this skill focused on a single requested phase unless the user explicitly asks for an end-to-end change. Inspect current files and workspace resources before proposing actions.

## Delivery Flow

1. **Data contract:** validate employee and department schemas, key relationships, status semantics, and metric definitions. Ask before resolving ambiguous business definitions.
2. **Governed analytics:** use Unity Catalog and Delta tables; document table and column meanings; configure Genie questions and verify generated SQL and aggregate results. Test access with the intended identities when available.
3. **Document retrieval:** ingest only the approved HR guides after approval. Preserve document ID, topic, version, and section metadata. Compare chunking and retrieval settings with representative questions; check filtering and index freshness.
4. **Grounded answers:** connect retrieval to generation, attach document and section citations, test supported and unsupported questions, and evaluate semantic and keyword/hybrid retrieval where available.
5. **Agent:** route workforce questions to analytics and procedure questions to retrieval. Evaluate tool choice, answer quality, errors, and traces before any deployment.
6. **Application:** expose the approved capabilities through a Databricks App. Respect Unity Catalog permissions, handle service failures, and verify user-facing behavior after each change.
7. **Evidence:** run focused checks, capture genuine screenshots from the active workspace, and document exact commands, results, assumptions, and limitations.

## Specialist Delegation

- Use `workforce-data-analyst` for schemas, metrics, and analytics.
- Use `hr-knowledge-specialist` for source documents, chunking, retrieval, and grounding.
- Use `governance-quality-reviewer` for permissions, privacy, evaluation, and release evidence.

## Guardrails

- Use synthetic data only. Do not make employment or eligibility decisions.
- Do not expose tokens or personal data in files, logs, prompts, or screenshots.
- Obtain explicit approval before workspace writes, ingestion, permission changes, deployment, or external GitHub changes.
- Never report a configuration, evaluation, deployment, or access check as successful unless it was actually verified.