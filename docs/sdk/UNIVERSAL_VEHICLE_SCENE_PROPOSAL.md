# Universal Vehicle Scene — interface proposal

28 October 2026. **PROPOSAL / NOT IMPLEMENTED.** Source Garage research,
`research/vehicles`, inspected baseline `b9a24f7` (implementation `138df440`).
This document defines an exchange boundary for future source adapters. It does
not add an importer, change current GT/Heritage routing or authorize a new
vehicle build. First cross-game adapter implementation waits for audit review.

## Existing implementation and evidence

The repository already has a useful conservative intermediate layer, but not a
universal contract. These are source-code observations:

| Existing component | Observed contract / reusable boundary |
|---|---|
| `addon_sdk/gt3_scene.py:reconstruct` | GT3 ModelSet1 draws retain shape/packet/command identity, vertices, triangles, material, texture binding, GS state, unresolved transforms and issues. External face images require complete finite source UVs; the implicit VIF mask is qualified against an exact CORE hash. |
| `addon_sdk/gt4_scene.py:reconstruct` | Separate GT4 ModelSet2 command interpreter, complete stored-shape accounting, selected model/LOD/callback path, original materials/textures, morph targets and explicit unknowns. A selected unresolved command path is rejected. |
| `addon_sdk/gt4_assembly.py:assemble` | Hash-pinned body/menu components and spec rig; separate wheel/rim/tyre instances and relative hubs. Source supplemental geometry remains separate when its purpose is unresolved. Zero-steer/spin static pose and menu/race reuse are reported. |
| `addon_sdk/gt3_assembly.py` and `gt_auto_profile.py` | MR compatibility fitting and automatic arch-derived profiles are authoring approximations, separate from source decoding. GT3 stock-tyre topology and donor hubs do not become recovered GT rig facts. |
| `source_scene_compile.py:compile_draws` | Shared GT geometry/GS-state translation to MR packets/materials. Explicit reports preserve omitted/unsupported effects; non-strict skip is reported. Its PS2-specific state and `rotate` convention must not become universal defaults for other games. |
| `scene_dx_writer.py:ScenePart`, `write_scene_dx`, `validate_scene_dx` | Qualified MR tag2/three-texture-slot grammar over `DrawGeometry`; donor collision is retained and bounds recomputed. This is an MR output contract, too lossy to represent original source semantics. |
| `addon_sdk/import_project.py:prepare` | Existing shared author project bridge, texture collision rejection, UI rendering callback and scene/native-state validation; no runtime allocation. |
| `addon_sdk/heritage_source.py` | Native-MR fast path: original snapshots, compatible native resources, exact file-set/hash pins, per-conversion reports and existing author project. Original native material/controller information must not be flattened through a GT-only representation. |
| `gt_source_project.py:GTSourceProject` | Immutable source/profile/color-table/identity pins; each original colorway has an independent editable project and manual history. Source selection has separate Undo/Redo/Restore. |
| `classic_pipeline.py:convert` | Opt-in v2 semantic operations with source/stock hashes and qualified draw-role evidence. Current accepted `source_format` values are only GT3 ModelSet1 and GT4 ModelSet2. A proposed new scene format is not already supported. |

Paths above are under `src/master_rallye/`. GT3 and GT4 must retain their separate
readers; shared VIF/GS code does not prove identical format or runtime semantics.
The current 572 structural GT3 members and 257/287 derived automatic profiles
are different denominators, neither counting gameplay-qualified vehicles.
The Clio candidates remain gameplay-pending. Later Master Plan entries and
CAPABILITIES record full owner Heritage Trooper acceptance; the earlier
`HERITAGE_GARAGE_RESULTS.md` opening pending label is historical and stale.

## Layer boundaries

Proposed sequence:

1. Read-only source inventory resolves a configurable root alias, edition and
   exact source files/members. Missing edition data stays unknown.
2. A source adapter decodes into `universal-vehicle-scene/1`, plus an inspection
   report. It can produce a partial scene without granting build eligibility.
3. A separate qualification/profile layer selects variant/LOD/rest pose, proves
   material roles and records any explicit approximation or author decision.
4. One shared MR authoring bridge translates only qualified semantics, then
   uses existing DX/DXT writers, native controller tooling and project services.
5. Existing Workshop systems apply reversible appearance/mechanical/frontend
   overlays and build an isolated roster. Gameplay is a separate test level.

Inspection must work without a retail MR donor. Source adapter output must not
contain CarID allocation, donor physics, MR texture replacement or installation
side effects. No adapter gets its own complete Master Rallye compiler.

## Proposed data contract

The name and fields below describe an interface, not an implemented schema.
Strings used as IDs are stable within a source-hash/adapter-version domain.
Large arrays and decoded images may be content-addressed private sidecars;
JSON metadata retains their digest, encoding, shape and byte limit. No embedded
game assets belong in a source-only report/archive.

