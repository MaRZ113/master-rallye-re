# R-GFX5-6 implementation delta

MarginFrame and its persistent X mutation/delayed Present restore are removed. The unchanged fingerprint-gated0056D110 entry hook now brackets consumer identity with a transient return bridge; only actual DrawPrimitive return0056D7C4/FVF0x142/triangle-list/identity-VIEW/live-UI-projection draws can apply a native WORLD copy. Matrix acquisition, local translation and immediate restoration are native-only trace events. Logical game/cache state receives zero coordinate writes. Nested contexts are bounded; source identity/epoch is rechecked at draw. [Architecture](render-local-ui.md).

Exclusive Width/Height or first accepted auto target is distinct from HWND client geometry. Invalid mode/depth pairing explicitly returns NOTAVAILABLE with no native call; native AA-only fallback preserves fullscreen, and there is no display alias/fallback into Windowed. Native D3D8/game owns exclusive window state. Current Windowed/maximize, Borderless, preview, AF MIN-only, AA, FOV/culling, freeze, cursor, COM/resources and learned vehicle reflection mechanisms remain. [Lifecycle](exclusive-lifecycle.md).

Producer and native capture filters are R-GFX5-6. F10 distinguishes desired packet coordinates from actual effective WORLD at draw; bounded native attempt/cooperative transition diagnostics expose display/AA decisions. Canonical numeric enums/booleans and vertical comments remain, with legacy strings accepted. No widened XY rules, groups, old sort hook, new whole-image profile or new artwork. Source/cache byte equality, precise native restoration, failure handling and actual production gates are covered by the native suites.

## Historical record (superseded where noted above)

# R-GFX5-5 implementation delta

This pass retains the final0056D110 consumer, frame-owned edits and successful Windowed/Borderless/Reset/preview/filtering/MSAA/FOV/vehicle mechanisms. No native widget owner is proven; group inheritance is absent. PreserveMargins is experimental, Centered4x3 recommended.

MarginAnchors keeps direction for two absent completed frames (MARGIN_ANCHOR_GRACE_FRAMES). Identity, structure, epoch and Reset changes override grace. It uses current animation coordinates on every consume. Bounded F10 records expose candidate IDs/membership/conflicts and packet grace; null group fields mean NOT_PROVEN. No unverified pointer fields, XY table changes or proximity grouping. [Policy](ui-group-ownership.md).

The existing strict visual boolean parser is shared by Trace's real INI reader. Numeric0/1 and true/false are equivalent; missing Trace settings default1, malformed/truncated values disable only the affected option and preserve raw/reason metadata. Enum string compatibility is unchanged. Both canonical INIs use numbers and one option per comment line. General example retains Stock visual defaults; stock-plus is opt-in with Centered4x3 and locally verified MenuFreezeFix enabled.

Producer/native capture filters are R-GFX5-5. Existing assertions retain their meaning. Synthetic UI IDs are registry-local; Python selects matching capture lifetime and ID/entity, avoiding merging separate registries in one session. No deployment or later phase.

## Historical R-GFX5-4 record (current policy above supersedes status/lifetime)

# R-GFX5-4 implementation delta

Only Windowed state ownership and stable PreserveMargins semantic direction changed. WindowApi snapshot exposes maximized state, the planner separates normal target from current client and the commit leaves maximized HWND placement alone. Final shutdown, cursor observer, Borderless and bounded native AA/error fallback behavior remain.

MarginAnchors owns direction proof; MarginFrame owns writes/restores. Registry is bounded512 and has no writable pointer ownership. DrawTextPacket bridge/guarded six-byte patch and native FPU/register replay remain. Frame gaps and current structure/context explicitly limit identity retention; no universal screen/allocator generation is invented. F10 provenance and state-transition records make those limits inspectable.

Regression contracts remain: AF MIN-only; MSAA4; source45 preview33.75; Centered4x3; feature-local freeze/UI/FOV/VehicleSemantics; FOV CPU planes; pool-aware Reset; COM identity; learned vehicle signatures/current material exclusion; exact draw-local reflection restoration. No backdrop/UI assets, whole-hash profile, lighting, freecam or future phase. Producer/capture filters are R-GFX5-4.

## Historical R-GFX5-3 implementation

# R-GFX5-3 implementation changes

Code candidate keeps all R-GFX3/R-GFX4 native overrides and material learning unchanged. Added: field-based self-induced Reset echo recognition without resource reset, pre-final-Release shutdown, rcWork centering, optional idle SetCursor policy, numeric/text enum parser, independent source45 preview correction, consumer-entry margins with bounded lifetime provenance, and independent decoded fixed-layout FOV/vehicle capabilities.

