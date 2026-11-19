# Backend Schema guidance

**New project.** From the PRD and App Flow, list what the product stores and who owns it, then ask the smallest useful set of questions about:

- relationships, cardinality, lifecycle, and expected volume;
- read and write access patterns, queries and reports, and consistency needs;
- the operations or API that clients call, and who may call each one;
- tenancy, sensitive fields, retention, deletion, and audit obligations.

**Existing project.** Read the schema, migrations, ORM models, API route handlers or OpenAPI and GraphQL definitions, and authorization middleware. Record entities and endpoints as verified with the paths. Access patterns inferred from queries are labeled inferred.

Tie each entity, index, and endpoint to a requirement or access pattern. Surface conflicts, such as retention obligations against deletion expectations, instead of choosing silently. Schema, tenancy, and security choices are consequential: design them with `simple-eng:database-engineering`, which presents them to the user for approval, and assess checkpoint D.

If the project stores no persistent data and has no backend, write `Not applicable: <reason>` under "Entities and cardinality".
