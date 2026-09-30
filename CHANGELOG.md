# Changelog

## 1.0.0 — 2026-09-30

First independently versioned GrindingStation release, based on the existing
fork with selected upstream gameplay fixes through Burning Lotus 1.5.5.

- Custom GrindingStation UI, icon and colors; application self-updates disabled.
- Historic navigation and deck matching across client sizes, including 1366×768
  and 1920×1080; visually verified Home can override stale menu state throughout
  the navigation sequence.
- Quest reroll verification and local text history with 48-hour retention.
- Ten-second protection after result-screen clicks; reward handling and
  Reconnect detection in the queue loop.
- Imported guarded cast, target and payment recovery improvements.

The next release will address the remaining flow coordination, post-game
latency and reconnect coverage described in docs/flow-optimization.md.

Validation: full suite executed (937 tests: 935 passed, 1 skipped, 1 known
failure in `test_combat_blocks.DeclareBlocksTest.test_the_time_budget_stops_scanning_and_submits_what_is_assigned`).
The combat-block time-budget test already failed before the navigation fixes;
this release does not claim to resolve it. Pyright was not available in the
local build environment.
