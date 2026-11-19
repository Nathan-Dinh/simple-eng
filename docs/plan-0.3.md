# simply-eng: planned changes

## Purpose

simply-eng becomes a consulting agency made up of build agencies and specialist agencies.
It helps build production-ready applications: software that works now and stays
maintainable and extensible as it grows.

## Summary

- Annotation system: a committed index of every file's purpose, area, layer, and dependencies, kept current by hooks. It is how agents find their way around a project.
- Agency structure: a lead directs three build agencies (Discovery, Design, Delivery) and five specialist agencies (DevOps, Security, Performance, Testing, Legal and compliance), with project-specific `se-` agents for large areas. Models are tiered by role.
- Working rules: approvals in chat, fact labels, research in project docs, clear documents, no added code comments, tight scope, and verify before done.
- Architecture standards: pass/fail checks, each owned by an agency and scaled to the project's stage.
- Removals: decision records, evidence records, the event log, and research reference notes, with a cleanup offer for existing projects.

## 1. Annotation system (highest priority)

Annotations are how AI navigates a project, so they must always match the current code.

How it works:
- Agents annotate files and record the relationships between them.
- Each annotation contains:
  - Purpose: what the file does, in a sentence.
  - Area: the business area it belongs to (for example payments or auth). Must be one of the areas listed in the index.
  - Layer: Presentation, Application, Domain, or Infrastructure (see Layered architecture). Can be empty for files outside the layers (config, tests, migrations) or list more than one when the framework combines layers (a Django model is Domain and Infrastructure).
  - Key symbols: the file's main public classes and functions, so an agent can find the part of a large file that matters.
  - Dependencies: the project files it depends on, in two kinds:
    - Imports: computed by a parser, not a model, so they are exact and cost nothing.
    - Other links: relationships a parser cannot see, such as a URL route to its view, code that reads a database table, or a view that renders a template. Written by a model.
    "Used by" is derived by reversing these links, not stored.
  - Content hash: a hash of the file when the annotation was last written, used to detect drift.
- Given a task, an agent matches it against the annotations to find the relevant files instead of scanning the whole codebase.
- Annotations live in `.simple-eng/annotations.jsonl`, not in source files (see Code comments). Each line is one file's annotation, sorted by path, so branches that annotate different files merge without conflicts.
- The index is committed with the code, so every session and every agent sees the same map.

Areas:
- Areas are listed in `.simple-eng/areas.json`, each with a one-line description. Annotations can only use listed areas, so names do not drift ("payment" vs "payments").
- Adding, renaming, or merging an area updates every annotation that uses it in the same change.

What gets annotated:
- Every file tracked by git, except generated files, vendored code, lockfiles, build output, and binary assets.
- The exclusions live in `.simple-eng/config.json` and default to the framework's usual generated and build paths.

Building the index:
- For an existing project, analyze-existing-project builds the index as part of its analysis. Labor-tier models write the per-file annotations (see Model tiering).
- For a new project, the index starts empty and grows as files are added.

Keeping it current:
- Any change that adds, moves, renames, or deletes files, or changes how files relate, updates the annotations in the same change.
- Stale or missing annotations are bugs and are fixed when found.
- `simple-eng validate` reports:
  - files with no annotation;
  - annotations that point to files that no longer exist;
  - annotations whose content hash no longer matches the file;
  - annotations that use an area not in the list.
- A PostToolUse hook runs the same check after each file edit, limited to the edited files so it stays fast as the project grows. It reports drift back to the agent, which updates the annotation in the same change.
- A Stop hook runs the check once more when the agent finishes, on every file `git status` reports as changed. This catches files moved or deleted through shell commands (`git mv`, `rm`), which the edit hook does not see.
- When a file's content hash changes, the parser refreshes its imports, and a labor-tier model rereads the file and updates its Purpose, Key symbols, Layer, and other links if they no longer match. The hash is then refreshed.

