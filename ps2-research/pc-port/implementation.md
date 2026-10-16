# PC-VISUAL-PILOT1.3 implementation

## Build boundary

The source `modernization/renderer/` remains at locked baseline HEAD
`61cb84d5c7f28d3bd88a3f1f9a8ce16d4c178390`. The deterministic overlay stages
that immutable source and applies the PS2 integration only in the ignored
PS2-enabled build tree. Both variants use the existing single `d3d8` proxy.
PS2 policy and code live under this directory. Baseline mode retains its old
`foliage_diagnostics` mirroring behavior; the PS2 build enables mirroring
before buffer creation only when a non-Stock PS2 mode is selected.

Configuration is read from `PS2Port.ini` beside `MRRRenderer.ini`. Missing or
invalid configuration, unsupported executable identity, or unverified course
ownership fails closed. F10 diagnostic capture is not required for mirroring.

## Target and runtime evidence

The exact PC executable SHA-256 is
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. The
France1 source record is DX draw 54 / `course.batch.1.21`, with target
face-multiset fingerprint
`2b60b1f044601052bb5eaeca074615abe3947fdc1b0769c17d300a0b3b3e6f7d`.
Source survey evidence found 25 France1 groups using `bush01-tga`; the target
classifier does not select by texture, source draw ordinal, or callsite.

For each live candidate, the classifier still requires the exact executable,
France1 race-owner certificate, supported indexed geometry, complete current
CPU mirrors, resource generations/revisions, and exact geometry fingerprint.
Those checks were not changed in PILOT1.3.

The user reports a live A/B: 5,364 successful target identity events; F10
frame 7608 contains the exact draw
`DrawIndexedPrimitive(4,11940,28,22944,48)` with the override active; the
reported alpha/blend/depth-write changes and restoration returned success.
Stock frame 4311 contains the same draw without an override. In frame 7608 it
was draw 46 of 704, followed by many depth-writing draws. The user observed
that the foreground bush became mostly invisible, with partial visibility
around and through neighboring tree foliage. This is user-supplied runtime
evidence; source capture files are not included here. The cause remains
unresolved between depth-write/draw-order interaction and alpha/texture-stage
interaction.

## Draw-local mode contract

The classifier returns a `StateRequest` only after the same exact geometry and
current-owner proof succeeds. `override_mask` uses bit order: alpha test,
alpha blend, source blend, destination blend, depth write.

| Mode | Mask | Requested D3D8 values |
|---:|---:|---|
| 0 | `0x00` | No request; Stock |
| 1 | `0x1F` | `ALPHATESTENABLE=FALSE`, `ALPHABLENDENABLE=TRUE`, `SRCBLEND=SRCALPHA`, `DESTBLEND=INVSRCALPHA`, `ZWRITEENABLE=FALSE` |
| 2 | `0x0F` | Same four alpha/blend values as mode 1; `ZWRITEENABLE` is preserved |
| 3 | `0x10` | Only `ZWRITEENABLE=FALSE`; alpha test, blend enable and both blend factors are preserved |

Masked transaction lifecycle:

1. Validate only masked native values against the effective state shadow.
2. Save only those original native values.
3. Apply only masked states whose values differ.
4. Mark a state before attempting `SetRenderState`, so a failed call is also
   rolled back in case native state changed before the failure was returned.
5. On a partial apply failure, roll back attempted states in reverse order and
   submit the original draw once with the original HRESULT semantics.
6. After a successful draw, restore only successfully changed masked states
   in reverse order. Unmasked slots are never read, applied, rolled back, or
   restored.

If restoration fails, the extension disables itself for that device and emits
the failure diagnostic. With diagnostics enabled, device setup emits one
`ps2_port_mode_selected` record, including for mode 0. Modes 1–3 emit at most
one target identity record per device; it includes the selected mode,
requested and actually applied masks, resource generations/revisions, and
pre-draw rollback status.

## Rendering boundary

All modes retain the original PC texture, draw order, topology, depth test,
culling, texture-stage state, and single native draw. There is no extra pass,
sorting, course-data change, or texture replacement. Mode 1 retains the
previously tested state approximation. It does not reproduce PS2 GS `As/128`
exactly or establish PS2 visual parity. See [`runtime-ab.md`](runtime-ab.md)
for the controlled four-mode comparison.
