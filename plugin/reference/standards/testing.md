# Testing standards (owner: Testing)

Tags: `[all]` applies at every stage and is never skipped; `[pre-production]` and `[production]` apply from that stage on. See `${CLAUDE_PLUGIN_ROOT}/reference/policies/specialist-review.md`.

## Coverage of what matters

- [pre-production] Critical paths have integration tests: auth, payments, data writes, and every transition of a state machine.
- [all] Every bug fix includes a test that fails without the fix.
- [all] Each acceptance criterion of a feature in scope has a test or a recorded manual check.

## Reliable tests

- [all] Tests are independent: they do not rely on run order, shared state, wall-clock timing, or network calls outside their control.
- [all] Tests use the framework's test runner and conventions.
- [all] A failing or flaky test blocks release. It is fixed, or removed with a stated reason, never silently skipped.

## Strategy

- [pre-production] The test strategy is stated in the TRD or Implementation Plan: which levels (unit, integration, end-to-end) cover which risks, and how tests run in CI.
- [pre-production] End-to-end tests cover the primary journeys in the App Flow.