Loading into context:
- The SessionStart hook loads only the list of areas and their descriptions, not the whole index, so large projects do not fill the context.
- Agents query the index for the slice they need instead of reading the file directly:
  - `simple-eng annotations --area payments`: every file in an area.
  - `simple-eng annotations --related-to src/orders.py`: a file's dependencies and the files that use it.
  - `simple-eng annotations --search "refund"`: files whose Purpose or Key symbols match.

## 2. Agency structure

### Hierarchy
1. Lead: the main Claude session. It receives the request, decides which agencies it needs, assigns the work, settles conflicts, and combines the results into one answer for the user.
2. Agencies: groups of skills that do the work and report to the lead.
3. Project agents (`se-` agents): carry out an agency's work on one area of this codebase.

Depth scales with complexity: a simple task goes to one agency; a complex task uses several agencies and their project agents.

### How work runs
- The hierarchy describes who directs whom, not how processes nest. Claude Code subagents cannot start their own subagents, so the lead starts every subagent itself: it gives each one the agency's skill and, when an area has one, the matching `se-` agent.
- Build agencies run in sequence, and only the stages a task needs: Discovery, then Design, then Delivery. A bug fix can go straight to Delivery.
- Specialist agencies run in parallel with each other, alongside or after the build work they review.
- Only the agency doing a task's main work uses project agents. Specialists review at the agency level, so the number of subagents stays small.

### Reports to the lead
Every agency returns the same report shape, so the lead can combine results:
- Summary: what was done or found, in a few lines.
- Changes: files created, edited, or deleted, with the annotation index updated to match.
- Findings: each with a fact label (see Fact labels) and, for specialist reviews, a severity: blocking, should fix, or note.
- Open questions: anything that needs the user's decision.

### Conflicts
- When agencies disagree (for example Security wants an extra check that Performance says breaks a budget), the lead does not pick a side silently. It presents both positions and the trade-off to the user (see Approvals).
- A blocking finding from a specialist stops the task until it is fixed or the user accepts the risk.

### Build agencies
Move a project from idea to working code.
- Discovery: initialize-project, analyze-existing-project.
- Design: architecture-design, database-engineering, ui-ux-design.
- Delivery: feature-development, maintain-project.

### Specialist agencies
Each owns one concern across the whole project. It does the work in its area, reviews any task that touches that area, and reviews every release at the release checkpoint.

| Agency | Covers | Brought in when a task |
|---|---|---|
| DevOps | CI/CD, environments, deployment, infrastructure as code, observability setup, incident response | changes how the app is built, deployed, or run |
| Security | threat modeling, authentication and authorization, secrets, validation at trust boundaries, dependency vulnerabilities | touches auth, user input, personal data, secrets, or a trust boundary |
| Performance | performance budgets, profiling, query analysis, load testing, caching | touches a hot path, a database query, or a performance budget |
| Testing | test strategy, coverage of critical paths, integration and end-to-end tests, test reliability | is ready for verification, or touches critical or untested code |
| Legal and compliance | dependency licenses, privacy and data protection (GDPR, CCPA), data retention, third-party terms, which accessibility laws apply (ADA, European Accessibility Act) | adds a dependency or third-party service, or collects, stores, or shares personal data |

Specialist reviews run in two passes to keep their cost below the cost of the work:
1. A labor-tier model runs the agency's checklist against the task.
2. Only if the checklist flags something does a judgment-tier model review it in depth.
The release checkpoint always runs both passes.

Legal and compliance flags risks and explains requirements; it does not give legal advice. Anything binding, such as contracts, published terms, or regulatory filings, goes to a human lawyer.

### Shared tools
The lead and any agency can use init, status, project-docs, checkpoints, and research-management. research-management is shared because most agencies need outside facts: Design compares technologies, Security checks vulnerabilities, and Legal and compliance checks licenses and laws.

### Changes to existing skills
- maintain-project hands incident response to DevOps and security reviews to Security.
- feature-development still writes tests as it builds; Testing owns the overall test strategy and reviews coverage.
- Accessibility is split: Legal and compliance says which laws and conformance levels apply; ui-ux-design implements accessibility to meet them.
- New skills, one per specialist agency: devops, security, performance, testing, legal-compliance.

