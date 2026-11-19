---
description: Discovery for a new project or a fresh start - take the user's brief, draft the PRD, App Flow, UI/UX Brief, TRD, Backend Schema, and Implementation Plan, and close gaps across sessions. Use when no established codebase or product definition exists.
needs: []
---

# Initialize a project

Begin with discovery, not code generation. If no problem or user is established, do not choose a stack or design a solution.

1. Run `simple-eng status`. If `docs/STATE.md` "Current focus" shows initialization under way, resume at the recorded document and question group instead of starting over.
2. Use `simple-eng:project-docs` in new-project mode: ask for a brief, draft all six documents from it, then close the gaps one document at a time.
3. Ask a few related questions per turn, never the whole question bank. A later document can start while minor unknowns remain, as long as they are visible in its open questions and in STATE.md.

## Record and hand off

- Every answer goes to its document or `docs/PROJECT.md` section in the same turn.
- After each turn that moves discovery forward, update `docs/STATE.md`: current document, next question group, open questions with why they matter, checkpoint status, and a "Recent changes" line.
- When initialization is ready to move on, summarize confirmed facts, assumptions, recommendations, open questions, and deferred decisions separately, and name the next checkpoint and the highest-impact remaining questions. Readiness does not require every unknown to be resolved.
