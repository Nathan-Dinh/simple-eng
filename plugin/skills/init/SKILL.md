---
description: Set up simple-eng in this project - the CLAUDE.md rules block, project profile, working state, and a first pass over missing project knowledge.
disable-model-invocation: true
---

# Set up simple-eng in this project

1. Run `simple-eng init` (a dry run). Show the user the planned files and the CLAUDE.md diff. If CLAUDE.md already exists, say that only the block between the `simple-eng` markers is managed and the rest stays untouched. After the user confirms, run `simple-eng init --apply`. Re-running after a plugin update refreshes only the block and the version marker; it never overwrites `docs/PROJECT.md` or `docs/STATE.md`.
2. Run `simple-eng status` to list the knowledge areas and their records.
3. Investigate the areas marked `investigate` (stack, commands, environments, architecture, data model, UI): read manifests, build and CI files, entry points, schemas and migrations, and UI code. Write findings into each area's record section, labeled verified with the file paths, or inferred with the basis. Do not run destructive commands, install dependencies, or call external services. For an area that clearly does not apply, write `Not applicable: <reason and evidence>`.
4. If a fact already lives in another file (for example `ARCHITECTURE.md`), point the area at it instead of copying: in `.simple-eng/config.json`, set `"areas": {"architecture": {"record": "ARCHITECTURE.md#Overview"}}`.
5. Ask about the areas marked `ask`, a few related questions at a time, starting with what the user's current goal needs. Say why each answer matters. Write each answer to its section in the same turn, labeled user-provided with today's date.
6. `init --apply` creates `.simple-eng/areas.json` with a `project` area, and annotates the files it created. For an existing codebase, the annotation index for the rest of the code is built by `simple-eng:analyze-existing-project`; for a new project, it grows as files are added.
7. In `docs/STATE.md`, list unanswered areas under "Open questions" (with why each matters), set "Current focus", and add a "Recent changes" line.
8. Run `simple-eng validate` and `simple-eng status`. Report what was recorded, what is still missing, and the suggested next workflow: `simple-eng:analyze-existing-project` for an existing codebase (it drafts the project documents from the code), or `simple-eng:initialize-project` for a new one (it starts from the user's brief).
