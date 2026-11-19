# Implementation Plan guidance

Build the plan from the PRD, App Flow, TRD, and Backend Schema as they stand. Ask the user for priorities, deadlines, team size, and what must be shown first; the documents cannot answer those.

**Existing project.** Start from what already works, verified by code and tests, and plan the gap to the PRD. Use open issues, TODOs, failing or skipped tests, and choices waiting for approval as inputs, labeled with their source.

Shape milestones as thin end-to-end slices a person or a test can observe, smallest useful slice first. Each milestone names its goal, its deliverables, the REQ IDs (and FEAT specs) it delivers, what it depends on (including choices the user must approve first), and an exit check that can actually run. Put setup work (repository, CI, environments) in the first milestone only as far as the next slice needs. List work the documents do not support yet under "Not planned yet" rather than guessing.

A milestone's status changes only from work that happened and was verified. Larger features within a milestone go through `simple-eng:feature-development`.
