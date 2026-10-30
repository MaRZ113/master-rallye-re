# Source Garage qualification matrix — 30 October 2026

Baseline `c557ed626722aa709384d150647dafd574c45f0a`, clean `research/vehicles`. Scope: existing Evo2, Dakar2 Xbox, Michelin and PC Paris-Dakar Silver regression reference. No new donor, CarID, native runtime candidate, roster capacity or accepted-project edit. The RAV4 owner is testing the preceding candidate; this work neither replaces it nor promotes its gameplay result.

## Levels and severity

L0: identified snapshot/source integrity; L1: structure; L2: source rendering; L3: native MR qualification; L4: actual owner D3D8. PASS at one level never upgrades another. Shared `source_qualification.preflight` deliberately leaves L3 WARN for successful geometry/material dry runs: it does not validate native controllers, physics or collision. Complete earlier native-pilot evidence remains separately applicable to exact preserved resources. `native_geometry_compiler_allowed` does not mean `native_entry_allowed`; the latter stays false until separately qualified native assembly/gameplay workflow.

P0: corrupted/lost/unstable source data or transformations; P1: native geometry/material/wheel/namespace blocker; P2: original shader/dynamics fidelity; P3: optional art. P0/P1 must be fixed or reported BLOCKED. P2 may remain a bounded WARN; P3 is excluded. UNSUPPORTED describes a missing mechanism, BLOCKED describes its consequence for a selected conversion. NOT TESTED is not PASS.

| Vehicle / resource family | L0 / L1 | L2 | Current L3 evidence and remaining entry gate | L4 historical boundary |
|---|---|---|---|---|
| Evo2 T4RSR52 /4RUNNERSR5.SMF |PASS/PASS|WARN|Exact accepted source-baseline DX/DXT regression PASS; generic dry-run WARN for legacy diffuse-only bump/material interpretation|Owner demonstrated playable; no new gameplay run here|
| Michelin Car25A /RAV4 ID25/A |PASS/PASS|WARN|v7.7 isolated native pilot offline qualified; exact baseline resources preserved. Shared semantic partition/conservation PASS; owner feedback pending|NOT TESTED by this stage; owner currently testing|
| Michelin Car06A /Mégane F2 ID6/A |PASS/PASS|WARN|Geometry-only fixture PASS; pane/lamp/controller/physics authoring unqualified, therefore full native entry BLOCKED|NOT TESTED; no native candidate|
| Dakar2 Xbox PAJERO_HI_0_0 |PASS/PASS|WARN|UV1 data aliases PASS; secondary shader/material policy, native wheel/glass/lamp/physics mapping BLOCKED|NOT TESTED; PS2 owner observation is not Xbox parity|
| Dakar2 Xbox HINO_HI_0_0 |PASS/PASS|WARN|Same shader/material blockers plus dedicated truck collision/physics qualification. Four recovered wheel nodes do not establish a new MR wheel-capacity limit|NOT TESTED|
| Dakar2 Xbox NISSAN_HI_0_0 |PASS/PASS|WARN|Qualified rigid transform path retained; secondary materials and native assembly policy BLOCKED; no guessed basis bypass|NOT TESTED|
| PC Paris-Dakar Silver #271 |PASS/PASS|WARN|Exact accepted source-baseline DX/DXT regression PASS; existing native pilot remains independent|Owner-launched; stiff suspension remains separate reversible tuning WARN|

The current automatic corpus always reports L4 NOT TESTED, preserving historical owner observations separately rather than treating static validation as a fresh gameplay test. Trooper/Subaru/Lancer/Pajero85/Clio, GT Garage and existing native alternatives remain protection/full-suite references.

## Exact identity anchors

Original primary hashes, not names alone, bind these rows. `SOURCE_GARAGE_CORPUS_PROVENANCE.json` records exact accepted scene and derived-output hashes; complete original resources remain in private manifests.

