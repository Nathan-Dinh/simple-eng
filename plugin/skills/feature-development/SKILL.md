---
description: Build a feature end to end - discover the user problem, specify observable acceptance criteria, design, implement test-first where it fits, and verify. Use for new features, user stories, or substantial behavior changes.
needs: [problem-users, commands]
---

# Feature development

## 1. Discover

Establish nine items for every feature: the user problem, actors, expected behavior, success measure, edge cases, affected components, required data, dependencies, and security and privacy implications. An item that does not apply is `Not applicable: <reason>`.

Answer what you can first from the existing code and the project documents (PRD, App Flow, TRD, Backend Schema). They are sources for the items, not a substitute for them. A document claim keeps its own label (`${CLAUDE_PLUGIN_ROOT}/reference/policies/working-rules.md`) and its path as source; an inferred claim, or one from a `draft` document, is not confirmed.

Then ask a small group of consequential questions, only about items that are still unknown and about conflicts between the documents, the code, and the request. Present each conflict with its options and say why each answer matters; do not resolve it silently.

End discovery with a checklist of the nine items: `Item | Answer | Label | Source`. A substantial feature records it in its spec; a small change shows it in the reply. Mark what stays unresolved, and do not move on while an item that changes scope, data, or permissions is unknown. When a confirmed answer contradicts a project document, report it as drift rather than editing the document silently.

## 2. Specify

For a substantial feature, write a short spec at `docs/features/FEAT-####.md` from `${CLAUDE_PLUGIN_ROOT}/reference/templates/feature.md`, starting from the discovery checklist; later sections expand its items rather than restate them. Cover problem, scope and out-of-scope, stories, requirements with observable acceptance criteria, dependencies, affected components and data, relevant quality attributes, and open questions. A small change needs no document. Resolve conflicting requirements or acceptance criteria with the user; do not invent a target, business rule, or permission. When the feature design is consequential, assess checkpoint E.

## 3. Design

Work out the contract or API, schema and migration, UI, state, integration boundaries, error behavior, security, tests, rollout, and rollback. Hand off to `simple-eng:architecture-design`, `simple-eng:database-engineering`, or `simple-eng:ui-ux-design` where their scope applies. Check for conflicts with the choices recorded in the project docs, and get the user's go-ahead in chat on consequential choices before implementing them.

## 4. Test and implement

Choose the verification approach with `${CLAUDE_SKILL_DIR}/tdd.md`. Follow the existing architecture and conventions, make the smallest complete change, and avoid unrelated refactoring. Record any significant deviation from the accepted design.

## 5. Verify

Check each acceptance criterion and applicable quality scenario. Run targeted tests and relevant regression checks. Review security and privacy, migrations, error behavior, observability, accessibility where relevant, and docs. Update the feature's status only from work that actually happened.

## Record and hand off

Update `docs/STATE.md` (feature, checkpoint E or F status, next step), and the feature's milestone in `docs/plan/implementation-plan.md` when one exists. The closing report covers what changed, requirement and acceptance coverage, checks run with exact commands and results, checks not run, deviations, and remaining risks.
