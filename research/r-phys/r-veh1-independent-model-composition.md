# R-VEH1 — Independent Model Donor and Physics Family Composition

**Implementation status:** `READY_FOR_RUNTIME` for the three plans in the
[runtime test plan](r-veh1-runtime-test-plan.md).

**Evidence boundary:** the shared persistent family lookup is already
`HUMAN_RUNTIME_CONFIRMED` by R-PHYS3. The new independent model-donor
compositions in this phase are **NOT_RUNTIME_CONFIRMED**. Offline plans and
synthetic tests do not establish that retail loads the composed model or that
its visual, collision, wheel, or damage behavior is correct.

## Composition identities

The composer keeps three choices independent:

| Identity | Meaning | Runtime use |
|---|---|---|
| Carrier `C` | One initialized retail type, such as type 7 / Navara | Selects the retail type record whose family string may be redirected |
| Physics family `P` | One named family accepted by the semantic config validator | Becomes the runtime family identity and supplies `Vehicles/P` plus `P/Player1` |
| Model donor `M` | One installed model package, whether or not a physics family exists | Supplies the files materialized at the runtime model path when `M != P` |
| Runtime family | Always `P` | Retail uses `DataGx\Vehicles\P` and `Vehicles/P` from the same family identity |

```text
Carrier C --[patch only when C != P]--> Runtime family P
                                          ├── DataGx\Vehicles\P\... (model lookup)
                                          └── Vehicles/P + P/Player1 (config broker)

Model donor M --[only when M != P]--> transactional loose overlay at DataGx\Vehicles\P\...
```

R-PHYS3 established that persistent Navara-to-Trooper binding changes both
model/resource lookup and config/physics lookup. R-VEH1 adds the independent
`M` choice on the model branch without changing the native config broker.

## Effective model package

The package resolver merges resources by family-relative path:

```text
Data.sma:DataGx/Vehicles/M/**
    overlaid by
<install>/DataGx/Vehicles/M/**
```

Loose files win for matching paths. Every effective file keeps its
`DATA_SMA` or `LOOSE_OVERRIDE` source in the plan and the apply manifest. The
complete subtree is materialized, preserving nested paths and auxiliary
resources; the operation is not limited to `car.dx`, `complete.dx`, and
`wheel.dx`.

The donor check validates package completeness independently of physics
families. It parses the available core DX files and verifies their parsed
texture references resolve inside the effective donor package. If the runtime
family's Data.sma package would still supply a missing core DX or a referenced
texture, the plan is refused because that would silently mix two packages.
Other runtime-family archive resources cannot be removed from Data.sma; they
are reported as archive fallbacks. Whether an unparsed native read consumes
one of those remaining files is still unknown.

When `M == P`, the composer uses the natural effective model package and does
not copy it over itself. When `M != P`, the composer resolves and snapshots all
donor bytes before any destination write, then plans a per-file overlay at
`DataGx/Vehicles/P`.

For a deterministic loose destination, every existing loose file in that
runtime-family tree that is absent from the donor is planned as an individual
`REMOVE_STALE_LOOSE` operation. The manifest backs it up and restore puts it
back. This prevents old loose package files from being left mixed with the new
donor. Data.sma fallbacks remain available and are never deleted. Files created
after apply are outside the manifest and are left alone on restore.

## Special identities and validation

- `forklift` is a complete model donor in the local retail archive but has no
  same-named normal physics family. It is offered for `M` and rejected for
  `P` by the existing semantic config validator.
- `Ufo` remains `COMPLETE_WHEELLESS`; its absent `wheel.dx` is expected by the
  project evidence. A Ufo package cannot replace a runtime family if that
  family has an unmaskable archived `wheel.dx`.
- Physics validation continues to use the R-PHYS3.2 semantic schema: 120
  fixed required paths/types plus Engine arrays driven by `Gears` and
  `TorqueEntries`. It does not require a universal total such as 147. Player1
  continues to require the existing 13-field overlay.
