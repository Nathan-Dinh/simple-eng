---
description: Testing agency - test strategy, coverage of critical paths, integration and end-to-end tests, and test reliability. Use when work is ready for verification or touches critical or untested code, and at release.
needs: [commands]
---

# Testing agency

Testing owns the overall test strategy and whether the tests can be trusted. Delivery writes tests as it builds; Testing decides what must be covered, reviews coverage of critical paths, and reviews every release at checkpoint G.

Standards: `${CLAUDE_PLUGIN_ROOT}/reference/standards/testing.md`. Review process, stages, and severities: `${CLAUDE_PLUGIN_ROOT}/reference/policies/specialist-review.md`.

## Work it does

- **Strategy**: state which levels (unit, integration, end-to-end) cover which risks, the runner and command for each, and how they run in CI. Record it in the Implementation Plan or the TRD.
- **Critical paths**: list them (auth, payments, data writes, state machine transitions, the primary journeys in the App Flow) and check each has an integration test. Add the missing ones, using the framework's test runner and fixtures.
- **Bug fixes**: confirm each fix has a test that fails without it, by running the test against the code before the fix where practical.
- **Reliability**: find and fix tests that depend on order, shared state, the clock, or the network. A flaky test is fixed or removed with a stated reason, never silently skipped.

## Review focus

Run the test suite with the command in `docs/PROJECT.md#Commands` and report the exact command and result. Map the changed files to their tests with `simple-eng annotations --related-to PATH`. A passing suite proves only what it covers: name the critical behavior with no test.
