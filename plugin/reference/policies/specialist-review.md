# Specialist reviews

How the five specialist agencies (DevOps, Security, Performance, Testing, Legal and compliance) review work. Each agency owns one standards file in `reference/standards/`. A review checks that file's rules against the work and returns findings in the standard report.

## When a review runs

- **Task review**: the task touches the agency's concern (the lead's routing table says when). Scope: the files the task changed and the files related to them (`simple-eng annotations --related-to PATH`).
- **Release review**: checkpoint G. Every specialist agency reviews the release in parallel. Scope: the whole project, area by area (`simple-eng areas`, then `simple-eng annotations --area NAME`).

## Proportionality

`simple-eng stage` gives the project stage: prototype, pre-production, or production. Each rule is tagged with the earliest stage it applies at. A rule tagged for a later stage is skipped, and the report lists each skipped rule and why ("stage is prototype"). Rules tagged `[all]` are never skipped; they include keeping secrets out of the repo, requiring authorization on endpoints, validating outside input, and isolating tenants.

## Two passes

The review costs less than the work it reviews, so it runs in two passes. The lead starts both, because subagents cannot start subagents.

1. **Checklist pass** (`simple-eng:labor`). Give it the agency skill, its standards file, the stage, and the scope. It marks every rule pass, fail, skipped for the stage, not applicable (with the reason), or unclear, and cites the file and line or the command it ran.
2. **In-depth pass** (`simple-eng:reviewer`). Only when the checklist flags a fail or unclear rule; at the release checkpoint it always runs. Give it the flagged rules and the checklist report. It confirms or dismisses each one, assigns a severity, and says what would fix it.

## Severity

- **blocking**: a rule in force is failed in a way that risks a security breach, data loss or exposure, legal liability, or an outage; every failed `[all]` rule is blocking. It stops the task until it is fixed or the user accepts the risk.
- **should fix**: a rule in force is failed and the risk is contained. Fix it in this task, or return it as an open question.
- **note**: an improvement, or a rule that will apply at a later stage.

## Findings

Each finding names the rule, the result, the severity, a fact label with its source (file and line, command output, or link), and the fix. A pass needs evidence too: "verified: `rg -n 'SECRET' src/` found nothing" rather than "looks fine".

## Doing the agency's own work

When a task's main work is in the agency's area (for example DevOps setting up CI), the agency follows its own standards while doing it, and Testing or Security review it like any other task.
