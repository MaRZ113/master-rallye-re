# Source versus authoring validation

| Restriction | Classification | Current treatment |
|---|---|---|
| Original scene/manifest/resource hashes | Source fidelity and input protection | Strict for the original parent; every native build re-verifies it |
| Original triangle/vertex count after intentional edits | Fidelity comparison | Intentional difference in derived projects; validate new arrays instead |
| Indices, finite values, float32 serialization, native draw limits | Native correctness | Hard failure remains |
| Source shader/secondary map equivalence | Source renderer fidelity | Strict source bridge unchanged; explicit derived materials replace it with a visible provenance warning |
| Complete original reflection group | Source-bound legacy ownership | Legacy unchanged; user face selections split into distinct complete derived material groups |
| Face/controller/material ownership after topology changes | Correctness and repair | Stable face IDs; deleted effects removed, stale selections rejected with reselect instructions |
| Independent wheel instances | Native controller relationship | Explicit instances retained; no shared-wheel runtime safety inferred |
| Existing topology_writer draw-only rebuilding | Implementation scope | Existing writer unchanged; new derived sections use the already-qualified ScenePart writer |
| Legacy GT-only Classic recipes | Legacy adapter boundary | Old paths preserved; new role-based native authoring accepts UVS independently of donor |
| Native runtime/resource integrity | Runtime safety | No relaxed asset allowlist, no roster or launcher changes |
| File-output containment | Original/accepted project protection | Hard failure remains |

Reports are separate: source-fidelity difference, structurally valid editable project, native fixture compatibility, and actual runtime qualification. A safe DX/DXT fixture does not certify collision fit, vehicle physics, wheel controllers, complete game integration or owner gameplay. Donor renderers retain their previous L2 WARN and strict material-equivalence findings.

No accepted `universal_scene_bridge`, `topology_writer`, GT Classic or runtime builder code was weakened. Migration is opt-in. Source Fidelity remains independent from MR Classic/Customized authoring.
