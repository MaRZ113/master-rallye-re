# Dakar 2 Xbox vertex-program and material closure — v8.1

30 October 2026. Clean starting revision `5ef073c44008b83f63cb767a00671aee0175cabd`, `research/vehicles`. This is a bounded continuation of the accepted decoder. No file-format rediscovery, source-scene edits, new native compiler, CarID, playable fixture, RAV4 correction or Evo2 color work.

## Result and limits

**L3 material readiness remains BLOCKED for all three vehicles.** The missing mechanism is now specific: selected vertex fragments generate lighting-dependent V0 and position/normal/world-dependent T2; the native MR environment helper has no verified equivalent for independent T1 alpha weighting, T0 output alpha and these T2 coordinates. Exact per-draw runtime selection/constants are not captured. A permanent diffuse composite would lose required effects.

Recovered and independently checked: original fragment selection/linking, base V0/T0/T1/T2 instructions, initializer c65, matrix-register ownership, conditional node alpha-test, source wrap addressing and initial pixel-constant upload. These are **static original instructions plus controlled original CPU execution**, not an Xbox GPU image or proof of effective state for every running draw. Original Xbox runtime/PGRAPH evidence is MISSING INPUT in the inspected local roots. PCSX2/Xenia are not substitutes.

## Original executable and implementation

Original `default.xbe` SHA256:
`715db4e407b38c0a6d14ea0ee9d08ebc524b9ece92ceeaa70b5fb81a5ec32378`.

The existing read-only Ghidra `Dakar2Xbox/mapped-xbe.bin` project and independent Capstone instruction decoding were reused. New exports stay in ignored `scratch/dakar2-material-closure/`. Final probes read original XBE sections from the pinned owner ISO; they do not trust a modified mapped dump.

- `nv2a_vertex.py`: bounded four-DWORD vertex-token decoding, typed operands/writes, readable inspection and a deliberately limited floating-point arithmetic diagnostic. Unknown operations, relative addressing, undefined requested outputs and missing constants fail. It is not a full GPU emulator.
- `dakar2_vertex.py`: exact-build reads, independent non-optimizing fragment concatenation and bounded Unicorn execution of the original CPU selector/linker and constant-upload paths. GPU binds/uploads are intercepted at the reported ABI boundary.
- `dakar2_coverage.py`: original HIR-kind/LOD coverage and original per-texture address flags, with explicit entry/reference context.
- `dakar2_materials.qualify_closure`: source-bound per-draw evidence and refined native blockers. No `omit_for_mr` permission or native fixture is emitted.
- `tools/probe_dakar2_vertex.py`, `tools/probe_dakar2_coverage.py`: reproducible private diagnostics; fresh output must be disjoint from original source roots/scenes.

