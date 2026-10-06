# R-OBS3 validation

## Static and automated evidence

- Synthetic suite: 603 run, 594 passed, 0 failed, 9 skipped because retail
  executable corpus fixtures are not installed/tracked in this checkout.
- `python -m compileall -q src tools tests`: passed.
- `git diff --check`: passed.
- Candidate family/registry audits: AI proof 10/10 anchors, `merc-id26`; GRID8
  10/10 anchors, registry unknown. Both have native Dump capability; both use
  the stock walker, so post-Results safety is false.
- Research package build and archive manifest verification: passed;
  `.cmd --help` smoke passed using its `python` fallback.
- The supplied AI candidate was resolved through the full
  `retail-broker-v1` family audit, with all ten family anchors matching and the
  separate `merc-id26` registry profile recognized.
- The GRID8 candidate passed the same family audit without adding its SHA to
  the source profile allowlist.
- The separate R-OBS3 package was built deterministically and its archive
  contents, per-file hashes, and manifest were verified. It contains source
  and metadata only, not a game executable.
- Public Observatory v0.1.0-beta source/package configuration was not changed.

## Capability rules

Passive Broker read requires known PE/layout and the three Broker-read core
anchors. Native Dump additionally requires the route, singleton, manager, and
walker anchors. Post-Results safety requires the exact approved hardened
walker. The editor opener and Flow Builder remain separately gated. Attract
state and vehicle-registry identity are informational and do not grant Broker
read.

## Evidence boundary

The resolver, cache re-audit, runtime fingerprint checks, package, and tests
are statically prepared. A human still needs to run the launcher against a live
candidate and verify a capture pair. Until then the phase remains
**READY FOR HUMAN RUNTIME**, not `CONFIRMED_BY_RUNTIME`.