| Anchor | SHA256 |
|---|---|
| Evo2 executable4x42.exe |`ab8286e6bce8a1bf3769acddfeb0a79df2e5d43c72f462a89aa90f477951ec75`|
| Evo2 TRUCK.POD |`5669509d709193621802a43c2c63b32e537fcf93ea3fd5d94af8c66947be6a41`|
| Evo2 T4RSR52.TRK |`d2ff6c5914e8102116e56704dac800442fed3adfbf42326c6b3311517e8bbcb4`|
| Evo2 body SMF |`a7f71e0ae1cae2fb64438ce8614bf7db47eb9dfc813d926388da4dfef7b6a11e`|
| Dakar2 Xbox default.xbe |`715db4e407b38c0a6d14ea0ee9d08ebc524b9ece92ceeaa70b5fb81a5ec32378`|
| Pajero selected LOD |`c5f68222a329d538c83ca0fc8f22be5581fa200b9f9dbd759e745a6b956cb713`|
| Hino selected LOD |`8cda26ab1a0f5b893e140ec9477b99a20fef16ead55015dda71ab5464d5ecd1b`|
| Nissan selected LOD |`fc9fe217dcde92e98d2a187aa73d524c5272fab8b6dc3bad10b63f48703b570b`|
| Michelin RallyMasters.EXE |`71c6c36505102e75518a7f6843bbc8355f205e439086e389ec877225e3e0a8ae`|
| Michelin Car25A.PDO |`bbbc58fe11456369231e595444d43377f94cc3f19af2e2057a4ec68a07802593`|
| Michelin Car06A.PDO |`f0a9400812814620832b4a3fe98a024318de72b929ba225a90c4a57e342e1a5b`|
| Silver accepted UVS |`9d3edfe6b4a5187a44946784c6fb1f836eed1ec311c6f8c42f0bf388108342c9`|

## Shared correctness and native blockers

Reproduction `A`: focused synthetic tests in test_scene_semantics.py, test_universal_vehicle_scene.py, test_universal_scene_bridge.py, test_dakar2_fidelity.py. `B`: tools/qualify_source_garage.py, exact corpus above. `C`: tools/validate_source_qualification_windows.py. Tests preserve both successful cases and adversarial rejection cases.

| ID / scope / severity | Original evidence, previous versus expected behavior | Source Fidelity / native effect; fix and validation | Final status |
|---|---|---|---|
| SG01 all raw streams, P0 shared | UVS source.streams carried a hash/stride but `_bindings` did not independently bind that claim to manifest members. A rebound transport manifest could disagree with the retained source claim | universal_vehicle_scene._bindings now checks every stream path/hash/stride/vertex-count size. A altered UV1 file plus self-consistent manifest must fail before exposure/native conversion. A/B |PASS resolved|
| SG02 source colors/secondary UV, P0 shared | Per-corner colors could fail only on preview/compile; additional typed UV association had no common validator | validate_scene checks color bytes/counts and optional typed uv_channels1..3, exact vertex association, finite values/evidence; save/reopen fail closed. Existing v1 fields unchanged. A/B |PASS resolved|
| SG03 UV/stage loss, P1 shared | Diffuse-only compiler could ignore retained stream10 and secondary texture bindings without a per-feature decision | scene_semantics.features/feature_policy gate all selected extra UV/stages. Missing policy rejects; omit_for_mr requires exact scope/evidence/impact and remains WARN. Equal UV alias can PASS data conservation only. A/B |PASS guard; shader support UNSUPPORTED|
| SG04 mixed part ownership, P1 shared | No universal triangle-role contract for glass versus paint/frames/lamps | Hash/material/mesh-bound claims reject overlaps, duplicate/out-of-range faces and role guesses. Native alpha-blend rule cannot include unqualified body/frame triangles. A, actual RAV4 recipe B |PASS resolved boundary|
| SG05 fragmented reflections, P1 shared | A fragment could be called a reflection-eligible surface without proving complete material coverage | Reflective-paint eligibility requires every face of all original meshes sharing that material; native reflection needs that contract. No overlay polygons generated. Previously accepted diffuse assets untouched. A |PASS guard; source reflection shaders WARN|
| SG06 semantic partition, P1 shared | Repeated per-vehicle primitive splitting risks missing/duplicated faces or implicit material changes | scene_semantics.partition conserves exact compiled surfaces and source-face bindings, leaves unknowns, keeps colors/UV/flags, ignores damage/reflection overlays as duplicate geometry. Native services remain explicit. A/B |PASS implemented|
| SG07 wheel controllers, P1 shared | A geometric scene with1..16 wheel nodes is valid; it does not prove qualified MR four-controller assembly | Preflight requires explicit front_left/front_right/rear_left/rear_right for existing native authoring path, reports BLOCKED otherwise. Compiler still preserves geometric instances. No new roster/wheel capacity inferred. A/B |PASS guard; arbitrary rigs UNSUPPORTED|
| SG08 transforms/material output, P0 shared | Source versus compiled geometry must be measured, not accepted from a screenshot | Common preflight checks inverse vertices/UVs, transpose-normal roundtrip and determinant winding, repeats compilation and native fixtures. Accepted3 DX resources per native reference and23 emitted DXT resources exact. B |PASS, exact per-vehicle errors in provenance|
| SG09 missing native policy, P1 shared | Valid source scene alone cannot authorize inferred wheel/physics/glass/namespace choices | No supplied qualified authoring profile => L3 BLOCKED; successful compiler dry-run => L3 WARN, full native entry still false. Source Garage dialog exposes boundary and unknowns; C runs with hidden windows while owner game stays foreground |PASS implemented; current Dakar2 entry BLOCKED|

