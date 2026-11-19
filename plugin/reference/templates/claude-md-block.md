## simple-eng

This project uses the simple-eng plugin. Project knowledge lives in the repository, not in chat or agent memory: `docs/PROJECT.md` holds stable facts, the project documents (PRD, App Flow, UI/UX Design Brief, TRD, Backend Schema, Implementation Plan; `simple-eng status` lists them) describe what is built and how, `docs/STATE.md` holds work in progress, and `.simple-eng/` holds the config, the list of areas, and the annotation index. A SessionStart hook loads PROJECT, STATE, the areas, and knowledge gaps at startup and after compaction.

### Rules

1. Inspect the repository before asking. Ask only what it cannot answer, and say why each answer matters.
2. Never fabricate requirements, sources, approvals, test results, timestamps, history, or deployment status.
3. Approvals happen in chat. Before a consequential step, present the choice and its trade-offs and wait for the user's go-ahead. Consequential steps: choosing or changing architecture or a major technology, changing a database schema, adding a dependency or third-party service, deleting data or files the user created, deploying, creating a project agent, and changing the project's stage. Only the lead asks; a subagent stops and returns the step as an open question. Batch a task's questions into one ask. An approval covers only the step asked about. For a major decision, add what was chosen, over what, and why to the project doc it belongs in.
4. Label the claims a decision depends on: verified (cite the file, command, or link), user-provided, inferred (say from what), proposed, or unknown (say what would answer it).
5. Prefer the simplest solution that meets the requirements, the existing stack, and the framework's conventions.
6. Change only what the task needs: no drive-by refactors, renames, or reformatting. Put improvements in the report as suggestions.
7. Do not add comments to project code. Write docstrings for public functions, classes, and modules in the framework's style. No TODO or FIXME comments. Never edit the user's comments; move them with their code.
8. Before reporting done, run the tests, linters, and type checks that cover the change. Report failures and skipped checks with their output; a task with a failing check is not done.
9. Write docs for someone new to the project: main point first, plain words, short sentences, and every name, number, limit, and edge case a reader needs to act.
10. Keep the annotation index current. A change that adds, moves, renames, or deletes files, or changes how files relate, updates `.simple-eng/annotations.jsonl` with `simple-eng annotate` in the same change. Find relevant files with `simple-eng annotations --area`, `--related-to`, or `--search` instead of scanning the codebase.

### Choosing depth

- A small, reversible change needs no workflow: make it, verify it, report it.
- For larger work, follow `simple-eng:lead`: it routes the task to the build agencies (Discovery, Design, Delivery) and the specialist agencies (DevOps, Security, Performance, Testing, Legal and compliance) it needs.

### Keeping context

- Write each answer the user gives to its record in the same turn, labeled user-provided with the date. Record "Not applicable: <reason>" the same way, so it is never asked again.
- Before ending a turn that changed the focus, checkpoints, or open questions, update `docs/STATE.md`. Keep it a short index of pointers, current items first.
- Keep project facts only in the repository. Agent memory is for how the user likes to work.
- Run `simple-eng validate` after editing records or files, and `simple-eng status` to see which knowledge areas are missing.

### Closing report

State what changed, what was verified and how, what was not verified, and the remaining risks.
