# Design standards (owner: Design)

Each rule is a check that passes or fails. The tag says the earliest project stage it applies at (`simple-eng stage` shows the current one): `[all]` applies from the first prototype, `[pre-production]` once the project is preparing for real users, `[production]` once it serves them. When a rule is skipped for the stage, the report names it and why. All agencies apply these while designing and building; Design reviews any task that touches them.

## Framework conventions

- [all] The code follows the framework's recommended project structure and coding style (for example, a Django project uses Django's app layout).
- [all] The ecosystem's standard formatter and linter (for example Ruff for Python, ESLint and Prettier for JavaScript) are configured in the repo, so style is enforced by tools, not review.

## Layered architecture

The four layers map onto the framework's own structure; no separate folder layout is imposed. They are also the `layer` values in the annotation index.

- Presentation: endpoints and UI. Handles input and output.
- Application: use cases. Coordinates the other layers.
- Domain: business logic and rules.
- Infrastructure: databases, external APIs, queues, and other external systems.

When a framework convention conflicts with these rules, the framework wins and the layer rules apply only where they fit. For example, Django models are both domain objects and database access, so the ORM is not wrapped in repositories, but business logic still stays out of views.

- [all] Presentation code contains no business rules.
- [all] Domain code imports nothing from the Presentation, Application, or Infrastructure layers, where the framework allows it.
- [all] Dependencies point inward: Presentation calls Application, Application calls Domain.
- [pre-production] Infrastructure implements interfaces that the Application and Domain layers define, where the framework allows it.

## System design

Common problems use established patterns instead of new inventions.

- [pre-production] Every call to an external system has a timeout, and retries use backoff.
- [pre-production] Operations that can be retried (payments, webhooks, queue consumers) are idempotent.
- [pre-production] Slow or bulk work runs in a background queue, not in the request.
- [pre-production] Public endpoints are rate limited.
- [all] Every cache has a stated invalidation rule.

## Data design

- [all] Every table or collection has one owning domain; other domains read it through that domain's code, not directly.
- [all] The schema is designed from the access patterns: the main queries are listed in the Backend Schema.
- [pre-production] Each main query is backed by an index or key.
- [all] Every migration is reversible, or states why it cannot be reversed.
- [production] Migrations on live data are backward compatible with the running code, so deploys need no downtime.

## Error handling

- [all] No exception is caught and ignored. Each one is handled, or logged and re-raised.
- [all] Errors are translated at layer boundaries: Infrastructure errors become domain errors before they reach the Application layer, and domain errors become responses in the Presentation layer.
- [all] The API returns errors in one consistent format, following the framework's convention where it has one.
- [all] Users never see stack traces, SQL, file paths, or other internal details; those go to the logs.
