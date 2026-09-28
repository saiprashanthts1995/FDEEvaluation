# Assignment 1: Claude Code Workflows

## Goal

Demonstrate how Claude Code can make work on the Northstar Outfitters project more repeatable, scoped, and reviewable. This module establishes the repository conventions that the later Databricks assignments will follow.

## Scenarios

1. **Repeatable workflow:** use a `/code_review` command to check correctness, data handling, security, errors, and tests.
2. **Context management:** use a focused catalog-auditor agent to investigate schema and data-quality references without loading the entire project into the main context.
3. **Reusable skill:** package the supplier-catalog onboarding procedure, including file/schema validation, safe loading expectations, and quality checks.
4. **Standards enforcement:** keep project-wide implementation and evidence rules in the root `CLAUDE.md`.
5. **Agentic debugging:** demonstrate reproduce, diagnose, fix, and verify on one deliberately introduced issue; retain the failing and passing test evidence.
6. **MCP integration:** connect GitHub MCP using an environment-provided token and demonstrate a read-only repository query.

## Use Case and Boundaries

The project uses synthetic product catalog, sales, and returns data for a fictional outdoor-gear retailer. Customer-support answers later use fictional return, warranty, and equipment-care documents. This assignment itself creates Claude Code project guidance and reusable workflows; it does not require real customer data or deploy Databricks resources.

## Execution Flow

1. Open this repository as the Claude Code project root and review `CLAUDE.md`.
2. Run `/code_review` against a small, representative change and record the findings.
3. Invoke the catalog-auditor agent with a targeted schema or quality question; compare its bounded result with a broad, unfocused investigation.
4. Invoke the catalog-onboarding skill on the documented synthetic input contract. Do not load files into a real workspace unless the later data assignment explicitly requires it.
5. Reproduce a small test failure, trace its cause, make the narrow fix, and rerun the same test.
6. Configure GitHub MCP locally with a token from the environment; query repository metadata without exposing the token.

## Evidence Checklist

Capture screenshots from the actual Claude Code session showing:

- `/code_review` invocation and its structured result.
- The catalog-auditor agent name, focused task, and concise findings.
- The catalog-onboarding skill being invoked and its validation checklist.
- A failing reproduction followed by the passing verification.
- A successful read-only GitHub MCP query, with credentials and private data out of view.

Save evidence under `01_claude_code/screenshots/` using descriptive names such as `01-code-review.png`. Include the command or test name in the README next to each screenshot when the scenario is completed. Screenshots must show this project/use case, not the HR screenshots in the reference repositories.

## Completion Criteria

- Each workflow is reproducible from the repository instructions.
- The skill and agent are narrow enough to be reused safely.
- The debugging example includes a real before/after test result.
- MCP credentials are not committed or visible in evidence.
- Screenshots and any scenario-specific notes are added before moving to Assignment 2.

## Status

Planning and repository structure established. Claude Code artifacts and live evidence are next.