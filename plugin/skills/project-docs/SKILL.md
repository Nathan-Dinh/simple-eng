---
description: Create or refresh the project documents - PRD, App Flow, UI/UX Design Brief, TRD, Backend Schema, Implementation Plan - from the user's brief (new project) or from the codebase (existing project), then close the gaps with targeted questions.
needs: []
---

# Project documents

Six documents describe what is being built and how. Each has one job; link between them instead of restating.

| Document | Path | Guidance | Done when |
|---|---|---|---|
| PRD | `docs/product/PRD.md` | `${CLAUDE_SKILL_DIR}/prd.md` | goals, users, and MVP requirements have IDs, labels, and statuses; checkpoint A assessed |
| App Flow | `docs/product/app-flow.md` | `${CLAUDE_SKILL_DIR}/app-flow.md` | every MVP journey has an entry, steps, an outcome, and its failure paths |
| UI/UX Design Brief | `docs/design/ui-ux-brief.md` | `${CLAUDE_SKILL_DIR}/ui-ux-brief.md` | design goals, design system, accessibility target, and states for critical journeys |
| TRD | `docs/architecture/TRD.md` | `${CLAUDE_SKILL_DIR}/trd.md` | quality drivers ranked; architecture and stack tied to requirements; consequential choices approved in chat with their rationale; checkpoints B and C assessed |
| Backend Schema | `docs/backend/schema.md` | `${CLAUDE_SKILL_DIR}/backend-schema.md` | entities, access patterns, API contracts, and isolation explicit; checkpoint D assessed |
| Implementation Plan | `docs/plan/implementation-plan.md` | `${CLAUDE_SKILL_DIR}/implementation-plan.md` | MVP milestones with linked requirements, dependencies, and exit checks |

Work in this order: each document builds on the ones before it. Read only the guidance file for the document in hand. `simple-eng status` lists each document as missing, draft, reviewed, or not applicable.

## 1. Choose the mode

- **New project**: little or no code, or handed off from `simple-eng:initialize-project`. Information comes from the user.
- **Existing project**: a working codebase, or handed off from `simple-eng:analyze-existing-project`. Information comes from the repository first; ask only what it cannot answer.

## 2. Gather

New project: ask the user for a brief in their own words, and say that rough notes, a pasted spec, or links all work. Say what helps most: what the product is, who it is for and the problem it solves, why now, what the first version must do and what it will not, known constraints (budget, timeline, team, hosting, data sensitivity), and technology preferences. One message is enough to start; do not turn this into a questionnaire.

Existing project: do the inspection from `simple-eng:analyze-existing-project` first, if it has not run in this session. When `simple-eng status` reports a legacy file, propose moving it to the new path with `git mv` and reshaping it to the template, keeping its content and labels; do it only after the user agrees.

## 3. Draft every document at once

Run `simple-eng docs --apply` to create the missing documents from their templates, then fill each one with what the brief or the code supports:

- Label each claim: verified (with the path or check), user-provided (with the date), or inferred (with the basis). Never invent a requirement, target, user, or history.
- Put each gap in the document's "Open questions and conflicts" table, with its impact.
- Write short facts (problem, scope, constraints, stack, commands) to their `docs/PROJECT.md` sections and link them from the documents.
- Label recommendations, such as a stack or a schema, proposed. They stay proposed until the user approves them in chat.
- If a document does not apply, write `Not applicable: <reason>` under the heading `simple-eng status` names for it, so it is not asked again.

Then tell the user which documents were drafted, how much of each is confirmed rather than inferred, and the highest-impact gaps.

## 4. Close the gaps, one document at a time

Take the documents in order. Each turn, ask a few related questions from the current document's open questions, starting with those that block later documents, and say why each matters. When the user is unsure, recommend a default with its implications and keep it proposed until they confirm. Write each answer into the document in the same turn and remove the question it settles. Move on when the document's "done when" holds or its remaining unknowns are visible.

## 5. Review and decide

A document's Status changes from `draft` to `reviewed` only when the user says they have reviewed it. A review is not an approval: consequential choices inside a document go through `simple-eng:architecture-design`, `simple-eng:database-engineering`, or `simple-eng:ui-ux-design`, which present them to the user for approval in chat. When a reviewed document later changes materially, set it back to `draft`.

## Record and hand off

- Update `docs/STATE.md` each turn: workflow `project-docs`, the current document, the next question group, blocking open questions, checkpoint status, and a "Recent changes" line (including reviews, with the date).
- Run `simple-eng validate` and `simple-eng status` after editing.
- When the documents are ready, summarize confirmed facts, assumptions, proposals waiting for approval, and open questions, and name the first milestone of the Implementation Plan as the next step.