### Model tiering
The model is fixed per role, not chosen per task. There are three tiers:
- Labor (cheapest): searching, reading, writing annotations, boilerplate, mechanical edits, and first-pass specialist checklists.
- Implementation (mid-tier): writing feature code, fixing bugs, and writing tests.
- Judgment (most capable): the lead, design decisions, trade-offs, and second-pass specialist reviews.

### Project-specific agents
- Project agents bring knowledge of one area of the codebase; agencies bring domain expertise. Project agents work under the agencies, not in place of them.
- An agent's area comes from the annotation index: files that share an Area value form one area.
- When an area grows large enough, simply-eng proposes an agent for it in chat and creates it after the user's go-ahead (see Approvals).
- Each agent knows its area: the relevant files, the domain rules, and the standards that apply there.
- Agents change with the project: new areas get new agents, and existing agents are updated, merged, or retired as their areas change.
- Agents are defined in `.claude/agents/` and committed with the code, so the whole team and every session use the same agents.
- Agents simply-eng creates are named with an `se-` prefix (for example `se-payments.md`). simply-eng only updates, merges, or retires `se-` agents and never touches agents the user wrote. To keep a hand-edited copy, rename it without the prefix.

## 3. Working rules

How simply-eng behaves while working in a project.

### Approvals
- Before a consequential step, simply-eng presents the choice and its trade-offs in chat and waits for the user's go-ahead.
- Consequential steps include: choosing or changing architecture or a major technology, changing a database schema, adding a dependency or third-party service, deleting data or files the user created, deploying, creating a project agent, and changing the project's stage.
- Only the lead asks the user. Subagents cannot pause for an answer, so they stop before a consequential step and return it as an open question in their report (see Reports to the lead).
- The lead batches the questions from one task into a single ask instead of interrupting for each one.
- An approval covers the step that was asked about. It does not carry over to later steps or other tasks.
- No approval log is kept. This replaces decision records and the approve/reject flow (see Removals).
- For major decisions (architecture, major technology, database design), simply-eng adds a short rationale to the relevant project doc: what was chosen, over what, and why. For example: "Chose Postgres over MongoDB because orders and payments need transactions across tables."

### Fact labels
Agents label the claims that matter for a decision, in their answers and in project docs. Not every sentence needs a label.

| Label | Meaning |
|---|---|
| verified | Checked directly by reading the code, running a command, or reading the source. Cites the source inline: file path, command output, or link. |
| user-provided | Stated by the user and not independently checked. |
| inferred | Reasoned from evidence but not checked directly. Says what it was inferred from. |
| proposed | A recommendation the user has not agreed to yet. Becomes user-provided once the user approves it. |
| unknown | Not known. Says what would answer it. |

### Research findings
- research-management writes findings into the project doc the research supports, with the source link and the date it was checked.
- For example, a technology comparison goes in the TRD, a database choice in the backend schema, and a UI pattern in the UI/UX brief.
- If that doc does not exist yet, project-docs creates it from its template first.
- Prefer primary sources: official docs, specifications, vendor pricing pages, and changelogs.
- Findings older than six months are rechecked before a new decision relies on them, because prices, versions, and APIs change. The checked date is updated after a recheck.

### Writing documents
Project docs are as simple as possible, but no simpler.
- Write for someone new to the project: plain words, short sentences, one idea per paragraph.
- Put the most important point first: the decision, the requirement, or the answer, then the detail behind it.
- Keep the details a reader needs to act: exact names, numbers, limits, edge cases, and trade-offs. Do not cut these to make a doc shorter.
- Leave out what a reader does not need: filler, repetition, background nobody asked for, and template instructions.
- Define a technical term the first time it appears, or link to where it is defined.
- Use lists and tables for facts that can be compared; use sentences for reasoning.

