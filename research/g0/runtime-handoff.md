# G0 runtime handoff — completed

This file preserves the original review/test plan. The human tests are now
reported complete in [`runtime-results.md`](runtime-results.md); do not treat
the following as pending runtime work.

The planned tests targeted Retail France1 and
`DataScene/RaceTest/France1.xml` in an isolated runtime copy:

- StartArea helper edits were expected to reproduce the prior direct XML
  start-grid transformation.
- FinishArea helper edits were expected to change the race-completion region.
- A SplitTime0 main Egg Row3 edit was expected to move the visible sign and
  gameplay trigger center together while leaving Radius, ID, ExtraTime,
  siblings, RaceLine, StartArea, and FinishArea untouched.

The project owner reports that all three Blender → XML → runtime checks passed
as predicted. Combined StartArea + FinishArea editing also loaded normally.
Exact runtime build, executable hash, output XML hashes, and manifests were not
provided with that result. See the machine-readable
[`runtime-results.json`](runtime-results.json) for the recorded evidence and
its missing provenance fields.
