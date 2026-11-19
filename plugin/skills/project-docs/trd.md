# TRD guidance

Start only once the PRD's requirements are understood. If no problem or user is established, do not choose a stack or design a solution.

**Quality drivers first.** Follow `${CLAUDE_PLUGIN_ROOT}/reference/rubrics/quality-attributes.md`. Ask context-specific questions, such as latency expectations, usage and growth, acceptable downtime and data loss, authorization and sensitive data, maintenance ownership and change frequency, accessibility expectations, and operating budget, a small group per turn. Have the user rank or compare the most important attributes, and never manufacture precise weights. Turn the top drivers into measurable scenarios whose targets come from evidence or explicit user acceptance. Record them in `docs/architecture/quality-attributes.md` from `${CLAUDE_PLUGIN_ROOT}/reference/templates/quality-scenarios.md`, summarize them under "Quality drivers", and assess checkpoint B.

**New project.** Work out which capabilities the requirements actually call for: client platforms, APIs, background work, real-time needs, integrations, object storage, search, caching, queues, authentication and authorization, and observability. Include a component only when a requirement supports it.

**Existing project.** Read dependency manifests, build and CI files, infrastructure and deployment configuration, entry points, and service boundaries, and record the current architecture as verified with the paths. A config file shows intent, not deployed state. Note drift between the docs and the code.

For the architecture and each meaningful technology choice, use `simple-eng:architecture-design`; it handles C4 views, alternatives, and approvals. In "Stack and technology choices", mark each choice proposed until the user approves it, then record what was chosen, over what, and why. When the TRD is done, assess checkpoint C.
