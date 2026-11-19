# PRD guidance

**New project.** From the brief, establish what problem is being solved, who experiences it, and what outcome would count as success. Then establish the primary use cases, expected usage, MVP essentials versus optional scope, and what is explicitly out of scope. Ask what is most uncertain. Ask about budget, timeline, team, legal, privacy, and contractual constraints, integrations, hosting, and data sensitivity. Follow up only where an answer changes feasibility, authorization, or architecture.

**Existing project.** Infer users and use cases from the README, docs, routes, UI copy, and tests, and label them inferred with the path. The code cannot tell you goals, success metrics, priorities, or what is out of scope, so ask about those.

Distinguish outcomes from features: "users need to find past orders quickly" is an outcome; "add a search bar" is a feature. Every goal needs a measurable success metric, or an open question saying none is agreed yet.

Turn confirmed answers into requirements with stable `REQ-####` IDs. Each one gets a type (functional or non-functional), measurable acceptance, a fact label and a requirement status as defined in `${CLAUDE_PLUGIN_ROOT}/reference/policies/working-rules.md`, and its source. Look for contradictions, missing actors, conflicting acceptance criteria, and incompatible constraints, such as scope against timeline. Present each conflict with its options and let the user choose; do not resolve it silently. A constraint is confirmed only when the user confirms it or evidence verifies it.

Record problem, scope, and constraints in their `docs/PROJECT.md` sections. The PRD holds goals, personas, stories, requirements, rules, and out of scope. When the PRD is done, assess checkpoint A with `simple-eng:checkpoints`.
