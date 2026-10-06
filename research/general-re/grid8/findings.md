# R-GRID8 — eight-car start-grid course audit

**Status: READY FOR HUMAN AUDIT.** This phase checks only the physical placement
of eight already-supported Quick Race participants. R-AI2.1's normal Quick Race
capacity through eight cars remains **CLOSED / CONFIRMED_BY_RUNTIME**; this work
does not reopen engine capacity, Results, HUD, AI, or Replay.

Static corpus evidence covers 39 registered scene IDs (`0..38`) and 36 distinct
canonical `RaceTest` resources. Each resource contains `Car0..Car7` actor
templates and a `StartArea`; native `0x0048EB40` generates a count-based grid.
These facts establish resource coverage, not physical clearance. All 36 runtime
rows therefore start as `NOT_TESTED`.

The universal candidate is built from exact retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. It
retains the R-AI2.1 eight-car setup and deterministic stock roster while
replacing only the `Track == 10` predicate with a fail-closed unsigned
`Track <= 38` check. The same race, one-human, local/offline, Ghost OFF and
player-ID0 guards remain. It also retains the narrow false-Attract loading
fix; the native Broker Dump code stays stock.

The historical eight-car runtime test used `Italy_S4` / Track10 and completed
the full race lifecycle, but the later closeout records a player launch near
unsuitable geometry. No separate course is documented as an eight-car
`PASS_CLEAR`. The smoke plan does not invent one: first reproduce/characterize
Italy_S4, then establish new results on France1 and Spain1. If the first smoke
reveals a structural anomaly, stop and review before expanding the sweep.

The candidate has passed its exact hash, byte-range, inverse and deterministic
reproduction checks. R-OBS2's `retail-broker-v1` family accepts it through
locally audited exact anchor matches without adding the candidate SHA to the
source profile list. The loading-failure anchor has one explicitly approved
32-byte fingerprint variant for the exact five-byte known false-trigger fix;
all Broker/debug/native-Dump anchors remain stock and exact. This is a bounded
compatibility-family variant, not fuzzy or arbitrary-build support.

The stock native Debug→Dump is suitable for an active-race capture. It remains
unsafe after Race Results; this audit does not need Results, so never request a
post-Results Dump. A Broker checker reports only
`GRID8_BROKER_STATE_MATCH_ONLY`; visible independent cars, spacing, contact,
physics stability and course clearance still require human observation.

See [candidate](candidate.md), [native formula](native-grid-formula.md),
[course list](canonical-courses.md), [checklist](runtime-checklist.md),
[validation](validation.md), and [remediation boundary](remediation-boundary.md).
