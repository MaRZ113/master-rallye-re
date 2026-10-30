# Dakar 2 Xbox renderer research — v7.4

29 October 2026. Baseline `423e8b714042db7a722e60bd2d6e98625614c3e9`, initially clean `research/vehicles`. This extends the accepted L1 decoder, not the platform audit. Original Xbox executable/container hashes remain pinned; GC and PS2 stay research-only. No MR compiler, candidate, CarID or physics edits.

## Result and qualification boundary

Derived Pajero and Hino UVS projects now use explicit per-draw source-state research, original vertex colors, native pass order and depth writes. The pale wheel-overlay defect is substantially reduced and the original complete rest assemblies can be inspected without selecting a diagnostic no-cull override. This is **L2 WARN**, not source-renderer parity: the default source cull context is statically inferred, full Xbox vertex/pixel shaders and dynamic equipment are not reproduced, and original Xbox runtime captures were not available in the inspected owner-local source/evidence folders.

The original L1 scene directories remain immutable. New private projects are under `.research-output/vehicles/dakar2-fidelity/final/{PAJERO,HINO,NISSAN}/scene/scene.json`. Source Garage reopens all three, renders actual D3D9 captures and keeps native Create disabled. The application previewer was rebuilt through the existing build script; prior MR preview scenes retain MRPV v1 behavior.

## Native evidence

Same original XBE SHA256 `715db4e407b38c0a6d14ea0ee9d08ebc524b9ece92ceeaa70b5fb81a5ec32378`. REA's prior XBE limitation remains; existing Ghidra 12.1.4 project was extended. Capstone 5.0.7 was installed only in ignored scratch for independent x86 instruction checks, not vendored. All addresses below are original virtual addresses; private `native-evidence.json` binds original section-byte hashes and exact declaration/pixel-definition records. Pseudocode remains static interpretation, not original source or runtime evidence.

| Field / path | Original evidence | Qualification |
|---|---|---|
| Per-draw culling | 0x87700 submits state 0x93 as `enabled[3] ? requested : 0`. 0xe3f50 emits NV097 0x308 enable and 0x39c face; 0xe3fc0 emits front-face 0x3a0 | Native state translation verified statically. Actual frame state not observed |
| Default vehicle context | 0x344f0 disables state3 at 0x34703. Vehicle 0x5ee50 enables depth state2, sets depth writes at 0x5ef7a, then calls 0x46ae0; those paths do not re-enable state3. 0x880e0/0x88100 write enable bytes; state3 is 0x23957f | Default scene-context inference: cull NONE. It is stored explicitly per draw, not applied as a universal material repair |
| Front convention | 0x868b0 selects requested convention; 0xe3f50 compares it to front-face state before selecting FRONT/BACK | Original mechanism recovered. No single forced CW/CCW convention asserted for all game contexts |
| Strips / parity | 0x8b590 sends original primitive and index count to 0xe5e30; original NV2A strip is 6 | Original index strip preserved; degenerate steps retain parity. No normal-driven face flips |
| Determinants | L1 Pajero/Hino local rest bases are identity; normalization mirror Z has determinant -1. Existing UVS staging reverses derived triangle winding and inverse-transpose transforms normals | Verified derived conversion; original arrays remain unchanged |
| Original colors | Original stream3 BGRA is now carried into disposable preview vertices | Exact color bytes retained/applied. Original lighting transformation of those inputs still approximate |
| UV0 / UV1 | Streams9/10 retained; original declaration at 0x193bb8. 0x8b590 binds four textures from submesh +0x10..+0x1c | UV0 preview qualified as input. UV1/secondary shader operations preserved as unresolved, not assigned generic MR roles |
| Shader selection | Declaration table 0x1940b8 has 20-byte entries. 8/13 use vertex program 0x192588, pixel definition 0x192148; 0x51a08/0x51a13 use 0x192850 / 0x192058 | Exact program identities/hashes and 60-word original pixel definitions retained privately. Neutral `T0 * original color` is explicitly an approximation |
| Blend | 0x8b360: mode0 disables; mode3 SRC_ALPHA / ONE_MINUS_SRC_ALPHA | Applied per declaration; original final shader alpha is not reduced to a proven texture0-only rule |
| Depth writes | 0x5ef7a → 0x86900(1) → state0x40; declaration blend3 does not disable it | Enabled in derived vehicle preview, including translucent wheel-sidewall draw. This removes much of the old back-surface overlay |
| Pass order | 0x46ae0 draws LOD flags without bit0x08000000 first, flagged nodes second; source ordinal/submesh order retained | Static original pass separation reproduced; scene-wide sorting and active runtime visibility remain unresolved |
| Alpha test | 0x86920 maps comparison values, state0x3a/0x3d. Second pass conditionally enables alpha test and GREATER reference100 from 0x18eab4; state0 is 0x23957c | Mechanism recovered. Exact active node-ID/equipment conditions not fully traced, so derived preview leaves test UNKNOWN rather than using one global cutoff |
| Texture addressing | 0x8aed0 maps original XTX flags to U/V addressing via 0x874a0 | Raw flags retained; current sample uses wrap. Full sampler/LOD/filter runtime parity not asserted |

