# PC-VISUAL-PILOT1.2 Integration Design

Status: `DESIGN_READY`; implementation waits for approval to add the minimal
draw-extension seam to the frozen baseline renderer.

## Target and evidence

The target remains France1 `bush01`: PS2 source node 3509209, material
`bush $alphatest() $clamp(uv) $shader(treeblend)`, 24 source faces; PC compiled
DX record 54 (`course.batch.1.21`), 24 unique unsigned triangles represented
in both windings. The geometry correspondence is already recorded in the
PC-VISUAL-PILOT1 source-signature report.

The supplied architecture brief adds newer live observations: one France1
draw match in each of two captures, no Turkey3 match, and original PC alpha,
blend and depth-write states. They are useful user-provided evidence, but the
capture artifacts are not present in this checkout, so the extension design
does not treat those observations as a reproducible classifier or as proof of
stable buffer ownership by themselves.

## Draw contract

At the existing `draw_indexed_at` boundary, the baseline should construct an
immutable snapshot from current bindings and current buffer mirrors. The
classifier should require all of:

- supported exact game build and current device/session generation;
- verified course ownership for the current loaded course;
- buffer identity plus current resource generation and CPU-mirror revision;
- complete byte coverage of the vertex/index ranges used by this draw;
- the source geometry fingerprint in the actual submitted index window;
- the exact live partition/range proven by the France1 captures;
- all required live negative controls remaining clear.

Any incomplete mirror, GPU-side write, raw COM escape, reset, unknown draw
partition, stale revision or competing ownership returns `NoMatch`. The
classifier never keys on texture name, primitive count, callsite, source draw
ordinal or old generation number by itself.

## Draw-local material transaction

Only a confirmed target may request these initial D3D8 changes:

| State | Stock | Pilot request |
|---|---|---|
| `D3DRS_ALPHATESTENABLE` | observed at runtime | `FALSE` |
| `D3DRS_ALPHABLENDENABLE` | observed at runtime | `TRUE` |
| `D3DRS_SRCBLEND` | observed at runtime | `D3DBLEND_SRCALPHA` |
| `D3DRS_DESTBLEND` | observed at runtime | `D3DBLEND_INVSRCALPHA` |
| `D3DRS_ZWRITEENABLE` | observed at runtime | `FALSE` |

The pilot preserves the current depth-test enable/function, culling, texture,
texture-stage state, queue/order and stock PC texture. It does not claim
bit-exact PS2 GS `As/128` blending or visual parity.

The core-owned transaction must capture the exact native values and reconcile
them with the logical/effective state tracker before the first setter. If any
value is unavailable, the native read fails, or a setter fails, it restores
already changed states and performs the original draw once with Stock state.
After a successful target draw it restores all changed values before returning
the original native HRESULT. A failed restore disables the extension for the
device and emits an explicit error. There is no draw replay or global queue
change.

## Configuration and lifecycle

The extension reads its own `PS2Port.ini`; baseline `MRRRenderer.ini`
semantics stay unchanged. Missing file/key, invalid value, unknown build,
unknown course, ambiguous target or missing evidence all select Stock. The
initial option is `FoliageMode=0` (Stock) / `1` (France1Bush01Treeblend).
Diagnostics have a separate opt-in setting.

Classifier caches are scoped to the device and current resource generation.
Successful reset, resource recreation, incomplete upload coverage, unexpected
write path or loss of course ownership invalidates them. The extension has no
state after the device is destroyed.

## Test plan

Tests under `ps2-research/pc-port/tests/` should exercise the pure classifier,
configuration fallback, exact-vs-near geometry fingerprints, partial upload
coverage, current-session generation changes, course and other-course
controls, and state-transaction rollback/restoration using a mock baseline
adapter. Integration tests must additionally verify one native draw and
original HRESULT preservation. Runtime acceptance remains manual: Mode 0
France1 baseline, Mode 1 same view, unrelated foliage/control views, Turkey3
control, and a PCSX2 France1 reference. No test result is runtime visual
confirmation.

## Not implemented yet

This file is the reviewable design only. No PS2 module, new renderer build,
material-state override or runtime installation was created because the
baseline currently has no safe extension point and its owner has frozen it.
