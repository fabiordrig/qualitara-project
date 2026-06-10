<!-- GSD:project-start source:PROJECT.md -->

## Project

**Fleet Telemetry Monitor**

A full-stack fleet monitoring service for 50 autonomous industrial vehicles emitting telemetry at 1 Hz per vehicle. Built as a take-home engineering assessment — a vertical slice demonstrating concurrent write handling, real-time anomaly detection, atomic fault transitions, and a live React dashboard.

**Core Value:** Operators can monitor all 50 vehicles' live status, see anomalies immediately, and trust that zone traversal counts and fault transitions are always consistent — even under burst concurrent writes.

### Constraints

- **Timeline**: 5-6 hours total — scope ruthlessly, document tradeoffs in ADR
- **Tech Stack**: FastAPI + PostgreSQL (backend), React + TypeScript (frontend)
- **Live updates**: Polling only (2-3s interval) — WebSockets explicitly deferred
- **Deliverable**: Single public GitHub repo with README explaining how to run

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->

## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