## Engine-specific remaining issues

These source-specific rows reference the exact identities above. Existing native evidence addresses/hashes remain in EVO2_SOURCE_SEMANTICS.md, DAKAR2_RENDERER_RESULTS.md and MICHELIN_FIDELITY_QUALIFICATION.md. No claim below turns decompiler pseudocode into original source or proves original runtime equivalence.

| ID / game / severity | Unknown and available evidence / module | Current preview and native impact | Resolution / required verification / status |
|---|---|---|---|
| E01 Evo2 second TIFF sample, P2 | ExtraSamples0 unspecified, two8-bit indexed samples; evo2.decode_tiff. New4x42.exe004273d0 dual-plane color consumer has mixed recolor/high-byte branches; full TIFF plane linkage not reconstructed | Original samples/palette retained; opaque diffuse is explicitly interpreted. Native MR must not key this plane as ordinary alpha | Bounded WARN. Original loader/renderer plane association still required; no source alpha override applied |
| E02 Evo2 nine colors, P2 | Nine original TRK records retained;005d7980 chooses record+0x207c/2080/2084 and uses float64 divisors360/100/100 before004273d0 | Neutral base texture is not simulated active running-game color selection. Existing source livery/native project unchanged | Records/native HSV loader PASS static; full color output WARN. Original bytes/constants independently checked; no fabricated nine-color artwork |
| E03 Evo2 bump/reflection, P2 | Original bump TIFF/raw material bindings preserved; full material-light dispatch incomplete | Legacy accepted profile remains diffuse-only with explicit WARN; new semantic contracts require explicit bump omission. No generic reflections or atlas islands | Bounded WARN / source shader UNSUPPORTED. Need original draw/sampler evidence for source equivalence |
| E04 Evo2 auxiliary meshes, P2 | Stock BODY mask005d43f0/0067d198 excludes Axler/nine Light objects from BODY pass; separate dynamic consumers unqualified | Retained original nodes and visibility evidence, not deleted or claimed permanently absent. No new native dummy frame/lights | Bounded WARN; active axle/lamp runtime pass remains unqualified |
| E05 Evo2 wheels/rest, P2 | Six original L/R08/12/16 resources; high-detail transforms qualified;1.05 belongs only to low-detail branch | Selected detail16, literal hubs and original sides preserved. No size inference from suffix, no global1.05 or settled-pose correction | Static/native regression PASS; original steering/spin/settlement WARN |
| D01 Dakar2 UV1, P2 | Exact stream10 in dakar2_fidelity.expose_uv1;132 present streams across42 Pajero/47 Hino/43 Nissan meshes | All132 are bit/value-exact UV0 aliases in this corpus. Typed channels now inspectable, originals/streams untouched; staged images identical |PASS resolved data association/alias. Does not prove shader texcoord generation/effects |
| D02 Dakar2 secondary textures/combiners, P1 native/P2 source | Native8b590 binds four texture fields; original declaration/pixel words pinned. Their operation/mapping is not emulated | UV0*T0*color remains approximation; body/lamp/glass/wheel alpha cannot be assumed equivalent to source final shader |BLOCKED native material readiness; source shader UNSUPPORTED. Need bounded material interpretation with exact coverage, not global omission to force import |
| D03 Dakar2 lighting/alpha/sampling, P2 or P1 when coverage critical | Prior original XBE cull/depth/blend/pass evidence retained; conditional alpha-test reference100 known, activation/combiner alpha unknown | Per-draw source-state inference retained. No global cutoff, cull reversal, added reflection or wheel cap |WARN source parity; affected native materials BLOCKED with D02. Original Xbox runtime/sampler evidence still required |
| D04 Dakar2 LOD/equipment/spares, P2 |39 named variants retained; HIR and LOD flags establish structures, not full active selection. Three authentic internal spare nodes preserved | Explicit selected static member; external MR-inspired spare remains separate authored overlay, never Source Fidelity |Bounded WARN; no art/extra-spare or fleet work. Owner PCSX2 imagery is PS2 reference only |
| D05 Nissan rotation, P0 | Qualified row/column basis conversion46da0/88eb0 from v7.4; compact_transform rejects scale/shear/nonfinite bases | Original nonidentity hierarchy retained; old default rejection remains unless explicit qualified path chosen |PASS existing rigid path/regression; animation/runtime rotation WARN |
| D06 Hino MR integration, P1 | Four authentic source wheel instances; native truck physics/collision policy not selected | No SUV donor copied to demonstrate success; static geometric recovery does not prove MR axle/travel/weight behavior |BLOCKED dedicated native policy. No claim that MR cannot support trucks or supports arbitrary wheel counts |
| M01 Michelin wheels/units, P2 source/P1 native | Initial Cars.BIN hubs and0.34 subtraction qualified; original moving matrices/physical metres unresolved | RAV4 explicit proper MR rest basis and radius-derived uniform scale validated separately. Mégane fixture uses labelled authoring experiment, not game physics |RAV4 native rest PASS from v7.7; source runtime WARN. Current original neutral scene deliberately still shows identity-pose wrong-side backing; separate derived MR-rest views show distinction |
| M02 Michelin glass, P1 | RAV34 bounded original faces; Mégane67 flag0x30000 faces differ. Source blend still unknown | RAV4 qualified native pane recipe stays unchanged. Mégane grey opaque windows remain neutral; no door/pillar transparency or automatic damage-zone invention |RAV4 native ownership PASS; Mégane native mapping BLOCKED pending its own exact panes after RAV4 feedback |
| M03 Michelin cutout/filtering, P2 | Native magenta-palette sentinel and index0 coverage qualified; black remains opaque. Exact source alpha-test/filter/mips incomplete | Original RGBA retained; neutral blending approximation, explicit MR cutout128 in reviewed native profile |Bounded WARN source. Native coverage/alpha damage proof retained at exact resource hashes; no blanket alpha policy |
| M04 Michelin damage, P2 | External BINs are targets; intact XO/rest backup verified in prior EXE evidence | No averaging/substitution. Existing MR damage/alpha replay applies to preserved native RAV4; original damage playback not needed for first candidate |Intact separation PASS; original playback UNSUPPORTED, event/detachable mapping WARN |
| R01 Silver suspension, P2 native tuning | Owner launched Silver and reports stiffness | No physics/profile changes in this stage |WARN retained separate reversible Physics Studio task |

