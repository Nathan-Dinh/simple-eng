# simple-eng

A Claude Code plugin that works like a small consulting agency to help you build production-ready applications: software that works now and stays maintainable and extensible as it grows. A lead (your Claude session) directs three build agencies and five specialist agencies. A committed index of every file's purpose and dependencies shows them where to look. Your project's knowledge stays in its repository, so Claude doesn't lose it on compaction, `/clear`, or in a new session.

## Install

In Claude Code:

```text
/plugin install simple-eng --marketplace Nathan-Dinh/simple-eng
```

On older Claude Code versions, add the marketplace first:

```text
/plugin marketplace add Nathan-Dinh/simple-eng
/plugin install simple-eng@simple-eng
```

The plugin's command line and hooks need `python3` (3.9 or later, standard library only). Without it, sessions keep working but project state isn't loaded, and a one-line notice says so.

## First run in a project

Open Claude Code in the project and type:

```text
/simple-eng:init
```

Claude shows what it will create, including a diff of `CLAUDE.md`, and asks before writing anything. Then it fills in what it can learn from the repository and asks you about the rest, a few questions at a time. For an existing codebase, run `simple-eng:analyze-existing-project` next: it drafts the project documents and builds the annotation index. Running init again after a plugin update refreshes only the managed part of `CLAUDE.md`.

What a project gets:

| File | Purpose | Who changes it |
|---|---|---|
| `CLAUDE.md` (a block between `simple-eng` markers) | The always-on rules: approvals, fact labels, scope, comments, verification, annotations | `/simple-eng:init`; your own text outside the markers is never touched |
| `docs/PROJECT.md` | Stable facts: problem, users, scope, constraints, stack, commands, environments | Claude, from what it finds and what you tell it |
| Project documents (`docs/product/PRD.md`, `docs/product/app-flow.md`, `docs/design/ui-ux-brief.md`, `docs/architecture/TRD.md`, `docs/backend/schema.md`, `docs/plan/implementation-plan.md`) | What is being built and how, including the rationale for major decisions and the research behind them | Claude, from your brief or the codebase |
| `docs/STATE.md` | Work in progress: current focus, checkpoints, open questions, recent changes | Claude, as work moves forward |
| `.simple-eng/config.json` | Project stage, annotation exclusions, project agent threshold, and optional pointers to facts that live elsewhere | `/simple-eng:init`, or you |
| `.simple-eng/areas.json` | The project's business areas, each with a one-line description | Claude, with `simple-eng areas` |
| `.simple-eng/annotations.jsonl` | The annotation index: one line per file | Claude, with `simple-eng annotate` |
| `.claude/agents/se-*.md` | Project agents, one per large area | Claude, after you agree |

Commit these files. They are the project's memory.

## How the agency works

The lead is your Claude session. It takes your request, decides which agencies it needs, starts their subagents, settles conflicts, and gives you one answer. A small change goes to one agency or none; a large one uses several.

**Build agencies** run in sequence, and only the stages a task needs. A bug fix can go straight to Delivery.

| Agency | Skills |
|---|---|
| Discovery | `initialize-project`, `analyze-existing-project` |
| Design | `architecture-design`, `database-engineering`, `ui-ux-design` |
| Delivery | `feature-development`, `maintain-project` |

**Specialist agencies** each own one concern across the project. They do the work in their area, review any task that touches it, and all review every release in parallel at checkpoint G.

| Agency | Covers | Brought in when a task |
|---|---|---|
| DevOps | CI/CD, environments, deployment, infrastructure as code, observability, incident response | changes how the app is built, deployed, or run |
| Security | threat modeling, authentication and authorization, secrets, input validation, dependency vulnerabilities | touches auth, user input, personal data, secrets, or a trust boundary |
| Performance | performance budgets, profiling, query analysis, load testing, caching | touches a hot path, a database query, or a performance budget |
| Testing | test strategy, critical-path coverage, integration and end-to-end tests, test reliability | is ready for verification, or touches critical or untested code |
| Legal and compliance | licenses, privacy (GDPR, CCPA), data retention, third-party terms, accessibility law | adds a dependency or service, or handles personal data |

Legal and compliance flags risks and explains requirements. It is not legal advice; anything binding goes to a lawyer.

**Model tiers.** Each subagent runs on a model fixed by its role, through three plugin agents:

| Tier | Agent | Model | Work |
|---|---|---|---|
| Labor | `simple-eng:labor` | haiku | searching, reading, annotations, mechanical edits, first-pass review checklists |
| Implementation | `simple-eng:implementer` | sonnet | feature code, bug fixes, tests |
| Judgment | `simple-eng:reviewer` | opus | design decisions, trade-offs, in-depth reviews |

The lead runs on whatever model you chose for the session.

**Specialist reviews** run in two passes, so a review costs less than the work it checks. A labor-tier subagent runs the agency's checklist; only if something is flagged does a judgment-tier subagent review it in depth. Findings are blocking, should fix, or note, and a blocking finding stops the task until it's fixed or you accept the risk.