The primary [NV2A register definitions](https://github.com/xemu-project/xemu/blob/master/hw/xbox/nv2a/nv2a_regs.h) corroborate method numbers/front-face/primitive constants. [Pixel-combiner definitions](https://github.com/xemu-project/xemu/blob/master/hw/xbox/nv2a/pgraph/psh_regs.h) document register encodings used to inspect the original pixel-definition words. No implementation from these LGPL files is copied. Original secondary combiners, source lighting and runtime fog are not guessed from their mere presence.

## Scene and preview architecture

`dakar2_fidelity.py` reads the qualified original executable directly from XDVDFS and records exact executable table/function hashes. It derives inspection projects from validated immutable L1 projects, preserving all positions, normals, UVs, triangles, source strip/stream records, compressed textures and original snapshots. Four native texture slots are now explicitly audited, including the usually empty fourth field. Original source semantics remain visible.

The reusable preview transport adds **MRPV v2**, retaining v1 compatibility. V2 has the same texture/draw/vertex/index layout, plus 12 bytes after each draw header: cull (1 NONE / 2 CW / 3 CCW), depth-write boolean, blend boolean. `--source-states` is explicit and only accepted in neutral-source mode. Default native MR views are unchanged. Source state mode preserves staged original pass order; ordinary previews retain existing alpha sorting. Diagnostic CW/CCW/NONE still override culling without activating source state mode. No original polygons are modified to produce the improved appearance.

Private final evidence: each vehicle has six fixed front/rear/left/right/top/isometric views in `views-source`, `views-cw`, `views-ccw`, `views-none` (72 images total). Source-state captures are reconstructed static approximations, diagnostic captures are labeled separately, and original runtime effects remain unknown. Lamp/glass diffuse/alpha inputs survive; reflections, animated lamps, dynamic shadow, wheel steering and gravity-settled suspension are not simulated. Pale/bright interior surfaces and differences from source lighting can remain; no L2 PASS is claimed.

## Nissan transform and variants

Nissan now reconstructs with an explicit qualified-rotation option: 39 nodes, 51 meshes, 3780 vertices, 4065 triangles. 0x46da0 copies the original HIR nine basis values into the runtime bone matrix. 0x88eb0 uploads compact basis+translation as D3D row vectors. UVS uses column vectors, therefore the original basis is transposed and translation retained. Synthetic quarter-turn and reflection tests independently verify that conversion; scale/shear/nonfinite bases remain rejected. The old default fail-closed rotated-basis gate remains unless qualification is explicitly requested. `MID_R_EXHAUST` is no longer assigned a guessed matrix. Source label remains Nissan Pickup; D22 generation is not newly proven. Runtime animation/visibility remain WARN.

39 Pajero/Hino/Nissan named variant members were inspected structurally, with exact original member hashes, resource counts and named burnt alternatives. Example XMD counts: Pajero 0_0=42, 0_1=10, 1_0=37, 2_0=25; Hino 39/5/28/25; Nissan 39/14/33/16. Some members contain no XMD. Names/counts do not prove active LOD distance or equipment policy. No fleet importer or speculative equipment switcher was added. Private `variants.json` and per-project variant inventories preserve this boundary.

## Reproduction

Use fresh ignored output directories. The existing original scene remains the input, not an exported OBJ or screenshot reconstruction.

```powershell
python tools/build_rally_workshop.py
python tools/dakar2_renderer_lab.py --xbox "E:/RallyWorkshop_Sources/sources/Dakar 2 Xbox/Dakar 2 - The World's Ultimate Rally (USA).iso" --source .research-output/vehicles/dakar2-source/final/PAJERO/scene/scene.json --output .research-output/vehicles/dakar2-fidelity/owner-pajero --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe
python tools/rally_workshop.py --source-scene .research-output/vehicles/dakar2-fidelity/final/PAJERO/scene/scene.json
```

Use HINO with its original L1 scene; `--nissan` creates a new private original snapshot with qualified compact rotations before deriving renderer inspection. Original images and all accepted projects stay read-only.

Focused validation: 70 tests pass, including six new source-free rotation/reflection/shear/color/state/determinism cases. Full Windows suite and private preservation/determinism reports are recorded with this delivery. `repeat-validation.json` verifies identical scene/manifest hashes and every original sidecar for all three. Real Tk Source Garage reopened/rendered each scene without errors and native Create remained disabled. No original Xbox runtime qualification, new MR gameplay claim or Silver suspension adjustment.

Final available Windows run: **1158 tests OK, two pre-existing optional skips, 67.186 seconds** (`windows-regression-delivery.log`). Protection audit: **10167 files / 15182553873 bytes, no changed or missing files**. Private `render-report.json` lists each node/draw, original stream hashes, local determinant, LOD flags and explicit state. `repeat-validation.json` pins deterministic scene/manifest hashes. Real Tk evidence is `gui-final/validation.json`. Interactive **K** enters explicit cull diagnostics; **J** restores source draw states. These switches affect only the preview. Review archive CRC/member hashes and exact retained v7.4 are checked after the scoped local commit.

The final native application was also exercised directly: source-state mode starts enabled, K enters explicit cull override, J restores source states (`interactive-states-validation.json`). This tests preview controls only, not original Xbox renderer state.


## Source Garage hardening follow-up — 30 October2026

Original XBE/cull/depth/blend/pass/compact-basis evidence above is preserved. No shader, cull or polygon rewrite. Separate typed-UV1 derived scenes expose132 actual stream10 arrays:42 Pajero,47 Hino,43 Nissan; all132 exactly alias corresponding UV0 in these selected members. Raw streams and original scenes remain immutable. Typed data exposure is deterministic and leaves staged MRPV and three before/after D3D9 images pixel-identical. This closes data association, not secondary-combiner/lighting/alpha/sampler equivalence. Shared native preflight now rejects silent UV/stage loss; all three lack qualified native material/wheel/glass/lamp/physics authoring policies and remain BLOCKED for native entry, L2 WARN. Hino four recovered wheel nodes are not proof of arbitrary native axle capacity or unsuitable SUV physics. Nissan still uses only the qualified rigid path, with scale/shear/nonfinite rejection intact. Default static member/variant policy and equipment unknowns remain explicit. Three internal Pajero spares and the separate authored external experiment are preserved; no backing discs/art or fleet import. Owner PCSX2 observations remain PS2 historical reference, not Xbox runtime evidence. See SOURCE_GARAGE_QUALIFICATION_MATRIX.md.
