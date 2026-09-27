# R-PHYS3.2 — Semantic Variable-Length Vehicle Config Validation

**Status:** implemented and verified against synthetic cases and the available
read-only retail/demo XML corpora. No game was launched and no executable or
game asset was modified.

## Why the old check was too strict

The P3.1 binder treated the retail Navara record's 147 path/type rows as the
universal shape of every vehicle. That rejected valid named families whose
Engine arrays contain a different number of entries. A total-field count or
whole-schema fingerprint cannot distinguish a missing reader input from a
valid array of a different declared length.

The binder now uses one semantic validator in the inventory, interactive
wizard, scripted `validate`, and `apply` paths. The fixed retail reader schema
has 120 required path/type pairs: 118 ordinary fields plus the two Engine
count headers. The Engine count headers are integers:

| Count path | Type | Indexed paths it controls | Indexed type |
|---|---|---|---|
| `Engine/Gears` | `Int` | `Engine/GearN`, `Engine/ChangeUpRevsN`, `Engine/ChangeDownRevsN` | `Float` |
| `Engine/TorqueEntries` | `Int` | `Engine/TorqueEntryN` | `Vector2` |

Indices must form the complete zero-based sequence declared by the count. For
`G` gears and `T` torque entries, the expected record size is:

```text
120 + 3*G + T
```

This is a derived diagnostic, not a fixed compatibility requirement. Retail
examples include 144, 146, 147, and 149 fields. The fixed schema fingerprint
is retained as an audit aid, but no family is accepted or rejected by a
whole-record SHA-256.

The 120 fixed path/type requirements group as follows:

| Group | Fixed requirements |
|---|---:|
| Chassis | 16 |
| DamageParams | 25 |
| Dimensions | 8 |
| Engine, including both counts | 18 |
| Steering | 5 |
| Suspension | 48 |
| **Total** | **120** |

## Reader evidence and confidence boundary

Retail Ghidra evidence for `FUN_0049CEF0` references the names `Gears`,
`ChangeUpRevs`, `ChangeDownRevs`, `TorqueEntries`, and `TorqueEntry`. Recorded
string-reference sites include `0x0049DA54/0x0049DA65/0x0049DA6B` for `Gears`,
`0x0049DCA2/0x0049DCB4/0x0049DCBA` for `ChangeUpRevs`,
`0x0049DE1D/0x0049DE2F/0x0049DE35` for `ChangeDownRevs`,
`0x0049DF1D/0x0049DF2F/0x0049DF35` for `TorqueEntries`, and
`0x0049E08D/0x0049E09F/0x0049E0A5` for `TorqueEntry`. This corroborates the
reader field names. The retail and demo XML path sets corroborate the
count-to-index relationship and exact observed types.

This report does not claim that every internal native loop or allocation
detail has been dynamically instrumented. The schema models only the
path/type requirements supported by the fixed retail record and observed
indexed fields. Demo builds have other fixed-field differences and are used as
cross-build evidence for Engine array cardinalities, not as alternate retail
validation targets.

## Validation classes

| Class | Meaning | Binding policy |
|---|---|---|
| `COMPATIBLE` | All 120 fixed requirements and all count-declared indexed paths are present with their expected types; there are no unexplained paths. | Allowed by default. |
| `INCOMPLETE` | A required fixed or count-declared indexed path is absent. | Rejected; the experimental schema switch does not waive missing data. |
| `TYPE_MISMATCH` | A required fixed, count, or indexed path has a different XML type. | Rejected; the experimental schema switch does not waive wrong types. |
| `UNVERIFIED_SCHEMA` | Required retail paths are present and typed, but unexplained paths or count encodings prevent a confident retail-schema classification. | Rejected by default. The user must type `ALLOW UNVERIFIED SCHEMA` in the wizard or explicitly pass `--allow-unverified-schema` to scripted validation/apply. |

The advanced schema override is separate from the existing `ALLOW MISSING
MODEL` override. It does not waive model availability, missing config paths,
type mismatches, or the required `Player1/Modifications` overlay. When used,
the semantic audit is included in the validation result and apply manifest.

## Cross-build evidence

These records were parsed from the repository's existing corpora. A build's
full record is compared to the fixed retail requirements only when it is the
retail build; older builds contain other version-specific path differences.

| Build | Family | `Gears` | `TorqueEntries` | Indexed paths found | Interpretation |
|---|---|---:|---:|---|---|
| Demo 8.4.1 | Trooper | 7 | 8 | 7 of each gear array; 8 torque entries | Supports count-driven arrays. Other paths differ from retail. Bowler and Custom are absent. |
| Demo 9.3.1 | Bowler, Custom | 7 | 8 | Complete observed index ranges | Supports shared count semantics; other paths differ from retail and these records are not accepted as retail configs. |
| Demo 9.10.0 | Bowler, Custom | 7 | 8 | Complete observed index ranges | Matches the retail candidate shape. |
| Demo 9.10.0 | Kamaz | 10 | 8 | Complete observed index ranges | Shows the validator must not cap `Gears` at the retail Navara value of 7. |
| Retail | Bowler, Custom | 7 | 8 | Complete observed index ranges | 149 total fields; both are `COMPATIBLE`. |
| Retail | Kamaz | 7 | 5 | Complete observed index ranges | 146 total fields; `COMPATIBLE`. |

