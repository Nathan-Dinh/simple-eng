# simple-eng

A Claude Code plugin that helps you build production-ready applications: software that works now and stays easy to change as it grows.

It works like a small consulting agency. Your Claude session is the lead. It sends work to build agencies (Discovery, Design, Delivery) and has specialist agencies (DevOps, Security, Performance, Testing, Legal and compliance) review it. Everything Claude learns about your project is saved in the repository, so nothing is lost after `/clear`, compaction, or a new session.

## Install

```text
/plugin install simple-eng --marketplace Nathan-Dinh/simple-eng
```

On older Claude Code versions, run `/plugin marketplace add Nathan-Dinh/simple-eng` first, then `/plugin install simple-eng@simple-eng`.

Requires `python3` 3.9 or later. No other dependencies.

## Get started

In your project, type:

```text
/simple-eng:init
```

Claude shows what it will create and asks before writing anything. Then it fills in what it can learn from the code and asks you about the rest. For an existing codebase, ask Claude to analyze the project next; it drafts the project documents and indexes every file.

Commit the files it creates. They are the project's memory:

- `CLAUDE.md`: the rules Claude follows in every session (only the block between the `simple-eng` markers is managed).
- `docs/PROJECT.md` and `docs/STATE.md`: stable facts, and where work stands.
- `docs/product/`, `docs/design/`, `docs/architecture/`, `docs/backend/`, `docs/plan/`: the PRD, App Flow, UI/UX brief, TRD, backend schema, and implementation plan.
- `.simple-eng/`: settings, the list of business areas, and the file index.

## How it works

**The lead routes each task.** A small change needs no ceremony. A larger one goes through only the stages it needs: Discovery (understand the problem or codebase), Design (architecture, data, UI), and Delivery (build or fix). Specialists join when a task touches their concern, such as Security for anything involving auth or user input, and all five review every release.

**Models match the work.** Subagents run on a model chosen by role: haiku for searching and routine edits, sonnet for writing code and tests, opus for design decisions and in-depth reviews. Reviews start with a cheap checklist and escalate only when something is flagged.

**You approve big steps in chat.** Before choosing architecture or a major technology, changing a database schema, adding a dependency or service, deleting your files or data, deploying, creating a project agent, or changing the project stage, Claude explains the trade-offs and waits for your go-ahead. The reason for each major decision is written into the relevant doc.

**Standards scale with the project.** Each agency checks a list of pass/fail rules (in `plugin/reference/standards/`). A prototype skips things like alerts and load testing; a production app doesn't. Secrets, authorization, input validation, and tenant isolation apply at every stage. Set the stage with `simple-eng stage`.

**Claude follows working rules.** It labels how it knows each important claim (verified, user-provided, inferred, proposed, or unknown), changes only what a task needs, doesn't add comments to your code (docstrings only), and runs your tests and linters before saying it's done. Details: `plugin/reference/policies/working-rules.md`.

## The file index

Claude finds its way around your code through `.simple-eng/annotations.jsonl`, one line per file:

```json
{"path": "orders/views.py", "purpose": "HTTP endpoints for placing and refunding orders", "area": "orders", "layer": ["Presentation"], "symbols": ["OrderView", "refund_order"], "imports": ["orders/services.py"], "links": ["templates/orders/detail.html"], "hash": "3f9a1c0b7d2e4a51"}
```

- Imports are parsed automatically for Python and JS/TS. Claude adds other links, such as a route to its view.
- Hooks keep it current: after each edit, and again when Claude finishes (which catches moved and deleted files).
- Claude asks the index for just the files a task needs instead of reading the whole codebase:

```text
simple-eng annotations --area payments
simple-eng annotations --related-to src/orders.py
simple-eng annotations --search "refund"
```

When an area reaches 15 files, Claude may propose a project agent for it (`.claude/agents/se-<area>.md`) that knows that part of the code. Agents without the `se-` prefix are never touched.

## Commands

Claude runs these for you. You can run them too, with `python3 <plugin-dir>/bin/simple-eng`.

```text
simple-eng status       what the project knows and what's missing
simple-eng validate     check docs, the file index, and project agents
simple-eng annotate     add or update a file's index entry
simple-eng annotations  search the file index
simple-eng areas        list, add, rename, or merge business areas
simple-eng agents       areas that should get or lose a project agent
simple-eng stage        show or set prototype, pre-production, or production
simple-eng docs         create missing project documents
simple-eng cleanup      remove leftovers from 0.2
```

Add `--help` to any command for its options.

## Upgrading from 0.2

0.3 removes decision records, evidence records, the event log, research notes in `docs/resources/`, and the `/simple-eng:approve` and `/simple-eng:reject` commands. Approvals now happen in chat, and research goes into the doc it supports.

On your first session after upgrading, Claude offers to clean up the old files once. Then run `/simple-eng:init` again to add the file index and refresh `CLAUDE.md`.

## Limits

- Hooks make sure context is loaded and drift is reported. Everything else depends on Claude following the rules.
- `validate` and `status` check structure, not whether the content is right. Only you can confirm that.
- Legal and compliance flags risks; it is not legal advice.
- Works with Claude Code only.

## Developing

`plugin/` is what installs; `tests/` and `docs/` are for maintainers.

```bash
python3 -m unittest discover -s tests            # tests
python3 plugin/bin/simple-eng validate --plugin  # check skills, agents, references, and size budgets
claude --plugin-dir ./plugin                     # try it locally
```

To release, bump `version` in `plugin/.claude-plugin/plugin.json`.
