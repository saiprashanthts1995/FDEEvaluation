# Workforce Assistant: Claude Code Toolkit

## Purpose

This folder documents the Claude Code workflows used to develop and maintain the Workforce Insights and HR Policy Assistant. Project context and standards are in the root `CLAUDE.md`; reusable skills and specialist subagents live under `.claude/`.

## Available Workflows

- `/code_review` reviews changed files for correctness, data quality, privacy, access control, groundedness, and test gaps without editing them.
- `/employee-data-onboarding` validates the synthetic employee and department inputs before any approved workspace ingestion.
- `/workforce-assistant-delivery` coordinates a requested component or end-to-end workflow; it is manually invoked to avoid running cloud operations unexpectedly.
- `workforce-data-analyst`, `hr-knowledge-specialist`, and `governance-quality-reviewer` are read-only specialist subagents for bounded research and review.

## GitHub MCP

The project `.mcp.json` points to GitHub's repository-only read-only endpoint. It references `GITHUB_PAT`; never put the token itself in this repository. Set the variable through an approved local secret manager before starting Claude Code. Review and approve the project MCP server when Claude Code prompts, then check its status with `/mcp` or `claude mcp list`.

MCP access is not verified merely because the configuration exists. Record a successful read-only repository query before marking the integration complete. Do not use this server for issue, pull-request, or repository writes.

## Evidence

Capture genuine screenshots of the invoked review command, each specialist subagent, both skills, and the connected read-only GitHub MCP query. Keep credentials out of view. Document the exact prompt or command and observed result; mark unavailable services as blocked rather than inventing results.