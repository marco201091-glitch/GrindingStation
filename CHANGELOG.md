# Changelog

## 1.1.0-dev — in development

- Post-match dismissal and queue handoff now share one cancellable cycle per
  match. Arena readiness is checked after a 2-second minimum and polled up to
  15 seconds; stale callbacks cannot restart a stopped or newer session.
- Victory/Defeat uses one Continue click at a time and preserves the required
  10-second wait before checking or clicking again.
- Historic and Starter share a stable, title-confirmed reward Claim path; the
  queue leaves the screen as soon as the Reward title disappears.
- A session reconnect monitor runs outside the queue loop, serializes its click
  against menu navigation, and pauses game actions until Arena emits new game
  state after reconnect.
- Queue Play is a single click; retries wait for state evidence instead of
  sending a second click to an unverified screen.
- Menu state now follows the latest explicit log transition; incidental format
  and deck names no longer invent Historic/My Decks/Find Match state.
- Match completion and unknown loading scenes invalidate prior state; the
  incremental tracker retains explicit state when its diagnostic tail rotates.
- Non-1920×1080 clients go directly to normalized image matching, avoiding an
  unnecessary native-size timeout on every lookup.
- Rotation and cast-acknowledgement tests isolate recovery probes from the live
  desktop, preventing screen-dependent waits during the test suite.
- Remaining work and acceptance checks: docs/development-1.1.md.

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