| Field | Required meaning |
|---|---|
| `schema`, `scene_id`, `adapter` | `universal-vehicle-scene/1`; adapter ID/version and implementation digest; deterministic scene identity. Unsupported major versions reject. |
| `source` | Exact title/platform; known edition/region/build and evidence; executable hash when available; root alias and relative path/member chain; original stored/decoded sizes and SHA256. Claiming an edition from a directory label is prohibited. |
| `catalog_identity` | Original database/vehicle IDs, raw labels, resolved display labels, exact association evidence. Separate suspected identity from confirmed record joins and author-supplied naming. |
| `coordinate_system` | Source handedness, up/forward axes, units or explicit unknown values; basis evidence; optional named normalized basis with invertible matrix and determinant. Unit guesses are never silently meters. |
| `nodes` | ID, original node/parent name/ID, local matrix, referenced meshes, source span and evidence. Keep original hierarchy, instances and shared mesh references. Unresolved parent/transform is explicit. |
| `meshes` | Source topology/primitive metadata, positions, normals/tangents if present, original vertex colors with their numerical encoding, UV channels, indices and primitive/material assignments. Decoded/derived triangle/vertex IDs map back to original spans. |
| `materials` | Raw source material/state references and interpreted fields: diffuse/specular/environment, blend/test/compare/ref, depth write/test, culling, draw order, multipass relationship, sampler/texture/UV association and unresolved fields. Preserve source numeric ranges. |
| `textures` | Original image/palette/mip/variant IDs, source member spans/digests, codec, dimensions, alpha channel values/encoding, decoded RGBA digest, sampler and addressing semantics. Missing/unsupported images remain records. |
| `wheels` | Wheel-node and mesh instances, source hub/local transform if recovered, axle/side only when evidenced; rim/tyre/brake/spare roles; steering/spin axes and source pose. Each fact declares whether recovered, inferred, author supplied or unresolved. |
| `surfaces` | Primitive selectors plus qualified roles: paint, trim, decal, glass, tyre, rim, lamp, brake, crew, collision, shadow, environment or unknown. Evidence references and status accompany each classification. Mixed-role surfaces can have triangle/UV-mask partitions. |
| `states` | Source glass/damage/light/brake visibility states, predicates, variant dependencies, morph targets and rest-pose selection. Source animation/runtime functions can remain opaque source extensions. MR controller names are assigned later. |
| `lods`, `variants`, `colorways` | Separate source LOD and model variants from color/material/palette choices; original selection predicates and exact catalog/table associations. Track discovered, decoded and selected members separately. Synthetic custom paint is a distinct authoring operation. |
| `unsupported_semantics` | Stable issue code, affected source selectors, raw-state/span reference, reason, impact, blocked operations and optional explicitly chosen preview fallback. Unknowns must survive every bridge/report. |
| `evidence`, `qualification` | Claims reference source bytes/format documentation/tool tests, diagnostics or actual render/runtime observations. Per-component and per-level status, scope/denominator and evidence paths/digests; no single universal compatibility score. |
| `limits`, `content_manifest` | Actual consumed budgets and bounded sidecars; every derived output digest and relationship to its original source. Original bytes remain immutable. |

A source selector should carry at least `(source_file_sha256, member_chain,
node/shape_id, primitive/packet_id, original_offset_or_record_id)`. Where exact
byte spans do not exist, retain the best exact original record identity and say
so. Changes such as triangulation, seam splitting, Clamp subdivision, normal
generation or mesh merging need a mapping/operation record; do not overwrite
the original geometry's identity with the derived one.

Evidence origin and result status are independent. Recommended origin values:
`source_bytes`, `documented_format`, `tool_observation`, `static_inference`,
`author_decision`, `preview_observation`, `runtime_observation`. Result vocabulary
is `PASS`, `WARN`, `FAIL`, `UNSUPPORTED`, `NOT TESTED`, `MISSING INPUT`.
Unknown semantic values use explicit `null` plus an issue/evidence reference;
zero, identity matrices, opaque alpha and empty lists must not masquerade as
unknown data.

## Conservative validation and qualification

- Input/member/decoded-byte, texture-pixel, node/depth, vertex/index/primitive,
  material and output limits are explicit and checked before allocation.
  Enforce aggregate budgets and cycle/duplicate-reference checks. Existing GT3
  gzip 16 MiB and other format-specific limits remain in their own readers;
  the proposal does not relax them or impose them on unrelated formats.
- Source-root aliases reference stable external paths without duplicating large
  installs. Resolve source-relative members safely, reject escaping paths and
  unapproved links, prohibit output inside source roots and verify pins before
  reusing cached decode results. Never execute donor game executables.
- Require finite numeric values and valid index/material/texture references.
  Missing UVs remain missing. A decoder can retain partial geometry for L1
  inspection while recording missing material/UV dependencies; textured MR
  authoring requires a separate qualification check.
- Preserve complete source and normalized coordinate transforms separately.
  Reflection changes winding and tangent handedness; normals use the proper
  inverse transpose. A matrix or source unit that is unresolved blocks automatic
  fitting. MR body fit is an explicit downstream derived operation.