**Standards.** Each agency owns a set of pass/fail rules (`plugin/reference/standards/`): framework conventions, layered architecture, system and data design, and error handling for Design, plus one set per specialist. Each rule is tagged with the project stage it starts at: prototype, pre-production, or production. A prototype skips traces, alerts, load testing, and rate limiting. Keeping secrets out of the repo, authorization on every endpoint, input validation, and tenant isolation apply at every stage. `simple-eng stage` shows the stage; changing it needs your go-ahead.

**Project agents.** When an area of the codebase reaches 15 annotated files (configurable), the lead proposes an `se-<area>` agent that knows that area's files, rules, and standards. It's created only after you agree, committed to `.claude/agents/`, and kept in step as areas are renamed, merged, or retired. simple-eng never touches agents without the `se-` prefix, so to keep a hand-edited copy, rename it without the prefix.

## Approvals happen in chat

Before a consequential step, Claude presents the choice and its trade-offs and waits for your go-ahead. Consequential steps are: choosing or changing architecture or a major technology, changing a database schema, adding a dependency or third-party service, deleting data or files you created, deploying, creating a project agent, and changing the project's stage.

- Only the lead asks you. Subagents stop before a consequential step and hand it back as an open question.
- Questions from one task come in a single ask.
- An approval covers the step you were asked about, nothing later.
- For major decisions, the reason goes into the relevant project doc, for example "Chose Postgres over MongoDB because orders and payments need transactions across tables."

No approval log is kept.

## Working rules

The `CLAUDE.md` block makes these rules apply in every session. `plugin/reference/policies/working-rules.md` holds the detail.

- **Fact labels.** Claims that a decision depends on are labeled verified (with the file, command, or link), user-provided, inferred (with the basis), proposed, or unknown (with what would answer it).
- **Research** goes into the project doc it supports, with the source link and the date checked. Findings older than six months are rechecked before a new decision relies on them.
- **Documents** are written for someone new to the project: main point first, plain words, and every name, number, and limit a reader needs.
- **Code comments.** Claude doesn't add comments to your code, only docstrings on public functions, classes, and modules. It never edits your comments and leaves no TODOs.
- **Scope.** Claude changes only what the task needs. Improvements it notices go in its report as suggestions.
- **Verify before done.** Claude runs the tests, linters, and type checks that cover a change, and reports failures as they are.

## The annotation index

Every file in the repository (tracked by Git, or new and not ignored), except generated, vendored, lockfile, build, and binary files, has one line in `.simple-eng/annotations.jsonl`:

```json
{"path": "orders/views.py", "purpose": "HTTP endpoints for placing and refunding orders", "area": "orders", "layer": ["Presentation"], "symbols": ["OrderView", "refund_order"], "imports": ["orders/services.py"], "links": ["templates/orders/detail.html"], "hash": "3f9a1c0b7d2e4a51"}
```

- **Imports** come from a parser, so they are exact and free. Python is parsed with the standard library's `ast`, and JS/TS relative imports with a pattern match. Other languages rely on links.
- **Links** are relationships a parser can't see, such as a route to its view or code that reads a table. A model writes them.
- **"Used by"** is computed by reversing imports and links.
- **Areas** must be listed in `.simple-eng/areas.json`, so names don't drift. Renaming or merging an area rewrites every annotation that uses it.
- **Lines are sorted by path**, so branches that annotate different files merge without conflicts.

The index stays current through hooks:

- After each file edit, a hook checks that file and tells Claude when its annotation is missing or out of date.
- When Claude finishes, another hook checks every file `git status` reports as changed. This catches `git mv` and `rm`, and Claude fixes the index before stopping.
- At session start, only the list of areas is loaded, never the whole index.

Agents query the slice they need:

```text
simple-eng annotations --area payments          every file in an area
simple-eng annotations --related-to src/orders.py   a file's dependencies and the files that use it
simple-eng annotations --search "refund"        files whose purpose or key symbols match
```

## Skills

| Skill | Use it for |
|---|---|
| `/simple-eng:init` | Set up or refresh a project (you run it) |
| `lead` | Any non-trivial task: routing to agencies, subagents, reports, conflicts |
| `status` | Which project facts are recorded or missing |
| `initialize-project`, `analyze-existing-project` | Discovery, for a new project or an existing codebase |
| `project-docs` | Draft and fill the six project documents |
| `architecture-design`, `database-engineering`, `ui-ux-design` | Design |
| `feature-development`, `maintain-project` | Delivery |
| `devops`, `security`, `performance`, `testing`, `legal-compliance` | Specialist work and reviews |
| `research-management` | External facts behind a decision |
| `checkpoints` | Checkpoints A–G, including the release checkpoint |

Claude picks these on its own when they fit. You can also invoke any of them by name, for example `/simple-eng:security`.

## The `simple-eng` command