### Code comments
- simply-eng does not add comments to project code. Only the user adds comments.
- Docstrings are the exception: simply-eng writes docstrings for public functions, classes, and modules, following the framework's docstring style. Docstrings on private helpers count as comments.
- simply-eng does not leave TODO or FIXME comments. Follow-up work goes in its report as an open question.
- simply-eng never changes the text of the user's comments.
- When simply-eng moves code, the user's comments move with it. When it deletes code, the comments on that code are deleted with it.
- Files produced by a framework or tool generator (for example Django migrations) keep whatever comments the generator writes.

### Scope
- Change only what the task needs. No drive-by refactors, renames, or reformatting of unrelated code.
- Improvements noticed along the way go in the report as suggestions, not into the change.

### Verify before done
- Before reporting a task done, run the project's tests, linters, and type checks that cover the change.
- Report the results as they are. If something fails or a check was skipped, say so with the output; do not report the task as done.

## 4. Tooling

- All simple-eng scripts and hooks run from the project root and resolve paths relative to it, whatever directory they are invoked from.
- After these changes the plugin has three hooks:
  - SessionStart: loads project context and the list of areas, and checks for leftovers from 0.2 (see Existing projects).
  - PostToolUse: annotation drift check on edited files.
  - Stop: annotation drift check on every file git reports as changed.
- Files simple-eng keeps in `.simple-eng/`, all committed:
  - `config.json`: project stage, annotation exclusions, and whether the 0.2 cleanup was declined.
  - `annotations.jsonl`: the annotation index.
  - `areas.json`: the list of areas.

## 5. Architecture standards

The standards simply-eng applies to the projects it helps build. Each has an owning agency.
- All agencies apply the standards while designing and building.
- The owning agency reviews any task that touches its standard.
- At the release checkpoint, every specialist agency reviews the release in parallel.
- Each rule is written as a check that can pass or fail, because the first review pass is a labor-tier checklist (see Specialist agencies).

Proportionality:
- Standards apply in proportion to the project's stage: prototype, pre-production, or production. The stage is set in `.simple-eng/config.json` and changed with the user's go-ahead.
- For example, a prototype skips traces, alerts, load testing, and rate limiting; tracing starts once there is more than one service; alerts start in production.
- Some rules apply at every stage and are never skipped: secrets stay out of the repo, endpoints require authorization, outside input is validated, and tenants are isolated.
- When the lead skips a rule because of the stage, its report says which rule and why.

### Framework conventions (owner: Design)
- Follow the framework's recommended project structure and coding style. For example, a Django project uses Django's app layout and coding style.
- Use the ecosystem's standard formatter and linter (for example Ruff for Python, ESLint and Prettier for JavaScript), configured in the repo, so style is enforced by tools rather than by review.

### Layered architecture (owner: Design)
Map these four layers onto the framework's structure rather than imposing a separate folder layout:
- Presentation: endpoints and UI. Handles input and output; contains no business rules.
- Application: use cases. Coordinates the other layers.
- Domain: business logic and rules. Depends on no other layer.
- Infrastructure: databases, external APIs, queues, and other external systems.

Dependencies point inward: Presentation -> Application -> Domain. Infrastructure implements interfaces that the Application and Domain layers define.

When a framework convention conflicts with these rules, the framework wins, and the layer rules apply only where they fit. For example, Django models are both domain objects and database access, so simply-eng does not wrap the ORM in repositories, but it still keeps business logic out of views.

### System design (owner: Design)
- Common problems use established patterns instead of new inventions:
  - Calls to external systems have timeouts and retries with backoff.
  - Operations that can be retried (payments, webhooks, queue consumers) are idempotent.
  - Slow or bulk work runs in a background queue, not in the request.
  - Public endpoints are rate limited.
  - Caches have a stated invalidation rule.

### Data design (owner: Design)
- Every table or collection has one owning domain; other domains read it through that domain's code, not directly.
- The schema is designed from the access patterns: the main queries are listed, and each one is backed by an index or key.
- Migrations are reversible, or the migration states why it cannot be reversed.
- Migrations on live data are backward compatible with the running code, so deploys need no downtime.