- Retail carrier choices still come only from the 25 initialized retail type
  records. Model-only and config-only names are not promoted to carriers.

## EXE patching and configuration compatibility

The existing `patch_family_initializer` implementation remains the only EXE
patch backend.

- `C == P`: the family mapping is unchanged; no EXE copy is produced. If
  `M != P`, this is a model-overlay-only composition.
- `C != P`: the verified retail patcher writes a distinct output copy and a
  verified `.original` backup. The source `MRallye.exe` is not modified.

Schema-v1 binding files remain unchanged: an old `{carrier_type,
physics_family}` row means `M = P`, preserving the previous full-family
behavior. Schema v2 requires an explicit `model_donor`. The legacy batch
`validate`, `apply`, and `restore --output-exe` routes remain available;
schema-v2 composition apply currently handles one carrier per transaction.
The interactive command and schema-v2 batch path both use the same composition
planner, semantic validator, patcher, transaction manifest, and restore
backend.

## Transaction and restore

The manifest separates `exe_changes` from `model_overlay_changes` and records
the selected `C/P/M`, runtime family, donor provenance, donor-relative path,
destination path, pre-apply and applied hashes, and per-file backup path.
Replaced and removed loose files are backed up individually under
`.research-output/r-veh1/backups/`; the original EXE bytes are kept separately
beside the output EXE when a patch is needed.

Before apply, the plan resolves all source bytes, validates all destinations,
and records their current hashes. Apply stages donor bytes before writing and
refuses if any destination changed after preview. Restore first checks every
tracked file and backup. If any applied file has changed, it restores nothing
and reports the conflict. New files are removed only when their current hash
still matches the applied hash; replaced files are restored only under the
same condition. Unrelated files created later survive. Directory cleanup is
limited to directories recorded as created by the tool and succeeds only if
the directory is empty. No family directory is recursively deleted.

## Read-only local corpus check

The plan report was generated from the local install without applying a
composition:

- EXE: SHA-256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Data.sma: SHA-256
  `268f3279d78078df635c1bc9dedb5a84d2e2351ea0dd94e94728adef3b934f76`.
- The archive-backed effective packages were complete: Navara 31 files,
  Trooper 31 files, forklift 22 files, and Ufo 21 files without `wheel.dx`.
- The local loose `DataGx/Vehicles` root had no package overrides at plan time.
- Trooper's base config passed the semantic reader schema at 147 fields; its
  Player1 overlay contained all 13 expected fields. Navara passed the same
  local schema checks.

The exact filewise plans and per-donor-file SHA-256 values are in the ignored
local artifact
`.research-output/r-veh1/runtime-plans/r-veh1-runtime-candidates.json`.
That file is a generated research artifact and is not tracked by Git.

## Current evidence status

| Claim | Status |
|---|---|
| Persistent family `P` feeds model lookup and named config lookup | `HUMAN_RUNTIME_CONFIRMED` by R-PHYS3 |
| Data.sma plus loose files resolve by filewise loose-over-archive precedence | `CONFIRMED_BY_BYTES` and synthetic tests |
| Local Navara, Trooper, forklift, and Ufo package counts/completeness | `CONFIRMED_BY_CORPUS` for the recorded Data.sma hash |
| `C == P` elides the EXE patch | `CONFIRMED_BY_BYTES` and synthetic tests |
| Per-file model overlay, stale-file backup, hash-checked restore | Synthetic transaction tests; not a game runtime result |
| `M != P` is loaded by retail as the selected model while physics remains `P` | **NOT_RUNTIME_CONFIRMED** |
| Forklift model behavior, wheel placement, collision, and damage | **UNKNOWN until human runtime testing** |

The three human tests, generated paths, and restore commands are in the
[R-VEH1 runtime test plan](r-veh1-runtime-test-plan.md). No R-COOKER1 work is
included.