- Preserve source order, multipasses and masks. Environment/alpha-only effects
  are not duplicated opaque body geometry. A texture's stored alpha alone does
  not establish a surface's opacity, glass identity or native controller role.
- Missing wheel rigs remain `UNSUPPORTED`/`NOT TESTED` at that component.
  Donor hub positions, stock tyres, inferred arches and presentation assembly
  are recorded authoring policies; none substitute for source transforms.
- No unknown role authorizes decal deletion, opaque conversion, wheel removal,
  decimation or damage/light controller generation. Opt-in approximations retain
  original selectors, hashes, policy and generated diff/restore path.
- LOD0 selection may be a later explicit MR policy; it does not erase original
  lower LOD discovery/accounting. Colorway changes cannot merge unrelated manual
  edits or recolor unknown atlas regions.
- L0 inventories source/containers; L1 records complete or partial structural
  reconstruction; L2 requires rendered preview plus stated visual inspection
  coverage/limitations. A captured screenshot alone supplies no parity claim.
  Gameplay remains independent and cannot inherit PASS from package preflight.

## Existing MR systems to reuse after review

`source_scene_compile.py` can inform a future neutral material translation
boundary; it currently consumes GT GS state and is not callable as a universal
decoder. Add a neutral-to-MR mapping only for demonstrated first-pilot semantics,
then reuse `ScenePart` / `DrawGeometry`, the qualified scene writer and
`addon_sdk/import_project.py`. Preserve native Heritage passthrough and its
`heritage-import.json` pins; do not recompile accepted native DX unnecessarily.

Reuse `addon_sdk/native_states.py` and native brake/glass authoring only after
source surface/triangle ownership is independently qualified. The existing
`scene_candidate`, `native_brake_scene_candidate` and
`native_state_scene_candidate` validation paths are distinct; do not weaken
`VehicleProject` validation to admit unsupported source states.

Reuse `classic_pipeline.py`, `classic_materials.py`, `classic_wheels.py` and
`classic_geometry.py` for separately qualified recipes. Extending Classic's
current format allowlist requires a reviewed change and preserved v1 Lancer
oracle, source/stock hash checks, exact-report approval and independent Source
Fidelity baseline. The Universal Vehicle Scene itself grants no Classic approval.

Keep donor physics in `addon_sdk/physics_profile.py`, cameras in
`addon_sdk/camera_profile.py`, audio in `addon_sdk/audio_profile.py` /
`audio_response.py`, shadows in `addon_sdk/vehicle_shadow.py`, frontend/UI in
`addon_sdk/ui_assets.py`, and project validation/build in `addon_sdk/project.py`.
Existing Workshop modules retain Paint/Crew, reversible history, camera,
presentation, audio and source-version UI ownership. Source wheel geometry or
published dimensions do not automatically override physics or suspension.

## Later pilot acceptance and regression handoff

After audit review, a bounded first adapter should prove one exact local vehicle
and format: repeatable source hashes; mesh/material/UV correspondence; wheel
provenance or explicit missing rig; at least one real texture decode; coordinate
evidence; partial/unsupported semantics; and deterministic intermediate output.
Synthetic tests should cover malformed offsets/counts, archive traversal,
decompression/aggregate budgets, missing UVs/alpha, unknown transforms,
material references, variant identity and source-write prevention. Real private
source smoke tests must record exact input/tool versions separately from those
fixtures. No proprietary fixture is committed.

Relevant existing regression oracles include `test_vmesh_gt3_to_dx.py`,
`test_gt4_source.py`, `test_gt4_reconstruction.py`, `test_gt4_material_pipeline.py`,
`test_garage_auto_sync.py`, `test_gt_garage.py`, `test_heritage_source.py` and
`test_classic_pipeline.py` under `tests/synthetic/`. The current ledger reports
967 complete Windows synthetic/CPU tests with two existing optional fixture
skips; this proposal has not rerun or upgraded those historical results.

Preserve private `.research-output/vehicles/heritage/`, `fidelity/`,
`gt-garage/` and their source author projects/candidates and recorded manifests.
Heritage `offline-acceptance.json` identifies its delivered project; do not guess
the active author path from an old candidate name. The current Clio alternatives
are `gt-garage/t/s2/candidate` and `gt-garage/t/c2/candidate`. Keep accepted
Subaru27 and Lancer28 resources and separate Pajero29/HeritageTrooper29/Clio29
rosters. The known qualified limit is 30 entries, not simultaneous competing29s.

Review archives follow repository ledger convention: clean source/docs/tests
from committed Git blobs, separate changed-files ZIP, metadata/entry hashes and
archive SHA256 under ignored research evidence. Exclude models, textures, audio,
native dumps, screenshots, installed/candidate runtimes and external games.
`.research-output/` and root `scratch/` are already ignored. Original
`MRallye.exe`, retail `Data.sma`, installed `d3d8.dll`, accepted resources and
unrelated Randomizer work remain outside this proposal's writes.