### Error handling (owner: Design)
- No exception is caught and ignored. Each one is handled, or logged and re-raised.
- Errors are translated at layer boundaries: Infrastructure errors become domain errors before they reach the Application layer, and domain errors become responses in the Presentation layer.
- The API returns errors in one consistent format, following the framework's convention where it has one.
- Users never see stack traces, SQL, file paths, or other internal details; those go to the logs.

### Security and data boundaries (owner: Security)
- Stateful workflows are explicit state machines: named states, allowed transitions, and who can trigger each transition.
- Data flows between domains, applications, and external systems are mapped. Each trust boundary states what is validated and authorized when data crosses it.
- Every endpoint requires authorization by default; public endpoints are marked as public explicitly.
- All input from outside a trust boundary is validated before use.
- Secrets are never in code or in the repo; they come from environment variables or a secret store.
- In multi-tenant systems, every query is scoped to the tenant, and a test proves one tenant cannot read another's data.
- Dependencies are scanned for known vulnerabilities in CI.

### Observability (owner: DevOps)
Every service emits:
- Logs: structured, with a request or correlation ID.
- Metrics: request rate, error rate, latency, and resource saturation.
- Traces: follow a request across layers and services.

And:
- Logs never contain secrets, passwords, tokens, or unmasked personal data.
- Each service has a health check endpoint.
- Error rate and latency have alerts with a stated threshold.

### Configuration and deployment (owner: DevOps)
- Configuration comes from environment variables or a config service, never from values hard-coded per environment.
- The same build artifact is deployed to every environment; only configuration differs.
- Database migrations run as a step of the deploy, not by hand.
- Every deploy has a rollback plan, and the plan has been tried at least once.
- CI runs the tests, linters, and dependency scan on every change before it can merge.

### Performance (owner: Performance)
- Critical paths have a performance budget (for example p95 latency) and are measured against it.
- No database query runs inside a loop (no N+1 queries).
- Endpoints that return lists are paginated.
- Optimizations are backed by a measurement taken before and after the change.

### Testing (owner: Testing)
- Critical paths have integration tests: auth, payments, data writes, and every transition of a state machine.
- Every bug fix includes a test that fails without the fix.
- Tests are independent: they do not rely on run order, shared state, wall-clock timing, or network calls outside their control.
- Tests use the framework's test runner and conventions (see Framework conventions).
- A failing or flaky test blocks release. It is fixed, or removed with a stated reason, never silently skipped.

## 6. Removals

This is a breaking change: commands, skills, and files that users rely on go away.

### Decision feature
- DEC-#### decision records and the `add-decision` and `show` CLI commands.
- The `approve` and `reject` skills.
- The decision dashboard (`dashboard` CLI command, dashboard.py).
- Pending-decision reporting in the session context (context.py).
- The decision policy, template, and schema (reference/policies/decisions.md, reference/templates/decision-record.md, reference/decision-event.schema.json).
- Decision owners: the `decision-owners` knowledge area in project-map.json and the "Decision owners" section of the PROJECT.md template. Approval now comes from the user in chat (see Approvals), so there is no separate owner list.
- The "Pending decisions" section of the STATE.md template.
- References to decision records and decision owners in architecture-design, database-engineering, checkpoints, project-docs, and the rubrics.

### Evidence records
- EVD-#### evidence records, the `add-evidence` CLI command, and the `docs/evidence/records` folder.
- The evidence policy and template (reference/policies/evidence.md, reference/templates/evidence-record.md).
- Research reference notes: the `docs/resources/` folder and its template (reference/templates/research-reference.md). Research findings go only into the project doc they support (see Research findings).
- References to evidence records in the skills, rubrics, and templates that cite them (research-management, analyze-existing-project, feature-development, maintain-project, init, and others).

### Event feature
- `decision-log/events.jsonl` and the event model in records.py.
- The UserPromptExpansion hook and its handler (`prompt_expansion` in hooks.py).
- The PreToolUse hook and its handler (`pre_tool_use` in hooks.py), which blocks writes to the event log and stops Claude from calling the approve and reject skills. Neither is needed once they are gone.
- The matching entries in hooks/hooks.json.

