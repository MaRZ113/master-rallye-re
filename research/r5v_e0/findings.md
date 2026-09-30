# R5V-E0 — Trooper as retail vehicle ID25

**Status:** Trooper candidate prepared; owner reports the P0 slot and preview
worked without replacing the original vehicles. P0 is recorded as a limited
owner-reported pass; texture appearance, repeated-menu stability, stats, and a
matching candidate hash were not included in the report. The P1 package is
staged for a human race test. No race was started by this research run.

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

## Human P0 report

On 2026-09-30 the owner reported: “Слот подтвержден, машина показывается и не
заменяет другие.” This establishes the reported ID25 visibility/presentation
and nonreplacement result. The tested executable hash and separate texture,
menu-stability, stats, and debug-log observations were not supplied, so this
report is kept distinct from a fully itemized P0 result. The prompt permits P1
after a P0 pass; P1 instructions are in the ignored candidate directory and
[runtime-test-plan.md](runtime-test-plan.md).

## Scope and limits

- R5V-C closeout is commit `f3b5883`; its duplicate-Astero P0/P1 result remains
  owner-reported and separate from this Trooper test.
- Trooper DX files are converted from the exact demo-9.3.1 revision-131 source
  snapshots already used by R-COOKER1.1. Their converted hashes match the
  three runtime-tested revision-135 candidates.
- The Trooper DX conversion itself is structurally validated and the same
  three converted resources have prior retail runtime evidence. The present
  ID25 + Trooper composition still needs its own human P1 race result.
- No retail executable, `Data.sma`, demo binary, game asset, screenshot, or raw
  analysis project is committed. Nothing was pushed.

See [trooper-evidence.md](trooper-evidence.md), [trooper-assets.md](trooper-assets.md),
[trooper-physics.md](trooper-physics.md), [trooper-collision.md](trooper-collision.md),
[branch-integration.md](branch-integration.md), and [validation.md](validation.md).