Retail corpus regressions also verify Navara `7/6` (147 fields), Pajero and
Mercedes `6/6` (144), and Trooper `7/6` (147). All seven tested retail records
match their count-declared paths and types. The tests preserve the cross-build
distinction: 8.4.1 and 9.3.1 provide array evidence, while 9.10.0 and retail
provide the listed candidate-path comparisons. A separate pass over all 35
named retail base records classifies every one as `COMPATIBLE`.

## Current read-only candidate readiness snapshot

The following is the current local retail install inventory at
`D:\Game\Master Rallye`, with executable SHA-256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. Model
availability uses the installed `Data.sma` plus loose overrides. These are
machine-local observations; another install may have different model files.
The local retail `Modifications.xml` has complete 13-field Player1 overlays
for 33 of the 35 named config families; `SeatBuggy` and `Ufo` have incomplete
Player1 overlays and remain blocked by the binder even though their base
records satisfy the semantic reader schema.

| Family | Initialized retail type ID | Base config | Player1 | Model package | Binder note |
|---|---:|---|---|---|---|
| Navara | 7 | `COMPATIBLE`, 147 fields (`7/6`) | `COMPLETE`, 13/13 | `COMPLETE`, `DATA_SMA` | Selectable carrier and source family. |
| Kamaz | 22 | `COMPATIBLE`, 146 (`7/5`) | `COMPLETE`, 13/13 | `COMPLETE`, `DATA_SMA` | Selectable carrier; useful next human test of a different torque-array length. |
| Pajero | 1 | `COMPATIBLE`, 144 (`6/6`) | `COMPLETE`, 13/13 | `COMPLETE`, `DATA_SMA` | Selectable carrier and source family. |
| Mercedes | — | `COMPATIBLE`, 144 (`6/6`) | `COMPLETE`, 13/13 | `COMPLETE`, `DATA_SMA` | Valid source family; not an initialized retail carrier. |
| Bowler | — | `COMPATIBLE`, 149 (`7/8`) | `COMPLETE`, 13/13 | `COMPLETE`, `DATA_SMA` | Valid source family with a different torque-array length. |
| Custom | — | `COMPATIBLE`, 149 (`7/8`) | `COMPLETE`, 13/13 | `MISSING` | Config is valid; apply remains blocked until model resources are installed or the separate explicit model override is used. |
| Trooper | — | `COMPATIBLE`, 147 (`7/6`) | `COMPLETE`, 13/13 | `COMPLETE`, `DATA_SMA` | Config-only in the retail type catalog; prior runtime binding remains separately human-confirmed. |

Here “—” means no initialized retail type ID, not an absent config or failed
schema. Type IDs, config families, model packages, and frontend selectability
remain separate identities.

## CLI behavior

The interactive family list reports fixed-field completeness, total fields,
`Gears`, `TorqueEntries`, Player1 status, and model provenance. After choosing
a family, the detail view prints count expectations, missing paths, extra
paths, type mismatches, and count errors. It no longer says that every family
must contain 147 fields.

The scripted interface remains available. JSON is still the default output;
`--text` selects the compact schema summary:

```powershell
python tools/physics_bind.py validate `
  --install-root 'D:\Game\Master Rallye' `
  --config 'research\r-phys\vehicle-physics-bindings-trooper.example.json' `
  --text
```

An unexplained but complete schema can be tested explicitly:

```powershell
python tools/physics_bind.py validate `
  --install-root 'D:\Game\Master Rallye' `
  --config 'research\r-phys\vehicle-physics-bindings-trooper.example.json' `
  --allow-unverified-schema --text
```

The CLI uses the same validator as the wizard and apply backend. It does not
launch the game. No runtime result is claimed by this phase.

## Verification and implementation boundary

Focused verification includes the schema validation matrix, exact path diagnostics,
the narrow override policy, wizard confirmation phrase, real retail family
records, and the 8.4.1/9.3.1/9.10.0 cross-build array evidence. The full
synthetic suite completed with **350 passed, 0 skipped** using
`python -m unittest discover -s tests/synthetic`. `python -m compileall -q src tools tests/synthetic` and `git diff --check` also completed successfully.
A read-only scripted dry-run against the current install returned `VALID`,
`120/120` fixed fields, `Gears = 7`, three `7/7` gear arrays,
`TorqueEntries = 6`, `6/6` torque entries, and 13 Player1 fields. No executable
or game asset was written. No game was launched.

The validator does not infer that an unrecognized path is safe, does not widen
the retail field schema silently, and does not infer physical behavior from a
config count.
