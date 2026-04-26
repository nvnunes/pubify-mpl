# AGENTS.md

## Astro-Agents Bootstrap
- Use `astro-agents` for reusable authoring, review, and routing guidance in this repo.

## Scope
- Documentation surface profile: public-python.

## Source Of Truth Docs
- Follow `README.md` for the public overview, install path, quick-start usage, and public examples.
- Follow `docs/architecture.md` for package shape, public API boundaries, artifact ownership, and export/layout lifecycle.
- Follow `docs/testing.md` for canonical verification commands and completion expectations.
- Follow `docs/development.md` for local setup and daily commands.

## Shared Guidance
- Use `astro-agents/guidance/agent-surface.md` for shared agent-surface guidance.
- Use `astro-agents/guidance/public-python-projects.md` for shared public Python repo guidance.
- Use `astro-agents/guidance/python-development.md` for shared Python architecture, coding-policy, and development-workflow guidance.

## Authoring Requirements
- For Python code, follow `astro-agents/authoring/code/python.md`.
- For repo docs such as `docs/architecture.md`, `docs/testing.md`, `docs/development.md`, and similar long-lived repo documents, follow `astro-agents/authoring/writing/repo-docs.md`.
- For `README.md`, follow `astro-agents/authoring/writing/readme-md.md` in addition to `astro-agents/authoring/writing/repo-docs.md`.
- For plan documents or phased execution docs when they are created or revised, follow `astro-agents/authoring/writing/plan.md`.

## Working Rules
- For package structure, public API boundaries, artifact ownership, and export/layout-lifecycle-sensitive changes, consult `docs/architecture.md` before editing.
- Before concluding substantial work, satisfy the verification expectations in `docs/testing.md`.
- Use the local `./.conda` workflow from `docs/development.md` for Python commands, test runs, and docs builds unless a task explicitly requires something else.
