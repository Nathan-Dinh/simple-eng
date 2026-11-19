# Working rules

How simply-eng works in a project. The CLAUDE.md block states these briefly; this file holds the detail.

## Approvals

- Before a consequential step, present the choice and its trade-offs in chat and wait for the user's go-ahead.
- The consequential steps are listed in the simple-eng block of the project's CLAUDE.md.
- Only the lead (the main session) asks the user. A subagent cannot pause for an answer, so it stops before a consequential step and returns it as an open question in its report.
- Batch the questions from one task into a single ask.
- An approval covers the step that was asked about. It does not carry over to later steps or other tasks. Silence, a recommendation, or a passing test is not approval.
- For a major decision (architecture, major technology, database design), add a short rationale to the project doc it belongs in: what was chosen, over what, and why. For example: "Chose Postgres over MongoDB because orders and payments need transactions across tables."

## Fact labels

Label the claims a decision depends on, in answers and in project docs. Not every sentence needs a label.

| Label | Meaning |
|---|---|
| verified | Checked directly by reading the code, running a command, or reading the source. Cite the source inline: file path, command output, or link. |
| user-provided | Stated by the user and not independently checked. Add the date in project docs. |
| inferred | Reasoned from evidence but not checked directly. Say what it was inferred from. |
| proposed | A recommendation the user has not agreed to yet. Becomes user-provided once the user approves it. |
| unknown | Not known. Say what would answer it. |

A config file, a passing test, or a documentation page proves only what it covers. None of them alone proves production behavior.

Requirements also carry a status: `open` (raised, not agreed), `accepted` (agreed by the user), `deferred` (agreed to postpone), or `dropped` (agreed out of scope). An inferred requirement never becomes accepted without the user agreeing.

## Research findings

- Write each finding into the project doc the research supports, with the source link and the date it was checked. A technology comparison goes in the TRD, a database choice in the Backend Schema, a UI pattern in the UI/UX Design Brief.
- If that doc does not exist yet, create it from its template first (`simple-eng docs --apply`).
- Prefer primary sources: official docs, specifications, vendor pricing pages, and changelogs. Treat tutorials as leads.
- Recheck a finding older than six months before a new decision relies on it, because prices, versions, and APIs change. Update the checked date after the recheck.
- Never claim a page was read if it was not, and never store credentials.

## Writing documents

Project docs are as simple as possible, but no simpler.

- Write for someone new to the project: plain words, short sentences, one idea per paragraph.
- Put the most important point first (the decision, the requirement, or the answer), then the detail behind it.
- Keep the details a reader needs to act: exact names, numbers, limits, edge cases, and trade-offs. Do not cut these to make a doc shorter.
- Leave out what a reader does not need: filler, repetition, background nobody asked for, and template instructions.
- Define a technical term the first time it appears, or link to where it is defined.
- Use lists and tables for facts that can be compared, and sentences for reasoning.
- When translating or summarizing, keep the source's meaning, caveats, and uncertainty. Do not turn a recommendation into a fact.

## Code comments

- simply-eng does not add comments to project code. Only the user adds comments.
- Docstrings are the exception: write docstrings for public functions, classes, and modules, in the framework's docstring style. A docstring on a private helper counts as a comment.
- Do not leave TODO or FIXME comments. Follow-up work goes in the report as an open question.
- Never change the text of the user's comments. When moving code, move its comments with it; when deleting code, delete the comments on it.
- Files produced by a framework or tool generator (for example Django migrations) keep whatever comments the generator writes.

## Scope

- Change only what the task needs. No drive-by refactors, renames, or reformatting of unrelated code.
- Improvements noticed along the way go in the report as suggestions, not into the change.

## Verify before done

- Before reporting a task done, run the project's tests, linters, and type checks that cover the change.
- Report results as they are. If something fails or a check was skipped, say so with the output, and do not report the task as done.