Claude runs `simple-eng` through its Bash tool; the plugin puts it on Claude's PATH. You can run it yourself with `python3 <plugin-dir>/bin/simple-eng`. Paths are resolved from the project root, whatever directory you run it in.

```text
simple-eng init [--apply]                   what /simple-eng:init runs
simple-eng status [--workflow NAME]         which knowledge areas are recorded, missing, or not applicable
simple-eng docs [--apply]                   create missing project documents from their templates; never overwrites
simple-eng validate                         check ID references, document status, the annotation index, and se- agents
simple-eng annotate PATH --purpose P --area A [--layer L] [--symbol S] [--link PATH]
simple-eng annotate PATH --confirm          the annotation still matches; refresh imports and the hash
simple-eng annotate --remove PATH           drop the annotation of a deleted or moved file
simple-eng annotate --from-json FILE|-      annotate many files at once
simple-eng annotations --area A | --related-to PATH | --search TEXT | --missing | --drift
simple-eng areas [add NAME DESC | rename OLD NEW | merge FROM INTO]
simple-eng agents                           areas that should get, update, or retire an se- agent
simple-eng stage [prototype|pre-production|production]
simple-eng cleanup [--apply | --decline]    remove simple-eng 0.2 leftovers
simple-eng context                          print what the session-start hook injects
```

## Upgrading from 0.2

0.3 is a breaking change. These are gone:

| Removed | Replaced by |
|---|---|
| `/simple-eng:approve` and `/simple-eng:reject`, `DEC-####` decision records, `decision-log/events.jsonl`, the dashboard, and the `add-decision`, `show`, and `dashboard` commands | Approvals in chat, with a short rationale for major decisions in the relevant project doc |
| `EVD-####` evidence records and `add-evidence` | Fact labels, with the source cited inline |
| Research notes in `docs/resources/` | Findings written into the project doc they support, with the source link and checked date |
| The "Decision owners" section of `PROJECT.md` and "Pending decisions" in `STATE.md` | You approve in chat |
| The UserPromptExpansion and PreToolUse hooks | PostToolUse and Stop hooks that keep the annotation index current |

On the first session after upgrading, Claude offers the cleanup once. It moves the findings from `docs/resources/` into your project docs, then runs `simple-eng cleanup --apply`. That deletes `decision-log/`, `docs/decisions/`, `docs/evidence/`, and `docs/resources/`, rewrites the simple-eng block in `CLAUDE.md`, and removes the two old sections. Text outside the `CLAUDE.md` markers is never touched. If you decline, the files stay and you aren't asked again. The exception is an old `CLAUDE.md` block: it tells Claude to use commands that no longer exist, so the session context keeps flagging it until you refresh it with `/simple-eng:init`.

## Boundaries

- **Guidance is not enforcement.** Hooks guarantee that state is loaded and that annotation drift is reported. Whether Claude writes good annotations, asks before consequential steps, and follows the standards depends on Claude following the rules.
- **Checks prove structure, not truth.** `simple-eng validate` catches missing, stale, and broken annotations and references. `simple-eng status` reports whether a fact is recorded. Neither checks that the content is correct; only you can confirm that.
- **The import parser covers Python and JS/TS relative imports.** TypeScript path aliases and other languages rely on model-written links.
- **Claude Code only.** Other agents won't pick up the skills, agents, or hooks.
- **Token figures are estimates** (bytes ÷ 4). `simple-eng budget` prints them.

## Developing

```text
.claude-plugin/marketplace.json   the marketplace; points at ./plugin
plugin/                           everything that installs (only this folder is copied to users)
├── .claude-plugin/plugin.json    name and version
├── skills/                       the lead, agency, and shared-tool skills
├── agents/                       the labor, implementer, and reviewer tier agents
├── hooks/hooks.json              session start, annotation drift after edits and at stop
├── bin/simple-eng                command-line entry point, on Claude's PATH
├── lib/simple_eng/               the code behind bin/ and the hooks
└── reference/                    files skills read on demand: policies, standards, rubrics,
                                  templates, project-map.json
tests/                            maintainer tests; not installed
docs/                             plans for upcoming releases; not installed
```

```bash
python3 -m unittest discover -s tests -v          # unit, fixture, and end-to-end CLI tests
python3 plugin/bin/simple-eng validate --plugin   # skills, agents, references, standards, token budgets
python3 plugin/bin/simple-eng budget              # estimated tokens per workflow
claude plugin validate . --strict                 # marketplace manifest
claude plugin validate ./plugin --strict          # plugin manifest and components
claude --plugin-dir ./plugin                      # try the plugin locally without installing
```

To release, bump `version` in `plugin/.claude-plugin/plugin.json`. Installed copies stay on their version until it changes.

The tests check code and guidance structure. They don't run an agent or prove how a conversation will go.

## References

- Claude Code plugin, hook, subagent, and skill documentation: https://code.claude.com/docs
- On plain language: https://www.learningguild.com/articles/be-concrete-why-simple-language-matters-in-the-ai-age