Cursor is managed only for configured Borderless/ExclusiveFullscreen, foreground game HWND and cursor inside its outer rectangle. Present samples movement/time; idle selects NULL, movement restores the saved handle, focus/outside relinquishes ownership and restores only if the current handle is NULL. A thread-local WH_CALLWNDPROCRET observer restores on WM_KILLFOCUS/WM_ACTIVATEAPP(false)/WM_DESTROY even when Present stops, and applies the idle policy after WM_SETCURSOR/WM_MOUSEMOVE. It does not replace the game WndProc or consume messages; CallNextHookEx preserves the chain. Watch installation requires the HWND to belong to this process/render thread; failure/multiple devices disables cursor management locally. Final shutdown detaches before native Release. Desktop behavior still needs Stage F observation. No ShowCursor display-counter operations or ClipCursor are introduced. AutoHideCursor defaults1 but Stock/Windowed remain unmanaged; delay0..60000ms (default1500), invalid values disable this feature locally.

Numeric selectors preserve text spelling: Display0Stock/1Windowed/2Borderless/3ExclusiveFullscreen; Widescreen0Stock/1Centered4x3/2PreserveMargins; AA0Stock/1MSAA; Shadows0Stock/1Off; Reflections0Stock/1ViewDependent2D. Boolean0/1 and true/false accepted. No numeric wrapping: invalid enum falls back locally with reason. Samples=4 still does not enable AA without Mode1/MSAA.

Backdrop work is an exact identity manifest and replacement layout contract only, separately marked ASSET_EXTENSION_REQUIRED. [Current handoff](runtime-handoff.md) has A-H, superseding old A-G. No new branch/worktree, disk patch, generated binary commit, deployment, push or next-phase implementation.

## Historical R-GFX5-2 record (superseded where stated above)

# R-GFX5-2 implementation and retained contracts

`quality.hpp/cpp` owns display planning, bounded native AA retries, pinned Windowed dimensions and post-success window commit. `quality_wrappers.cpp` owns native Reset/Present/viewport forwarding and logical getters. `visual_wrappers.cpp` routes SetTransform through the production setter helper, validates the discovered UI caller and current ortho matrix, and records live proof for subsequent cached UI/aspect updates.

`compatibility.hpp/cpp`, generated `fingerprint_recipes.hpp` and [recipes](fingerprint-recipes.json) provide unique, section-local, decoded owner validation. `menu_freeze.cpp` revalidates an enabled owner and preserves its transactional single-byte change/rollback/already-patched behavior. `provenance.cpp` logs R-GFX5-2 and per-feature compatibility; unknown SHA no longer disables D3D-generic functions.

Generated interfaces preserve every ABI slot, COM identity, parent references and raw child resources. A small testable setter helper takes the already captured return PC; the exported COM SetTransform still obtains the original game's return address. Root transfers the planner with its actual adapter/type/HWND/descriptors to the device.

Preserved: AF stage0 MIN-only/cappedMax; MAG/MIP/stage1 Stock; gameplay VFOV/CPU synchronization; frontend45 exclusion/five cameras/backview; shadow Stock/Off; resource generations/poolReset; race/HUD lifetime; dynamic/stationary constellation discovery; sticky brake identity; learned body0x152 signatures; wheel0x112/brake0x102/alpha/static exclusions; draw-local reflection/exact TCI restoration. Camera/culling, reflection/classifier/semantic/resource algorithms and PreserveMargins source/rules/bridge have no continuation diff. No grace, texture, strength, light or vertex-RGB tuning.

Trace remains schema1 with additive fields and version R-GFX5-2. Quality records include raw/logical/effective PP, physical surfaces, pinned target, commit status, requested/effective AA sample count and named swap. UI events show requested/effective matrices, UI32, widescreen_applied/source, virtual width/extra/half. UI differences no longer use the FOV2 draw marker. Existing capture allocation remains bounded at32MiB.

`generate_fingerprints.py` is read-only for its hash-locked input, decodes instructions and emits only phase-local curated recipes. `audit_quality_runtime.py` reads bounded session/F10 JSONL and produces counts/hashes; it does not infer human visual PASS. Native compatibility tests exercise the real production verifier and optionally inspect an existing PE file without mapping/executing it. Python tests cover generator hash rejection without writes, complete decode, unknown callee rejection, recipe normalization, audit semantics and the production UI capture. Old capture assertions remain; filters select the new producer label and identify the original positive MSAA4 fixture alongside the new UI fixture.

Native quality tests cover plan/native/commit order, no window mutation on native failure, failed Reset retaining accepted descriptors, idempotent commit, configured and automatic pinned sizes, invalid first auto target, hidden real decorated/popup/restored HWND, corrected production setter, wrong caller/shape, cached proof, native rejection and FPU state. COM/ABI/FPU, vehicle/reflection/Reset and camera suites remain passing.

Limits: synchronous game message behavior after commit still needs real runtime proof; successful native creation alone is not a Borderless PASS. A failed Win32 commit retains native descriptors and logs rollback status. Split-camera packet margin timing, mixed DPI, monitor migration and unreviewed backbuffer preservation remain unproved. No general x86 decoder or relocated absolute-global support is claimed.
