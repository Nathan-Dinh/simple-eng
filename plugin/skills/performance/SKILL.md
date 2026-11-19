---
description: Performance agency - performance budgets, profiling, query analysis, load testing, and caching. Use when a task touches a hot path, a database query, or a performance budget, and at release.
needs: []
---

# Performance agency

Performance owns how fast the project responds and how well it holds up under load. It does performance work, reviews any task that touches a hot path or a query, and reviews every release at checkpoint G.

Standards: `${CLAUDE_PLUGIN_ROOT}/reference/standards/performance.md`. Review process, stages, and severities: `${CLAUDE_PLUGIN_ROOT}/reference/policies/specialist-review.md`.

## Work it does

- **Budgets**: agree a budget with the user for each critical path (for example "search p95 under 300 ms at 50 requests per second") and record it in the TRD's quality drivers. Never invent a target.
- **Measure first**: before optimizing, measure with the framework's profiler, query log, or a benchmark, and record the command and the numbers. After the change, measure the same way. An optimization without a before-and-after measurement is not done.
- **Queries**: look for N+1 patterns (a query inside a loop, lazy loading in templates or serializers), missing indexes on the main access paths, and unbounded result sets. Check the query plan for the slowest ones.
- **Load testing**: at pre-production and later, load test critical paths against their budgets with a tool that fits the stack, against a non-production environment.
- **Caching**: add a cache only for a measured need, and state what it holds, its lifetime, and what invalidates it.

## Review focus

Look at loops that touch the database or the network, list endpoints, ORM relationship loading, serializers, template rendering of related objects, work done in the request that could run in the background, and cache reads and writes.