No remaining source renderer WARN is deleted. See SOURCE_GARAGE_WARN_RESOLUTION.md for changes and UNIVERSAL_NATIVE_BRIDGE_QUALIFICATION.md for reproducible usage, exact evidence and next recommendation.


## Cross-game material fidelity checkpoint — v8.0, 30 October 2026

Baseline `e7353076512431b5ec71456bde9c2d203eb77336` was verified as clean
`research/vehicles`. The complete attached v8.0 reconciles the prior Master by
insertions only: v7.8 owner feedback and v7.9/v8.0 history are retained without
deleting any earlier line. The live user request controls this milestone.

Dakar2 now has an original-byte-qualified60-word NV2A combiner decoder/evaluator
and154 per-draw material reports across Pajero56/Nissan51/Hino47. Multi-map RGB
is `T0.rgb*V0.rgb + T1.a*clamp(T2.rgb*C0(stage1).a)` with saturation, alphaT0.a;
simple materials multiplyT0 by vertex-programV0. All132 present UV1 arrays still
alias UV0, but original stage coordinate generation, V0 lighting, effective
mapped constant and conditional coverage remain required. **Material L3 stays
BLOCKED**, with no fake diffuse-only fixture. Source declarations/shader hashes
are a non-omittable shared bridge requirement, even if a caller waives stage
bindings. Hino truck physics/collision/suspension remain independent blockers.
See DAKAR2_NATIVE_MATERIAL_QUALIFICATION.md.

