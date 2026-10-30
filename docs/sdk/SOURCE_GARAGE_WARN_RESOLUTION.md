# Source Garage WARN resolution and visual evidence

This is an implementation/hardening stage over baseline c557ed6, not a new format audit. The complete owner request is retained at retained/source_garage_hardening_request.md; the live request controls scope. SOURCE_GARAGE_QUALIFICATION_MATRIX.md is the issue ledger, with separate source L2, native L3 and owner L4.

## Resolved correctness defects

- Raw vertex streams now bind their own original source hash/stride/count to the manifest at save and reopen. Rebinding only the transport manifest cannot substitute UV1 bytes.
- Typed secondary UV channels and per-corner colors validate their count, finite components and byte domain before use; the v1 schema and existing serialized scenes remain valid.
- Additional UV/stages no longer silently disappear in the native bridge. Exact equal UV aliases may be represented by UV0; other omissions require an explicitly scoped native interpretation with evidence and visible WARN/impact. Complete shader support is not implied.
- External semantic contracts pin source scene, mesh, material and exact face IDs. Conflicting body/frame/glass/lamp claims fail. Reflection eligibility requires complete original material coverage.
- Shared semantic partitioning conserves exact source-face surfaces, colors, UVs and original material flags. Unknown faces remain; damage/reflection eligibility never creates duplicate geometry or new native controllers.
- Common preflight distinguishes valid geometric instances from the qualified four MR wheel-controller slots. No new wheel or roster capacity is inferred.
- Source Garage has a read-only qualification report showing levels, source unknowns and native blockers. Opening a valid scene does not silently approve native import.

Synthetic failures are preserved as tests: hostile/rebound stream manifests, missing/oversized streams, invalid colors/UVs, unevidenced/differing UV aliases, secondary texture loss, role overlap/material mismatch, out-of-range/duplicate faces, fragmentary reflection ownership and unsafe alpha over body/frame geometry. The partition test independently reconstructs the multiset of surfaces before/after; it does not just compare a selected numeric recipe with itself.

## Bounded source-format findings

Dakar2: all132 present UV1 streams are exactly UV0 aliases for these three selected members, exposed as typed data without losing originals. Counts: Pajero42, Hino47, Nissan43. Missing UV1 on other meshes is not fabricated. Three original-versus-typed D3D9 isometric captures have **identical pixels**, matching byte-identical MRPVs; this proves the metadata exposure leaves rendering alone. It does not implement secondary texture/combiners, lighting, alpha-test activation, sampler or equipment runtime rules. Native entry remains BLOCKED until a conservative material/assembly policy is actually qualified.

Evo2: fresh REA/Ghidra12.1.4 investigation of the exact4x42.exe follows005d7980→004273d0. Original nine TRK color records survive. Two original float64 constants are360 and100, not32-bit floats, used for the HSV parameter path. File mappings and three instruction samples are independently checked against original PE bytes. The color consumer reads two separate planes and has mixed recolor/high-byte behavior around00427c76/00428112. This narrows the investigation but **does not yet prove the TIFF second sample's complete association with those buffers or original renderer alpha**. Some indirect TIFF methods were not function-defined by this Ghidra analysis; no repeated speculative decompilation or implementation guess was used to bypass that gap. Private exports are in scratch/source-garage-hardening/evo2-evidence.json and evo2-snapshot.json, with original instruction hashes in the research output. Original palette and both sample planes remain immutable. Their second-plane distribution is88492 pixels0..128,7239 pixels129..254,166413 pixels255; a nontrivial distribution is not proof of alpha.

Michelin: use the preceding v7.7 evidence and exact native recipe; do not restart the importer. Current source inspection scenes remain immutable, including explicit neutral identity wheel pose/opaque windows and their WARNs. The separate MR-rest experiment/native RAV4 already supplies proper outward wheel facing and bounded panes. Mégane remains a neutral scene plus fixture/readiness plan, never an automatically promoted native vehicle. Original BIN damage targets and four body LODs remain separate.

## Visual and native regression

Private `.research-output/vehicles/source-garage-hardening/corpus-final/` contains six fixed orthographic source views, wheel/window close-ups and material-ID diagnostics for all seven cases. All seven sheets were inspected. Michelin original left-side dark wheel backings remain a known identity-pose source limitation; these images are deliberately not presented as the corrected MR-native pose. Dakar2 Hino's bright/grey material differences, wheel interiors, lighting and glass remain L2 WARN. No global no-cull, all-polygon reversal, black backing cap, reflection overlay or extra spare was added. Per-draw Dakar2 source culling/depth/pass inference remains unchanged. Consistent native RAV4/derived Michelin rest-pose comparisons remain available in michelin-native/fidelity from the exact preserved previous milestone.

Fresh native geometry fixtures are private, without CarID/physics/controllers/runtime assembly. Three DX resources per previously qualified Evo2/RAV4/Silver reference reproduce their accepted source-baseline bytes exactly. All23 emitted DXT resources (3/14/6) are also exact. The Mégane fixture is an explicitly labelled geometry experiment only. Position/normal/UV/winding checks and duplicate compilation are common across these sources, not Toyota-specific polygon corrections. No Dakar2 native fixture is generated by ignoring its blockers.

The actual Tk window/worker/report flow reopens all seven originals with zero callback errors. It runs hidden, with no foreground activation over the owner's running game; therefore no new GUI screenshot is claimed. D3D9 GPU images are actual separate captures. Original-game runtime fidelity and D3D8 driving are not asserted.

Full regression, protected-file counts and committed metadata are recorded in REGRESSION_MATRIX.md / SOURCE_GARAGE_CORPUS_PROVENANCE.json. Existing Studio Undo/Redo/Restore and native damage tests remain in the suite; this read-only audit makes no edits requiring new owner-project history. Source restoration is reopening the original; every derived typed-UV project is separate. Original RAV4 native resources and sealed candidate are protection inputs while the owner tests; mutable owner saves/options are not reset.


## Cross-game material fidelity checkpoint — v8.0, 30 October 2026

Resolved: required original shader behavior cannot be waived through blanket stage omission; Evo2 TIFF plane routing and original pre-gloss nine-color arithmetic are reproducible in code; RAV4 transparent-rim RGB fringe and incomplete UV/face lamp ownership have isolated fixes. D3D9 reproduces/removes thefringe, and exact lenscoverage/masked native states retain bodylighting. Source/defaultaccepted projects remain unchanged.

Still bounded: Dakar2 coordinate generation/V0/effectiveconstant/conditionalcoverage keep all3 materials L3 BLOCKED; original Evo2 bump/gloss/GPU highbyte remainsWARN; original Michelin L2WARN; corrected RAV4 D3D8 remainsownerpending. Historical owner RAV4 loading/driving/bodydamage/glass confirmation is retained, without inventing fullrace/Results. Evidence/code/tests and finalcaptures are in DAKAR2_NATIVE_MATERIAL_QUALIFICATION.md, EVO2_TIFF_COLOR_SEMANTICS.md, MICHELIN_RAV4_VISUAL_MICROFIX.md and CROSS_GAME_MATERIAL_PROVENANCE.json.89focused/1240Windows tests OK (2skips),12742protectedfiles unchanged.
