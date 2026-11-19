# UI/UX Design Brief guidance

**New project.** Ask who uses the interface and in what context (device, frequency, expertise), what it should feel like, which products to emulate or avoid, which brand assets exist, which devices and viewports must work, and which accessibility target applies. If no target is known, recommend one (for example WCAG 2.2 AA) and keep it proposed until the user confirms it; never assume a compliance target.

**Existing project.** Inspect the design system, component library, theme and token files, styling framework, layout primitives, and existing screens. Record what exists, labeled verified with the paths, and build on it rather than proposing a new system.

For each critical journey in the App Flow, specify the loading, empty, error and recovery, disabled, and success states. Check consequential choices against `${CLAUDE_PLUGIN_ROOT}/reference/rubrics/ux-principles.md` and name the principle behind each. Deeper design work, prototypes, and design DECs go through `simple-eng:ui-ux-design`.

If the product has no user interface, write `Not applicable: <reason>` under "Users and design goals".