Evo2 original TIFF loader byte routing and isolated original x86 pre-gloss
consumer establish sample0 palette indices and sample1 recolor/high-byte control.
Auxiliary<=128 retains RGB;255 selects adjusted palette;129..254 blends using
float32(auxiliary-128)/127 and native truncation. Exact original HSV helpers and
nine TRK records reconstruct9 separate, deterministic reopenable source scenes;
original TIFF/planes/palette/catalog are rechecked. The high byte is retained,
never called ordinary opacity. Optional bump/gloss/GPU effects stay WARN.
Source Garage offers separate original-color scenes; their native Create is
disabled. Accepted4Runner is unchanged. See EVO2_TIFF_COLOR_SEMANTICS.md.

RAV4 owner-confirmed loading/appearance/driving/body damage/breakable glass is
historical partial L4 evidence. Race completion/Results remain unconfirmed.
New isolated A/B/C/D copies preserve the original candidate. Wheel-onlyB changes
2419 zero-alpha RGB texels in the one indexed rim map; visible pixels/coverage,
UV, geometry and native state remain exact. Lamp-onlyC uses336 explicit lens
texels and10 source faces, retaining ordinary diffuse surfaces under masked
emission/glow; no white body lighting loss. Both intact OFF and broken-glass
surface multisets and collision/bounds suffix are exact. D combines independent
offline checks. All four launcher verify/environment/allocation checks pass.
Final explicit race D3D9 views show the wheel fringe removed inB/D and revised
bounded lamps. **Corrected D3D8 remains OWNER PENDING.** No existing project was
modified. See MICHELIN_RAV4_VISUAL_MICROFIX.md for launch paths/checklist.

Fresh7-case preflight: L0/L1 PASS, L2 WARN; generic native geometry WARN for
Evo2/RAV4/Megane/Silver; Dakar2 BLOCKED. Generic preflight L4 NOT TESTED means no
new owner run in this stage, not cancellation of historical owner evidence.
Three accepted source-baseline DX each for Evo2/RAV4/Silver and23 DXT remain
exact. Mégane is still a readiness reference, not a new native vehicle.

Validation:89 focused tests PASS; full available Windows suite1240 tests OK,
2 existing optional skips,77.518s. Seven actual hidden Tk open/worker/preflight
dialogs and Evo2 color-worker derivation/reopen pass without focus activation.
Protection:12742 files/15853855826 bytes, including307 sealed accepted RAV4
resources, zero changed/missing. Mutable owner state outside the index was not
reset. Private `.research-output/vehicles/cross-game-materials/` holds corpus,
native shader evidence, color scenes, A/B/C/D, final GPU evidence and logs.
Metadata-only CROSS_GAME_MATERIAL_PROVENANCE.json separates levels and evidence.

No original EXE/SMA/DLL/disc/install, accepted project, Randomizer, roster or
alternativeCarID29 was changed. No push/publication, new playable Dakar/Megane,
new CarID, donor, fleet, Blender Bridge, historical livery or physics tuning.
Stop here for review and owner RAV4 comparison.


### Current level interpretation (supersedes older pending-feedback wording)

| Vehicle | L0/L1 | L2 | L3 | L4 |
|---|---|---|---|---|
|Evo2 4Runner|PASS|WARN GPU/gloss|Historical accepted native, unchanged; new colors source-only|Historical owner gameplay; no new run|
|Dakar2 Pajero|PASS|WARN|BLOCKED decoded shader dependencies|NOT TESTED|
|Dakar2 Nissan|PASS rigid source basis|WARN|BLOCKED independently checked materials|NOT TESTED|
|Dakar2 Hino|PASS|WARN|BLOCKED materials; truck systems separate|NOT TESTED|
|Michelin RAV4|PASS|WARN original renderer|Existing native; B/C/D offline validated visual alternatives|Owner partial baseline PASS; corrected variants PENDING|
|Michelin Megane F2|PASS|WARN|Geometry-only WARN; model-specific native systems unqualified|NOT TESTED|
|PC Paris-Dakar Silver|PASS|WARN|Existing accepted native unchanged|Historical owner launch; stiffness separate|

No dry-run compiler result promotes a complete native vehicle or new gameplay
approval. Shader/auxiliary/lamp ownership boundaries above remain explicit.
