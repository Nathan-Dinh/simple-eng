---
description: Design or change persistent data - entities, cardinality, access patterns, tenancy and authorization isolation, retention, migrations, and recovery. Use for schema, migration, database choice, or multi-tenant data work.
needs: [requirements, stack]
---

# Database engineering

## Discover before designing

Inspect the existing schema, migrations, ORM or query patterns, access controls, tests, and deployment constraints first. Ask the smallest useful set of questions about:

- core entities, ownership, relationship cardinality, and lifecycle;
- read and write access patterns, queries, reporting, transaction boundaries, consistency, and expected volume;
- tenant model, authorization boundaries, sensitive fields, privacy, auditability, retention, deletion, and residency;
- migration, rollback, backup, recovery point and time objectives, and operational ownership.

Answer what you can from the repository and label the rest. Surface conflicts (for example, retention obligations against deletion expectations) instead of choosing silently.

## Select and design

Compare relational, document, key-value, graph, or other models only when access patterns and consistency needs justify it, and keep the established technology unless a change is justified. Document entities, ownership, cardinality, keys, foreign keys, constraints, normalization and denormalization choices, indexes tied to real queries, transaction consistency, data lifecycle, and the access-control model. Add an ER diagram where it helps. Apply the data-design rules in `${CLAUDE_PLUGIN_ROOT}/reference/standards/design.md`: one owning domain per table, a schema designed from listed access patterns, reversible migrations, and backward-compatible migrations on live data. Record it, with the API surface over the data, in the Backend Schema, `docs/backend/schema.md`, using `${CLAUDE_PLUGIN_ROOT}/reference/templates/backend-schema.md`.

For multi-tenant systems, define how tenant identity is established, propagated, authorized, and enforced at every read and write boundary, including background jobs, admin flows, exports, and caches. A tenant column alone does not provide isolation. Tenant and security design, and any schema change, are consequential: present them in chat with their trade-offs and wait for the user's go-ahead (the simple-eng rules in CLAUDE.md). Record the approved choice and why in the Backend Schema.

## Migrate and verify

Describe migration order, compatibility with running application versions, backfill and locking risks, validation, rollback or forward recovery, backup implications, and the test plan. Do not create or run production migrations until the user has approved the schema and security design.

Verify constraints and access boundaries with tests, including negative cross-tenant cases where they apply. Record the exact checks that ran and their limits, and link schema choices to requirements and tests.

## Record and hand off

Update `docs/STATE.md`: checkpoint D status, choices waiting for the user, migration risks still open, next step.
