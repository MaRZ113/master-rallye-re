# Universal native bridge qualification

Implemented path remains adapter→immutable UVS v1→explicit MR profile→shared compiler/scene writer→existing native SDK. This stage adds shared validation and provenance operations, not an Evo2/Dakar2/Michelin-specific compiler. Old accepted resources remain unchanged; no existing project migration is required.

## Contracts and checks

`universal_vehicle_scene.py` optionally accepts mesh `uv_channels` with keys1..3, each containing `values` (float2 per vertex) and nonempty `evidence`. `uvs` remains UV0. Raw `source.streams` entries require path/SHA256/stride and exactly vertex_count×stride bytes. All claims bind independently of the transport manifest. Corner BGRA must have one four-byte tuple per vertex. Existing sidecars, source transforms, snapshots, damage targets and unknowns remain unchanged. Neither UV1 nor unspecified TIFF samples are automatically assigned material meanings.

`scene_semantics.py` supports an external `universal-vehicle-semantics/1` document: exact `source_scene_sha256` and `claims` with mesh_id, material_id, triangles (`all` or explicit IDs), role, interpretation (`source_qualified` or `mr_authoring`) and evidence. Roles include opaque_body, glass, frame, lamp_off/on, reflective_paint, mirror_body/inset, tyre, rim, wheel_interior, equipment, damage_eligible and cabin_crew. Unknown is valid. Source mesh names or grey pixels do not automatically classify glass. Damage eligibility is not an invented native zone.

Primary face ownership must be disjoint. Damage/reflection eligibility can annotate an existing primary role; they cannot emit duplicate overlays. A reflection claim must cover all original faces of every mesh sharing that original material. `native_roles` rejects whole-material alpha blending when body/frame/unqualified faces would become transparent. `partition` produces ordinary SceneParts plus source-face/node/material/claim bindings for existing native services, preserving material flags/positions/normals/UV/colors. It does not silently assign alpha, glass breakage, lamps, physics or CarIDs. A checked private RAV4 contract demonstrates exact34 glass faces and12 original rear lamp faces without changing its accepted native project.

Profiles optionally carry `semantics` and `source_feature_policy`. Extra UV and secondary texture bindings require an exact feature key, disposition, evidence and impact. `alias_uv0` passes only when the typed values are identical or bound original UV0/UV1 streams have identical SHA/stride8. It says nothing about shader operations. `omit_for_mr` is a deliberate approximation and always WARN. A missing/unknown approval is rejected. Existing legacy diffuse-only bump behavior stays compatible and visibly WARN; new semantic contracts require an explicit bump disposition. This narrow compatibility boundary is documented rather than retroactively invalidating accepted vehicles.

`source_qualification.preflight` loads/validates a scene read-only, inventories source features/unknowns and optionally invokes the shared compiler twice. It checks inverse source positions/UVs, transpose-normal roundtrip, determinant winding and native hashes. Native MR four-wheel authoring uses explicit FL/FR/RL/RR slots; more/different geometric wheel instances remain a valid UVS but cannot silently become supported controllers. Render dry-run success does not validate physics radius, suspension, collision hull, native wheel spin/steer, sound, frontend, damage events, roster or owner gameplay. Those stay in existing per-candidate SDK validation.

## Reproduce

Use fresh ignored outputs outside source roots/accepted scenes. No original installation is duplicated.

```powershell
python tools/source_garage_preflight.py --scene <private-scene.json> --profile <explicit-MR-profile.json> --semantics <optional-ownership.json> --output .research-output/vehicles/source-garage-hardening/new-preflight
python tools/qualify_source_garage.py --output .research-output/vehicles/source-garage-hardening/new-corpus --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe
python tools/validate_source_qualification_windows.py --output .research-output/vehicles/source-garage-hardening/new-ui --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe
```

The corpus tool selects seven already accepted exact source scenes and existing profiles. It regenerates offline geometry fixtures only where a profile exists, compares accepted native reference bytes, and leaves Dakar2 BLOCKED. It exposes UV1 into separate reopenable projects with independent deterministic manifests and unchanged source MRPVs. It does not prepare registry entries, native physics, game launchers or new owner candidates. The CLI accepts explicit profiles for experiments but never calls such an omission source fidelity or gameplay qualification.

Protection uses `tools/verify_source_garage_preservation.py` with the historical expected-hash manifest, accepted scene roots and the preceding RAV4 sealed resource-index SHA. Reports are fresh/disjoint. Existing source and runtime assets are read-only; mutable owner runtime state is outside the sealed index and is not restored or overwritten. Source-only ZIPs package committed text, never private fixture DX/DXT/pixels/audio/executable payloads.

## Next owner-tested vehicle

Finish the already delivered RAV4 owner checklist first. Incorporate actual steering/travel/glass/brake/Results findings through its reversible native project. Then Mégane F2 is the next bounded import: original geometry/UVs/tyre selection and generic compiler are ready, but its own67-face window candidate set, rear lamps, native controller/collision/physics policy still need qualification. Do not rename it Maxi without evidence. Dakar2 is not the next native choice while shader/material and native assembly policy remain BLOCKED. No fleet, new donor, Blender Bridge or roster expansion follows automatically.


## Cross-game material fidelity checkpoint — v8.0, 30 October 2026

The v1 contracts remain backward compatible. Source shader declarations/hashes produce a required `source_shader` feature; `omit_for_mr` cannot waive it. A UV alias or an inactive fourth stage is not proof that active additive stages are redundant. Dakar2 typed decoder/evaluator records original inputs, constant mappings, active modes, per-drawbindings and exact blockers. No new compiler or silent diffuse fallback.

Opt-in per-material `transparent_edge_padding={radius,evidence}` accepts1..32 and unchanged binary source coverage, preserving all nonzero-alpha pixels. Default profiles are unchanged. Common native-state authoring optionally uses explicit `masked_overlay`, retaining the diffuse surface in both brake cases plus masked emission/glow inON. Source-specific lens contracts bind scene/atlas hashes, sourcefaces and concave UV contours; they cannot classify arbitrary red paint or migrate Toyota faceIDs toRenault. Intact/off surface conservation and collision are verified by the writer; enclosing derivation separately verifies alpha masks. These overlays are explicit native render passes, not new source geometry.

Capture helpers can explicitly select race/frontend/wheel. Native brake tests must selectrace, since the default frontend has no race switch. Final affected RAV4 images were regenerated.89focused/1240full Windows tests pass (2optional skips); accepted sourcebaselines remain exact. Shader parity, nativephysics and ownergameplay levels remain separate. See the three engine reports and CROSS_GAME_MATERIAL_PROVENANCE.json.
