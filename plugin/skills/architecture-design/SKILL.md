---
description: Design or change system architecture and choose technologies - boundaries, C4 views, layers, and alternatives weighed against quality drivers, approved by the user in chat. Use for architecture, stack, or major component choices.
needs: [problem-users, requirements, quality-priorities, constraints]
---

# Architecture and technology design

Run `simple-eng status --workflow architecture-design` first. Investigate or ask about the blocking areas before committing to anything consequential.

## Discover and bound

Review requirements, quality scenarios, repository structure, current architecture, dependencies, deployment shape, and the rationale already recorded in the TRD. Confirm the system's purpose, actors, boundaries, external systems, constraints, and open assumptions. Identify only the capabilities the requirements support (APIs, background processing, real-time, integrations, storage, search, caching, queues, identity, observability, deployment). If a critical input is missing, say so before choosing a component.

## Model

Use C4 at the levels that help:

- **System context**: users, system boundary, external systems, responsibilities, key data exchanges.
- **Container**: deployable or runtime units, responsibilities, interfaces, data stores, communication.
- **Component**: internal responsibilities and dependencies, only when it clarifies a real design or change.
- Code-level detail only when the implementation complexity justifies it.

Document trust boundaries, important data flows, integration contracts, failure modes, and deployment topology where relevant. Use Mermaid only when it communicates more clearly than prose and matches the implementation. Record the result in the TRD, `docs/architecture/TRD.md`, using `${CLAUDE_PLUGIN_ROOT}/reference/templates/trd.md`.

## Evaluate choices

Apply the Design standards (`${CLAUDE_PLUGIN_ROOT}/reference/standards/design.md`): framework conventions, the four layers mapped onto the framework's structure, established system-design patterns, and error handling. Follow `${CLAUDE_PLUGIN_ROOT}/reference/rubrics/technology-selection.md`, and check priorities against `${CLAUDE_PLUGIN_ROOT}/reference/rubrics/quality-attributes.md`. Prefer the existing technologies unless evidence justifies a change. Do not introduce a service, abstraction, or dependency without a requirement.

Present each consequential choice in chat with its alternatives, evidence, and consequences, and wait for the user's go-ahead (the simple-eng rules in CLAUDE.md); until then it stays proposed. Once approved, record what was chosen, over what, and why under "Stack and technology choices" in the TRD. Where a choice also shapes data or security boundaries, assess checkpoint D as well as C.

## Verify and maintain

Trace choices to requirements, scenarios, and evidence. Define how each relevant quality will be evaluated, and do not call an attribute achieved without a check. When an approved choice conflicts with new evidence, present the change and its trade-offs to the user, and update the rationale in the TRD once they agree.

## Record and hand off

Update `docs/STATE.md`: checkpoint C status, choices waiting for the user, open questions, next step.
