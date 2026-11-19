---
description: Understand an existing codebase before changing it - inspect structure, stack, tests, CI, data, and docs, build the annotation index, separate facts from inference, and ask only what the code cannot answer.
needs: []
---

# Analyze an existing project

## Inspect before asking

Work out what kind of repository this is (application, library, infrastructure, other). Inspect, with bounded reads, the file tree, entry points, dependency manifests, build and run configuration, architecture, persistence layer, tests, CI and deployment configuration, security and privacy controls, and docs. A config file shows intent, not deployed state.

Run safe, focused checks when useful (for example the test suite, if it is cheap and has no side effects) and note the exact commands and results. Do not run destructive commands, install dependencies, call external services, or touch production without authorization.

## Findings and questions

Summarize verified facts with paths. Keep user-provided context, inferences, proposed improvements, and unknowns apart (labels in `${CLAUDE_PLUGIN_ROOT}/reference/policies/working-rules.md`). Identify existing conventions and accepted decisions; never invent the history behind them.

Treat contradictions between docs and code as drift candidates, not proof of intent. Before treating either one as authoritative, ask when the difference is consequential.

Then ask a small group of material questions the repository cannot answer: users and outcomes, expected usage, unrecorded constraints, operational expectations, data classification, ownership, target environments, success criteria. Say why each answer matters.

## Build the annotation index

The index (`.simple-eng/annotations.jsonl`) is how agents find their way around the project later, so build it as part of the analysis.

1. Propose the business areas from the structure you found (for example `payments`, `auth`, `catalog`), each with a one-line description, and add them with `simple-eng areas add NAME "description"`. Keep the `project` area for docs, configuration, and tooling that belong to no single area.
2. `simple-eng annotations --missing` lists the files to annotate. Split them into batches by directory and start one labor-tier subagent (`simple-eng:labor`) per batch. Each one reads its files and writes a JSON list of `{path, purpose, area, layer, symbols, links}` to `simple-eng annotate --from-json -`. Imports are parsed automatically; `links` holds only what the parser cannot see: a URL route to its view, code that reads a table, a view that renders a template.
3. Layer is Presentation (endpoints, UI), Application (use cases), Domain (business rules), or Infrastructure (databases, external APIs, queues). Leave it empty for config, tests, and migrations, or list more than one where the framework combines layers (a Django model is Domain and Infrastructure).
4. Run `simple-eng validate` until the index has no problems, then spot-check a few annotations yourself.

## Prioritize

Identify the highest-impact gaps and whether they block a safe change. Do not turn discovery into an unsolicited redesign. When the project documents are missing, legacy, or out of date (`simple-eng status`), offer to draft them from the code with `simple-eng:project-docs` in existing-project mode. For architecture work, review quality priorities and the rationale recorded in the TRD first; for database work, look at the schema, migrations, tenancy, and tests; for features, use `simple-eng:feature-development`.

## Record and hand off

- Write findings into `docs/PROJECT.md` sections (stack, commands, environments) and the project documents that `simple-eng status` lists, with labels and paths.
- In `docs/STATE.md`, record the lifecycle stage, open questions, drift candidates, and one proposed next checkpoint or action.
- If there is no change request, stop at discovery and ask only the highest-impact next question.
