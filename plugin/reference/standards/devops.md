# DevOps standards (owner: DevOps)

Tags: `[all]` applies at every stage and is never skipped; `[pre-production]` and `[production]` apply from that stage on. See `${CLAUDE_PLUGIN_ROOT}/reference/policies/specialist-review.md`.

## Observability

- [pre-production] Logs are structured (for example JSON) and carry a request or correlation ID.
- [pre-production] Every service emits metrics for request rate, error rate, latency, and resource saturation.
- [pre-production] When there is more than one service, traces follow a request across layers and services.
- [all] Logs never contain secrets, passwords, tokens, or unmasked personal data.
- [pre-production] Each service has a health check endpoint.
- [production] Error rate and latency have alerts with a stated threshold and a named person or rotation who receives them.

## Configuration

- [all] Configuration comes from environment variables or a config service, never from values hard-coded per environment.
- [pre-production] The same build artifact is deployed to every environment; only configuration differs.

## Build and deploy

- [pre-production] CI runs the tests, linters, and dependency scan on every change before it can merge.
- [pre-production] Database migrations run as a step of the deploy, not by hand.
- [production] Every deploy has a rollback plan, and the plan has been tried at least once.
- [production] Infrastructure is defined as code in the repo, not configured by hand in a console.

## Incidents

- [production] An incident record keeps the timeline with real timestamps and sources, the impact, the cause once known, and follow-up actions. Nothing in it is invented.
