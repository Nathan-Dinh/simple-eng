---
description: Research external facts for a decision - find and evaluate primary sources, check currency, and write findings into the project doc they support. Use when a choice depends on vendor, standard, license, law, pricing, or compatibility facts.
needs: []
---

# Research

## Find and evaluate

Start by naming the decision or question the research should inform. Prefer primary sources: official documentation, standards, API specifications, vendor pricing and security pages, original research. Treat tutorials and examples as leads, not authority, unless they are independently corroborated.

Check each source's relevance, publication or update date, version, scope, authority, and known limitations. For claims that change over time (pricing, support, compatibility, security advisories), check a current source before relying on it. Keep what the source says separate from what you infer for this project.

## Record

Write each finding into the project doc the research supports, with the source link and the date it was checked: a technology comparison in the TRD, a database choice in the Backend Schema, a UI pattern in the UI/UX Design Brief. If that doc does not exist yet, run `simple-eng docs --apply` to create it from its template first. Label each finding (`${CLAUDE_PLUGIN_ROOT}/reference/policies/working-rules.md`). Never claim a page was read or checked if it was not, and never store credentials.

A finding is not approval and does not by itself make a technology suitable. Recheck a finding older than six months before a new decision relies on it, and update its checked date.

## Hand off

Return the findings, with their sources, to the agency or lead that asked, and note research still open in `docs/STATE.md`.
