# PC-VISUAL-PILOT1.2 — France1 `bush01`

Historical design snapshot. PILOT1.3's four diagnostic masks, bounded mode
logging, and current A/B instructions supersede its single-mode runtime
guidance; see [`../runtime-ab.md`](../runtime-ab.md) and
[`../implementation.md`](../implementation.md).

The source target is France1 PSM node 3509209, material
`bush $alphatest() $clamp(uv) $shader(treeblend)`, with 24 source faces. Its
verified PC counterpart is compiled DX record 54 (`course.batch.1.21`), with
24 unique unsigned triangles duplicated by winding. The PS2-style pilot is
restricted to live D3D8 draws whose current mirrored geometry yields the exact
verified face-multiset fingerprint and whose runtime owner is certified as
France1. It does not use the DX draw ordinal, texture, or caller as a predicate.

The integration is carried only by
[`../overlay/patches/0001-renderer-integration.patch`](../overlay/patches/0001-renderer-integration.patch)
and staged-only generator patch
[`../overlay/patches/0002-interface-generator.patch`](../overlay/patches/0002-interface-generator.patch).
The source baseline remains unchanged. The patch/build procedure is described
in [`../overlay/README.md`](../overlay/README.md).

The extension emits an immutable-input classification and can request five
draw-local D3D8 render-state values. The shared core applies them only after
native state matches the tracked effective state, submits the original draw
once, restores changed states, and preserves the draw HRESULT. The pilot keeps
the PC texture and approximates broad PS2 alpha/depth behavior; it does not
reproduce the exact PS2 GS blend equation, queue ordering, or pixel parity.

Status remains `IMPLEMENTED_PENDING_USER_RUNTIME`. Earlier F10 capture files
are absent from this checkout, so stable runtime draw identity is not claimed
until a fresh live log is obtained. The user's manual Free Camera A/B steps
are in [`../runtime-ab.md`](../runtime-ab.md).
