# PS2-VEHICLE-MODEL-PORT2

Status: IMPLEMENTED_PENDING_USER_RUNTIME (X-Trail frontend only).
Starting HEAD: 932b3694ed25da059ec65a0824f3f0e4d986e365. Ending commit: see release-provenance.json in handoff.
Branch: master. Frozen renderer tree: e33386bcf682db6983380c499e4928726c758fe0.

## Implemented

An opt-in original XTRAIL COMPLETE.PSM frontend replacement: 24 meshes, 6606 vertices, 4636 triangles, 28 original textures including the verified default.gxi. Original positions, normals, UVs and vertex colors are retained. No original game files are written. PS2MDL02 is a local private runtime resource; proprietary geometry/textures are excluded from Git and the handoff.

The current native owner → packet → cache → compiled model → 24 mesh nodes → proxy/native VB/IB relationship was observed in the user session. Two F10 captures after selection changes contain all 24 unique compiled signatures (2487 PC triangles). See owner/current-findings.md and current-join.json. Historical addresses are evidence only. Runtime admission rechecks the current caller, owner/backreferences, all source records, upload generations/revisions, matrices, native bindings and fixed-function shader state. One complete warmup frame precedes replacement. Unknown or incomplete identity retains Stock.

The implementation lives in renderer/frontend_model.*, frontend_model_native.hpp and frontend_transaction.hpp. Only staged patch 0001 integrates it; original modernization/renderer is unchanged. Existing Mode 4 reflection resources are required. All private textures and material validation must succeed before suppressing the verified PC model. Private meshes render once; the 24 corresponding original records are suppressed for that current owner only. Other vehicles and race draws retain their existing paths.

## State safety and limitations

The transaction retains native texture references, render/texture-stage states, shaders, texture transform and stream binding; restoration uses effective-only tracker notifications. Pending restoration is retried before a real Reset; window-mode reset echo retains its existing handling. Failed setters are included in rollback. DrawPrimitiveUP stream changes are restored even on failure. A GPU failure after partial geometry submission cannot be atomically undone; it is reported and the feature disables safely rather than claiming a successful frame.

Native WORLD/VIEW/PROJECTION are preserved, with original PS2 local vertices and no fitted offset. Previous bounds-registration offsets are not runtime transform proof. CULL_NONE is a documented approximation pending original strip/culling semantics. Mode 3 uses the existing mixed reflection source; glass is submitted last with conventional D3D8 blending. Alpha normalization, lighting, pivot, culling and sampled reflection are not pixel-exact PS2 emulation.

## Validation

Both Win32 Release builds succeeded with --parallel 1. Baseline CTest 24/24; PS2-enabled 34/34; port Python regressions 133/133; owner tests 13/13; asset tests 9/9. Proxy exports and repeated interface generation passed. Native tests cover defaults, unknown identities, shader state, partial state failures, exact restoration/effective shadow, texture failure cleanup and Reset resource recreation. These are automated results, not menu/runtime confirmation.

Baseline DLL SHA-256: 011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138.
PS2 DLL SHA-256: 9d1c7d62f34c0dd0467c4a10afd11a112fd215cf9da78c40855f11ad17d8e887.
Private model SHA-256: ba1cee9a21c2a2ae2935158136ae80b587eca7dc9a6701afc573e069818d772b (741114 bytes).

Original PC executable, PS2 ELF and source COMPLETE hashes were verified. Course SDK remains clean at 4244fa0c4d878523c9947f54816bf377cdfb2589. Unrelated pending work was preserved. No automatic deployment or push.

## Separate race readiness

CAR replacement is deferred until this frontend candidate is visibly validated. Race body, independently transformed wheels, steering/suspension, damage and brake/glow ownership require separate admission/suppression contracts. This frontend replacement does not establish those contracts. Wheel appearance in COMPLETE is included; race wheel reflections remain a later check.

Next single step: run the X-Trail frontend A/B in runtime-ab.md, including rotation, selection changes and Reset. No PS2 parity claim or full-model runtime success yet.
