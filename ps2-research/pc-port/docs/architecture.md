# PC PS2 Port Architecture Decision

Date: 2026-10-12
Status: `BASELINE_HOOK_REQUIRED_APPROVAL`

## Decision

Keep all PS2-specific policy and future feature code under
`ps2-research/pc-port/`. Reuse the existing D3D8 proxy implementation as the
single interception and device-lifecycle layer. Build the ordinary renderer
unchanged by default and, after approval for a narrow baseline hook, build a
separate PS2-enabled artifact from the same baseline sources plus the optional
extension. Do not copy the proxy source tree and do not create another D3D8
interceptor.

## Repository snapshot

- Repository: `D:/Game/Master Rallye/master-rallye-re-general`
- Branch: `master`
- Inspected HEAD: `a67cbefd7c5ad34e04e268b3c07d4ae997df9776`
- The worktree already had user changes in camera/race-epoch files and
  `modernization/renderer/docs/r-cam1-all-racetest/`. Those changes are outside
  this task and were left untouched.
- Course SDK and game assets were not needed for this source-architecture
  inspection.

## What the current build exposes

`modernization/renderer/CMakeLists.txt` defines one source list, builds it as
the static `proxy_core`, and links that into the `d3d8` shared library. There
is no separate extension target, extension factory, registration table, or
public draw callback contract. `Device8` is a concrete `final` implementation
of `IDirect3DDevice8` in `include/wrappers.hpp`.

The indexed draw seam is `Device8::draw_indexed_at` in
`src/visual_wrappers.cpp`. It currently:

1. records/classifies the draw with `Trace::before(71, ...)`;
2. repairs pending renderer state;
3. optionally runs the read-only foliage diagnostic;
4. creates a `ReflectionScope`;
5. calls the native `DrawIndexedPrimitive` exactly once;
6. records the native result and lets the scope restore its temporary state.

`ReflectionScope` is a renderer-internal RAII helper. It is not a general
extension interface: it owns one reflection-specific texture-stage change and
updates private trace state. A PS2 module compiled outside the proxy cannot
safely call it or observe all the current per-device provenance.

The inspection found no supported extension/callback point at the draw seam.
Linking an unrelated DLL cannot intercept the already wrapped `Device8`, and
copying/patching the draw wrapper would create the forbidden competing proxy.

## Recommended ownership boundary

The baseline should own:

- D3D8 interception and COM/resource lifetime;
- device, frame, reset and draw lifecycle;
- vertex/index CPU-upload mirrors and generation/revision invalidation;
- immutable draw evidence handed to extensions;
- validated native state reads, logical/effective state tracking, scoped
  state application and exact restoration;
- the one native draw call and its original HRESULT.

The optional PS2 extension should own:

- a separate `PS2Port.ini` policy, defaulting to `Stock`;
- the France1 `bush01` source geometry signature and current-session classifier;
- validation of course ownership and negative controls;
- PS2 material-state selection and diagnostics;
- future water/reflection policies in their own modules.

The extension must return a bounded state request from immutable draw facts;
it must not receive an unrestricted native-device pointer. The baseline then
applies a draw-local transaction only when every requested original state is
known and successfully captured. Any ambiguous identity, unknown state,
partial setter failure, stale resource revision, unsupported build or reset
falls back to the stock draw. Restore failure disables that extension for the
device and is reported as a native failure.

## Proposed source tree

```text
ps2-research/pc-port/
  README.md
  docs/
    architecture.md
    pilot1.2-design.md
  renderer/
    integration/       # extension-facing data contract and state requests
    foliage/           # France1 bush01/treeblend policy and classifier
    water/             # future; not started
    reflections/       # future; not started
  tests/               # PS2 extension and integration-contract tests
  tools/               # reproducible PS2-enabled build entry point
```

The extension-facing contract should contain value types rather than expose
`Device8`, `Trace`, or other renderer internals. Its draw snapshot should carry
the device/session identity, draw arguments, bound buffer identities and
generations, covered CPU-mirror revisions, relevant byte ranges, and only the
validated material/texture facts available at that draw. State requests should
be an allowlisted list of render-state key/value pairs.

## Build composition

The baseline build must remain the existing documented build and must not
require any PS2 source or configuration. The proposed opt-in build adds a
second build configuration that compiles the existing baseline source list
with the approved adapter seam and the sources under `ps2-research/pc-port/`.
It emits the same proxy implementation to a separate output directory, for
example `ps2-enabled/d3d8.dll`; the baseline artifact and its output path remain
unchanged. A user selects one artifact for a manual test; the repository does
not deploy or rename DLLs into the game directory.

The current build has no such option or command. A reproducible command and
build script will be added only with the approved integration change; this
document does not present a non-working command as available.

## Runtime evidence boundary

The supplied architecture brief reports two France1 captures with one
matching D3D8 draw each, a Turkey3 control with no match, and observations of
the original PC alpha/blend/depth-write states. Those are treated as
user-supplied runtime findings for planning. Their capture files are not in
the current repository, and the previously referenced
`D:/Games/Master Rallye Pristine/MRRenderer/logs` path is not present on this
host. The committed pilot documents still describe the earlier
`TARGET_IDENTITY_AMBIGUOUS` checkpoint. Therefore this pass does not claim to
have independently reproduced or persisted the newer captures.

Before a feature is activated, the new evidence must be stored under the
PS2-port research tree and prove current-session resource/buffer generation,
CPU upload coverage, exact submitted range, course ownership and the live
negative controls. No fixed draw ordinal, historical resource generation or
texture identity may be used as the permanent predicate.

## Required baseline interface approval

The smallest safe integration is an internal draw-extension seam and an
optional alternate build. It requires edits to the frozen baseline files:

1. `modernization/renderer/include/wrappers.hpp` — hold the optional
   per-device extension instance behind the extended-build compile option.
2. `modernization/renderer/src/wrappers.cpp` — create/destroy the extension
   with the device lifecycle and invalidate it on reset/recreation.
3. `modernization/renderer/src/quality_wrappers.cpp` — notify/invalidate the
   extension at successful device reset boundaries.
4. `modernization/renderer/src/visual_wrappers.cpp` — provide the immutable
   draw snapshot and apply the returned state request around the existing
   single native indexed draw, using a core-owned RAII state transaction.
5. `modernization/renderer/CMakeLists.txt` — keep the normal target
   independent and add the optional PS2-enabled artifact/test composition.

PS2 policy, configuration, feature sources, and their focused tests remain in
`ps2-research/pc-port/`. No edit to the baseline INI, assets, Course SDK, or
game executable is needed. The baseline behavior remains unchanged when the
extension is absent; its source still gains a no-op-capable internal call
point, and the optional artifact adds the PS2 object code. That compatibility
effect must be reviewed explicitly.

No baseline file was changed in this pass. Approval is required before making
these edits, as required by the supplied architecture decision.
