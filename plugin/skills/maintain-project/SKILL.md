---
description: Fix bugs, upgrade dependencies, run migrations and refactors, and pay down technical debt in an established project, with surgical changes and recorded verification.
needs: [commands]
---

# Project maintenance

## Establish scope and evidence

Inspect the affected code, tests, docs, architecture boundaries, and dependency policy before changing files. For a bug, establish the observed and expected behavior and a reproduction; keep evidence apart from hypotheses. Incident response belongs to `simple-eng:devops`, and security reviews to `simple-eng:security`; this skill makes the fix they hand over. Preserve timestamps and sources, and never invent a timeline. Ask only for information that changes the diagnosis or a safe fix.

## Assess impact

Identify the affected users, data, and components, compatibility and migration effects, reversibility, deployment and operations, privacy and security, and cost. Check for conflicts with the choices recorded in the project docs, and do not resolve consequential conflicts silently. If an approved choice must change, present the change and its trade-offs to the user and update the rationale in the doc once they agree (the simple-eng rules in CLAUDE.md).

## Change and verify

Choose the verification approach with `${CLAUDE_PLUGIN_ROOT}/skills/feature-development/tdd.md`. Make a surgical, complete change that keeps to the Design standards (`${CLAUDE_PLUGIN_ROOT}/reference/standards/design.md`), update directly related docs, and run the smallest relevant tests, linters, and builds. For upgrades and migrations, verify compatibility and the recovery path. Report commands and results, including failures and checks that did not run. A clean test run does not prove untested requirements or production state.

## Record and hand off

For non-trivial work, update `docs/STATE.md` with the change, verification scope, unresolved risks, and next action.
