# Security standards (owner: Security)

Tags: `[all]` applies at every stage and is never skipped; `[pre-production]` and `[production]` apply from that stage on. See `${CLAUDE_PLUGIN_ROOT}/reference/policies/specialist-review.md`.

## Trust boundaries and data flows

- [pre-production] Data flows between domains, applications, and external systems are mapped in the TRD. Each trust boundary states what is validated and authorized when data crosses it.
- [pre-production] Stateful workflows (orders, payments, approvals) are explicit state machines: named states, allowed transitions, and who can trigger each transition.
- [pre-production] A threat model lists the main threats to each trust boundary and how each is handled.

## Authentication and authorization

- [all] Every endpoint requires authorization by default; public endpoints are marked as public explicitly.
- [all] Authorization is checked on the server for every read and write, not only hidden in the UI.
- [all] In a multi-tenant system, every query is scoped to the tenant, and a test proves one tenant cannot read another's data.
- [all] Passwords are hashed with a slow, salted algorithm (for example Argon2 or bcrypt), never stored or logged in plain text.

## Input and output

- [all] All input from outside a trust boundary is validated before use (type, length, format, allowed values).
- [all] Queries are parameterized; no user input is concatenated into SQL, shell commands, or templates.
- [all] Output rendered in HTML is escaped by the framework's templating, not built by string concatenation.

## Secrets

- [all] Secrets are never in code or in the repo; they come from environment variables or a secret store.
- [all] Secrets, tokens, and passwords never appear in logs, error messages, or URLs.

## Dependencies

- [pre-production] Dependencies are scanned for known vulnerabilities in CI.
- [pre-production] Known high or critical vulnerabilities in dependencies are fixed or have a recorded reason and a date to revisit.
