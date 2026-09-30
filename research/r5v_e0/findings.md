# R5V-E0 — Trooper as retail vehicle ID25

**Status:** R5V-E0 P0 and P1 are FULL PASS by owner-reported runtime evidence.
Trooper is runtime-confirmed as an independent 26th retail vehicle at ID25;
the original IDs 0–24 remain present. The exact tested executable hash and raw
logs/screenshots were not supplied, so this is attributed to the owner's
2026-09-30 report and is not represented as an independently repeated test.

## Result

The existing retail slot25 patcher now supports `astero-proof` and `trooper`
profiles. The Trooper profile calls the same retail record initializer used by
the Astero proof, passes ID25/class2 and an owned temporary `Trooper` string,
and uses Astero ID16 values only for frontend stats/floats. Physics is sourced
from the retail `Vehicles/Trooper` family; the model and authentic tag101
collision come from the Trooper demo payload. IDs 0–24 and their initializer
sequence remain byte-identical to the retail source.

The ignored candidate is `.research-output/r5v_e0/runtime-test/`:

- `MRallye_slot25_trooper_test.exe`, retail source SHA-256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
  candidate SHA-256
  `3022bdc6eb07d1e388f9c8ef693b83ce1c20c12c2c1a62719aad1cc59a1b1f13`;
- `DataGx/Vehicles/Trooper/` with three retail-compatible DX files and 24
  referenced DXT dependencies;
- patch/data manifests and the P0/P1 test instructions.

The loose package resolver reports `COMPLETE` / `LOOSE_OVERRIDE`, 27 files,
and no unresolved texture references. Retail Trooper physics validates as
`COMPATIBLE` (147 fields, all 120 fixed required fields, and 13 Player1
modification fields). The authentic Trooper tag101 collision passes the
structural checks described in [trooper-collision.md](trooper-collision.md).

## Human runtime report

The owner reports the following result in the supplied R5V-E0.1 master prompt
(2026-09-30):

- ID25 is selectable in T3; the Trooper frontend, race, and wheel models load.
- Trooper physics, collision, and damage work.
- A full stage was completed; Race Results and return to the menu work.
- Original vehicles remain available; ID25 presents a vehicle without
  replacing another vehicle.
- The observed display label is `STEEL MONKEYS FORKLIFT`; frontend stats show
  Astero-derived values; the Vehicle Select icon is absent; race 1P, progress,
  and Race Results icons show Astero.

This records R5V-E0 P0 = FULL PASS and P1 = FULL PASS as owner-reported runtime
results. The exact tested EXE hash, debug log, and screenshots were not
included, so the repository does not independently verify the test artifact.
The separate display, stats, and icon mappings are the subject of R5V-E0.1.

## Scope and limits

- R5V-C closeout is commit `f3b5883`; its duplicate-Astero P0/P1 result remains
  owner-reported and separate from this Trooper test.
- Trooper DX files are converted from the exact demo-9.3.1 revision-131 source
  snapshots already used by R-COOKER1.1. Their converted hashes match the
  three runtime-tested revision-135 candidates.
- The Trooper DX conversion itself is structurally validated and the same
  three converted resources have prior retail runtime evidence. The owner
  reports the ID25 + Trooper composition passed the P1 race checks; the tested
  candidate identity is not available for independent byte-level matching.
- No retail executable, `Data.sma`, demo binary, game asset, screenshot, or raw
  analysis project is committed. Nothing was pushed.

See [trooper-evidence.md](trooper-evidence.md), [trooper-assets.md](trooper-assets.md),
[trooper-physics.md](trooper-physics.md), [trooper-collision.md](trooper-collision.md),
[branch-integration.md](branch-integration.md), and [validation.md](validation.md).