### Always-on rules
The CLAUDE.md block template (reference/templates/claude-md-block.md) loses its decision rules and gains the new working rules:
- Remove: approval by `/simple-eng:approve`, "never edit decision-log/events.jsonl", "change a decision only through a superseding DEC", and the pointers to `docs/decisions/`, `docs/evidence/`, and the event log.
- Add: approvals in chat, fact labels, writing documents, code comments, scope, verify-before-done, and keeping annotations current.

### Code cleanup
- records.py keeps only the traceability-ID checks (REQ, QA, FEAT, TEST) and the fact-label list. Remove the event transitions (ALLOWED_AFTER), `set_record_status`, and DEC and EVD from the ID patterns. Rename the file to match, for example traceability.py.
- Remove the LOG, DECISIONS, and EVIDENCE paths from paths.py.
- Delete or trim the tests for the removed code: test_hooks.py, test_records.py, and the decision and evidence cases in test_cli.py, test_context.py, and helpers.py.

### Docs and metadata
- README: remove the approve/reject commands, the decision and evidence CLI commands, the "how approval works" section, and the event-log limitations; describe approvals in chat and the annotation system instead.
- plugin.json: drop "decisions with typed approvals, evidence" from the description and "decisions" from the keywords.
- Bump the minor version (0.2.0 to 0.3.0) when releasing, and add an "Upgrading from 0.2" note to the README that lists what was removed and what replaces it.

### Existing projects
Projects already set up with simply-eng still have the old files and rules. On the first session after upgrading, simply-eng offers to clean them up in one ask (see Approvals):
- Move the findings from each note in `docs/resources/` into the project doc it relates to, with its source link and checked date (see Research findings). Notes that fit no project doc are listed in the ask so the user can decide what to do with them.
- Then delete `decision-log/`, `docs/decisions/`, `docs/evidence/`, and `docs/resources/`.
- Rewrite the simple-eng block in CLAUDE.md from the new template. Text outside the simple-eng markers is never touched.
- Remove the "Pending decisions" section from `docs/STATE.md` and the "Decision owners" section from `docs/PROJECT.md`.

If the user declines, simply-eng records that in `.simple-eng/config.json`, leaves the files alone, and does not ask again. The CLAUDE.md block is the exception: until it is rewritten it tells agents to use commands that no longer exist, so the SessionStart hook keeps flagging it.

## Implementation order

1. Removals and code cleanup, including the cleanup offer for existing projects. This shrinks the codebase before anything new is added.
2. Working rules and tooling: update the skills and the CLAUDE.md block template for approvals, fact labels, research findings, writing documents, code comments, scope, and verify-before-done.
3. Annotation system: the index and areas files, the import parser, the validate check, the query command, and the PostToolUse and Stop hooks.
4. Lead and build agencies: the hierarchy, reports, conflicts, model tiering, research-management as a shared tool, and the Design-owned standards in the design skills.
5. Specialist agencies: the five new skills, each with the standard it owns and its review checklist, and the handoffs out of maintain-project.
6. Release checkpoint: runs every specialist agency in parallel, applying proportionality by project stage.
7. Project-specific agents. Needs the annotation index (step 3) to define each agent's area.
8. Release 0.3.0: README, plugin.json, and the upgrade note.

## Open questions (answered)

- Which specific models fill the labor, implementation, and judgment tiers? Labor: `haiku`, implementation: `sonnet`, judgment: `opus`, as the model aliases on the plugin's `labor`, `implementer`, and `reviewer` agents. The lead is the main session, so its model is the user's choice.
- Which languages does the import parser support first? Python (standard library `ast`) and JS/TS (relative `import`, `export ... from`, `import()`, and `require()` specifiers). Other languages have no parsed imports; their dependencies are recorded as other links.
- How large does an area get before simply-eng proposes an agent for it? 15 annotated files, set by `agent_threshold` in `.simple-eng/config.json`.
