# Performance standards (owner: Performance)

Tags: `[all]` applies at every stage and is never skipped; `[pre-production]` and `[production]` apply from that stage on. See `${CLAUDE_PLUGIN_ROOT}/reference/policies/specialist-review.md`.

## Budgets and measurement

- [pre-production] Each critical path has a performance budget (for example p95 latency under a stated load), recorded in the TRD's quality drivers.
- [pre-production] Critical paths are measured against their budget, and the measurement method and result are recorded.
- [pre-production] Critical paths are load tested against their budget before release.
- [all] Every optimization is backed by a measurement taken before and after the change.

## Data access

- [all] No database query runs inside a loop (no N+1 queries); related data is loaded in bulk or joined.
- [all] Endpoints that return lists are paginated, with a maximum page size.
- [pre-production] Queries on the main access paths use an index or key; the query plan is checked for the slowest ones.

## Work outside the request

- [pre-production] Work that is slow or scales with data size (exports, emails, image processing, bulk updates) runs in a background job, not in the request.
- [pre-production] Each cache states what it holds, how long, and what invalidates it.