The factual vertex bitfields were cross-checked against [xemu's register definitions](https://github.com/xemu-project/xemu/blob/master/hw/xbox/nv2a/pgraph/vsh_regs.h) and [vertex translation implementation](https://github.com/xemu-project/xemu/blob/master/hw/xbox/nv2a/pgraph/glsl/vsh-prog.c). No third-party implementation is vendored. The inspected xemu implementation initializes temporary registers; that behavior is not adopted as proof of original NV2A hardware initialization. Original lit R11 remains an explicit diagnostic input.

## Original composition

`8b360 → 8d930 → 8d800` combines original fragments, then original `f85bb` concatenates and `e1170/e0f10` bind the program/declaration. The original non-optimizing linker clears each intermediate final bit, concatenates intact tokens and sets only the final token's termination bit. Independent Python output matches original CPU output byte-for-byte.

| Controlled context | Simple base `192588` | Three-map base `192850` |
|---|---:|---:|
| Lighting disabled, no fog/texture matrices | 11 instructions | 27 instructions |
| Directional light slot0 plus ambient | 20 instructions | 36 instructions |
| Point light slot0 plus ambient | Context separately retained | Context separately retained |
| Fog and all four texture transforms | Context separately retained | Context separately retained |

All eight combinations are probes with explicit state, not a claim that all eight occur on these cars. Counts, exact fragment identities/hashes, CPU instruction counts and semantic listings are in private `vertex-evidence.json`. No shader binary is exported or packaged.

The unlit prefix `1939a0` writes R11 from c65.z; lit selection loops eight enabled light slots, chooses directional/point fragments, then adds ambient c40. The base multiplies R11 by source input v3, replaces R11.w with v3.w, and the suffix `19385c` writes V0. Consequently **V0 RGB is not generally the raw source color stream**; V0 alpha in these base paths is source v3 alpha.

Directional slot0 transforms the normal with c14/c15/c16, normalizes it, computes max(dot(normal,−c42),c65.x), and accumulates the coefficient times c43 into R11. Point slot0 uses c41−v0, its reciprocal length and dot(v2,direction), then accumulates c43. These are instruction relationships, not a claim of physically correct generic lighting. In particular c14..17 are uploaded from WVP in the traced matrix path; no substitute normal matrix is silently inserted. The initial lit accumulator, light parameters and effective runtime selection remain required state.

## Matrix and c65 proof

Original initializer stores at `86bb0..86bc4` and upload at `86f3a..86f5b` establish initial **c65 = [0, 0.5, 1, 2]**, using hardware index161. Two bounded original initializer slices reproduce the upload without executing unrelated graphics/device initialization.

Original `8cda0`, its matrix copy/multiply/transpose helpers and original stack pointers were executed with asymmetric, explicit world/view/projection fixtures. Only upload/deferred-state functions were intercepted. All 1,375 CPU instructions complete, and the independent matrix calculation matches every uploaded float:

| Vertex constants | Original source |
|---|---|
| c0 | Last row of current view matrix |
| c6..9 | Transposed current world matrix |
| c10..13 | Current projection storage |
| c14..17 | Transposed world × view × projection |
| c66..69 | Transposed world × view |

Do not call c6..8 a view matrix. What the running engine places in its current world stack, and whether an upstream context is camera-relative, remains uncaptured. The initializer is not proof against every later constant overwrite.

## Texture outputs

Without optional texture-transform suffixes:

- T0 = v9, the original first UV input.
- T1 = v10, the original second UV input.
- Let P be the first three dot-products of v0 with c6..8; let N be the three dot-products of v2 with c6..8. The base computes R = P − 2 dot(P,N) N, normalizes R, then T2.xy = 0.5 R.xy + 1; T2.w = 1 at initialized c65. T2.z retains the normalized vector's z component.

This is normal/position-generated sampling, **not UV1 or UV0 reuse**. N is used as encoded by the original instructions; a replacement normalization is not inserted. All 132 stored UV1 arrays still exactly alias UV0. That says nothing about T2.

Optional `8ca90` fragments can replace texture outputs through per-stage matrices. For example T0 becomes four dot-products of v9 with c18..21. Original enable flags and corresponding matrices must be captured before claiming the base outputs are effective on every draw. The complete selected fragment listings preserve the other outputs rather than guessing their inputs.

## Constants, coverage and addressing

See [DAKAR2_COVERAGE_EVIDENCE.md](DAKAR2_COVERAGE_EVIDENCE.md) for the complete original evidence and CPU reproduction.

Original `e6250` uploads embedded stage1 C0 alpha89/255, checked independently for both selected pixel definitions. Later overrides/effective every-draw state remain unproven. The pixel evaluator still requires an explicitly supplied mapped constant; no embedded-default fallback was added.

Original `46ae0` first pass inherits entry alpha state. In the second pass only, HIR kind1..7 or LOD flag0x10000000 enables GREATER with the current reference global; after each second-pass node it resets ALWAYS/0 and disables testing. The original initialized reference100 has a known temporary10 writer elsewhere. Controlled original CPU replays at both references agree with the independent rule. HIR kind is not the UVS sequential ordinal.

| Vehicle | First pass | Second pass without explicit cutout | Second pass explicit cutout | Simple / three-map draws |
|---|---:|---:|---:|---:|
| Pajero |38|10|8|14 / 42|
| Nissan |30|13|8|8 / 43|
| Hino |41|6|0|0 / 47|

The eight cutout draws on each smaller vehicle are its four road wheels × two groups. Hino wheels are first-pass; do not copy that predicate onto them. Pajero internal spares are kind0. Window/headlight-cover labels do not select automatic cutout or prove glass opacity.

All 37 retained XTX resources have flag7; original binding argument2 forces source low-bit addressing and selects wrap U/V. Unknown flag0x4 is retained. Filtering/mips and full hardware PROJECT2D behavior remain outside this CPU point-sample proof.

## Separate material categories and native alternatives

Every original draw has exact source node/mesh/material, shader/bindings, blend/depth/cull inference, controlled coverage, source hashes and explicit blockers. No role is exempted by a successful body example.

| Category | Source ownership evidence | Native qualification |
|---|---|---|
| Painted body / sponsor artwork | Original BODY/MAINBODY/BONNET/BACK/CAB groups, atlas bindings and source UVs | BLOCKED by V0 and required T1/T2; no atlas repaint or replacement |
| Windows / covers | Named SIDEWINDOW(S)/SIDESCREEN/WINDSCREEN and HEADLIGHTCOVER nodes, exact independent groups | BLOCKED; blend declaration/coverage retained, no automatic native glass opacity/damage |
| Rear lamps | Pajero L/RREARLIGHTS; Nissan RLIGHT/TOPRLIGHTS; Hino RLIGHT groups | BLOCKED; labels identify candidate geometry, not a verified brake controller or ON switch |
| Tyres / rims / interiors | Original road-wheel and spare submeshes and original texture bindings | Simple22 groups still require effective lighting/coverage/native proof; Hino wheels require three-map behavior |
| Cabin / crew | Original INTERIOR/INT/DRIVER/CODRIVER groups | BLOCKED under their actual shader; no substitute MR cabin |
| Optional equipment | Original rollcage, spotlights, axles, exhausts and three Pajero internal spare nodes | Geometry retained; effective original visibility/material context unresolved |

**A — exact static composite:** not approved. T2 depends on transformed position/normal and selected matrix state; V0 carries lighting. Source-rest/unlit samples can demonstrate arithmetic, but cannot become a universally valid livery texture, wheel texture or fidelity PASS.

**B — existing MR passes:** examined, not approved. The qualified native opaque environment helper uses baseRGB + baseAlpha × helperRGB. Xbox needs independent T1 alpha weighting while preserving T0 output alpha and its own generated T2. Repurposing coverage alpha on glass/cutout materials or assuming MR environment coordinates match would change behavior. Even for an opaque group, a complete coordinate/lighting/coverage proof is missing. No fragmented reflection geometry or second compiler was introduced.

**C — precise limitation:** retain L2 WARN / L3 BLOCKED. The 22 simple wheel/spare groups have no secondary-map blocker but still lack a proven effective original lighting/coverage context and native equivalence. The 132 three-map groups additionally lack an MR mechanism preserving their independent mask and generated coordinate contribution. Zero source-faithful native fixtures are authorized by current evidence. Hino truck physics/wheels/collision are separate, uninvestigated native boundaries.

## Private previews and remaining evidence request

Private root `.research-output/vehicles/dakar2-material-closure/qualification-run1/` contains:

- independent per-draw qualification and controlled coverage for 56/51/47 groups;
- three bounded source-stream samples per draw in two explicit rest/shifted-world contexts;
- `controlled-stage-points.png/json`: original sampled base, mask, secondary contribution, composite and shifted-world composite, using explicitly supplied unlit state/89 alpha and nearest-wrap sampling;
- front/rear/left/right/top/isometric actual D3D9 captures for each unmodified source scene, **18 captures**. These retain the existing single-stage approximation and its L2 WARN. They are not falsely labelled corrected multi-stage output or native MR fixtures.

Point samples are not rasterized screenshots, do not establish filtering/alpha boundaries between pixels and are not source-runtime fidelity evidence. The current D3D9 viewport cannot express the complete shader. No attractive diagnostic is substituted for native validation.

The minimum useful future Xbox/PGRAPH capture is the selected composed vertex program; its c6..9/c14..17/c18..33/c40..69 and viewport registers; active light/texture-matrix flags; final pixel constants after overrides; stage addressing/filter/mip state; alpha enable/compare/reference, blend/depth/cull and actual equipment visibility, tied to one exact draw and original resource IDs. First capture one painted body, one window and one road-wheel draw on Pajero; then independently corroborate Nissan/Hino. No emulator was installed or game launched during this milestone.

## Reproduce

```powershell
$env:PYTHONPATH='src;.;tests/synthetic'
python -m unittest test_nv2a_vertex test_dakar2_coverage test_dakar2_closure test_dakar2_materials
python tools/probe_dakar2_vertex.py --xbox "E:/RallyWorkshop_Sources/sources/Dakar 2 Xbox/Dakar 2 - The World's Ultimate Rally (USA).iso" --scene .research-output/vehicles/dakar2-fidelity/final/PAJERO/scene/scene.json --scene .research-output/vehicles/dakar2-fidelity/final/NISSAN/scene/scene.json --scene .research-output/vehicles/dakar2-fidelity/final/HINO/scene/scene.json --output .research-output/vehicles/dakar2-material-closure/fresh-proof --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe
```

The full original source scenes, textures, vertex/index streams, transforms, Nissan basis and Hino assembly remain unchanged. RAV4 A/B/C/D and Evo2 nine-color outputs are preserved. Test/preservation/archive counts are recorded in the regression matrix and metadata-only `DAKAR2_MATERIAL_CLOSURE_PROVENANCE.json`. Stop at this evidence boundary; no new native import follows automatically.
