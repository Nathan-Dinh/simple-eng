---
description: Assess an engineering checkpoint (A scope, B quality, C architecture, D data and security, E feature design, F verification, G release) before a consequential step - evidence, readiness, and what the user must approve.
needs: []
---

# Engineering checkpoints A-G

A checkpoint makes a consequential step traceable; it is not ceremony for minor work. For a task that spans several, assess only the ones its risk and scope call for. Each checkpoint ends as passed, deferred, or blocked.

| Checkpoint | Focus | Ready to proceed when |
|---|---|---|
| **A — Product scope and requirements** | Problem, users, use cases, MVP, constraints, success, requirements, open questions | Important requirements are identified and labeled; material conflicts and unknowns are visible; scope, out-of-scope, and the next discovery step are understood. Unknowns may remain if they are not hidden. |
| **B — Quality attributes** | Priorities, constraints, scenarios, accepted trade-offs | The prioritization method, its limits, and the leading drivers are recorded; scenario measures are evidence-backed, user-accepted, or explicitly open. |
| **C — Architecture and technology** | Boundaries, useful C4 views, alternatives, recommendation, operational consequences | The architecture is tied to requirements and quality drivers; evidence, alternatives, and trade-offs are visible; consequential commitments are approved by the user. |
| **D — Database and security model** | Entities, cardinality, access patterns, tenancy, privacy, lifecycle, migration, recovery | Data and trust boundaries, authorization and isolation, constraints, and migration risks are explicit; the user approves schema and security choices before production-impacting work. |
| **E — Feature design** | User problem, scope, acceptance criteria, affected components, data, UI, API, tests | Behavior and edge cases are observable; dependencies, design, and risks are understood; consequential choices are approved or remain proposed. |
| **F — Implementation and verification** | Implementation, tests, quality scenarios, docs, deviations | Acceptance criteria have evidence; checks actually ran and their limits are recorded; deviations and unverified risks are visible. |
| **G — Release readiness and maintenance** | Rollout, recovery, monitoring, support, known risks, follow-up; every specialist agency's release review | All five specialist reviews ran; no blocking finding is open unless the user accepted the risk; rules skipped for the stage are listed; release, rollback or recovery, and operational ownership are understood and accepted by the user. If no release is in scope, say so. |

## At each checkpoint

1. State the question being decided.
2. Summarize the evidence and its limits, with fact labels (the simple-eng rules in CLAUDE.md). Readiness (enough evidence) is separate from approval (the user's go-ahead).
3. Identify conflicts, unknowns, options, and consequences.
4. For a consequential step, present the choice and its trade-offs in chat and wait for the user's go-ahead. The user may approve, ask for alternatives, or defer.
5. Record the outcome in the "Checkpoints" table in `docs/STATE.md` with a link to the project doc that holds the evidence and rationale, plus the next action. A completed checklist or a recommendation is not approval.

## Release checkpoint (G)

Before a release, the lead runs every specialist agency in parallel: `simple-eng:devops`, `simple-eng:security`, `simple-eng:performance`, `simple-eng:testing`, and `simple-eng:legal-compliance`. Each reviews the whole release in two passes, a labor-tier checklist and then a judgment-tier review, and at this checkpoint both passes always run (`${CLAUDE_PLUGIN_ROOT}/reference/policies/specialist-review.md`).

1. Run `simple-eng stage` and pass the stage to every review. Rules tagged for a later stage are skipped; the combined report lists each skipped rule and why. Rules tagged `[all]` are never skipped.
2. Start the five checklist passes in one message, then the five in-depth passes once their checklists return.
3. Combine the findings by severity. A blocking finding stops the release until it is fixed or the user accepts the risk in chat. Present conflicts between agencies with both positions and the trade-off.
4. Deploying is consequential: ask for the go-ahead with the findings in hand. Record G's outcome in `docs/STATE.md`.

Moving to a later stage (prototype to pre-production to production) is also consequential. Propose it when the project is about to serve real users, list the rules that would start to apply, and run `simple-eng stage NEW` only after the user agrees.
