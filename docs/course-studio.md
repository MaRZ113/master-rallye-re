# Blender Course Studio (COURSE-VIS1)

Course Studio extends **master_rallye_io**, not a second add-on. The SDK parsers,
race-logic authoring transaction, material preview and COURSE-CAP2 builder remain
the implementation base. `src/master_rallye/course_studio.py` has no `bpy`
dependency. The Blender adapter owns presentation and translates source XYZ to
Blender `(X, -Z, Y)` at scale 1, using the existing coordinate helpers.

## Open and edit

1. Install the ZIP using Blender's Install from Disk, enable Master Rallye IO,
   then open the 3D View sidebar: **Master Rallye > Course Studio**.
2. Choose **Open Course Project**. Select a RaceTest XML, course DX, unpacked
   course folder, `course-studio.json`, or `mr-course-registry/1` catalog. For a
   catalog, specify its resource root and an explicit Race ID. The resource
   root is the directory containing `DataGx` and `DataScene`.
3. The source `CourseProject` binds the landscape from the exact XML model path,
   the sibling HNT, the exact AI dataset, and available TXT/GXM sidecars. A
   registry with multiple registrations requires a selection; missing and
   ambiguous dependencies produce errors. No fuzzy filename choice is made by
   the Studio resolver. The existing material sidecar scoring remains visible
   as material-candidate provenance, not an invented physics binding.
4. Use the semantic collections: Visual Terrain, Static Objects, Collision,
   Start & Finish, Checkpoints, RaceLine, Limits, AI, Diagnostics. Layer toggles
   control the actual collection containing the corresponding helpers.
5. Edit terrain vertex positions in Edit Mode. Return to Object Mode for
   validation. The writer preserves triangle order, draw/group attributes,
   UVs, materials, normals, spatial bounds and all trailing collision bytes.
   It refuses changes to topology, UVs or assignments, and refuses modifiers.
   A position edit therefore needs an explicit visual/physics acceptance check;
   it does not rebuild collision or automatically recalculate native bounds.
6. Move existing area markers and RaceLine/Limit helpers. Curves follow the
   existing route handler. Split center, Radius and Split Time ID are exposed
   in the panel. The trigger uses the native sphere center, not the centroid
   of its visual companions. ExtraTime remains uninterpreted.

### Marker Builder

All commands operate on an embedded working XML transaction. Source XML remains
unchanged. Working XML and the operation audit survive saving the `.blend`.

| Command | Native changes |
|---|---|
| Create Start Area / Create Finish Area | Place the four existing `Marker Pos` fields around the 3D cursor, using the requested width/depth. If absent, clone the opposite supported four-marker list. Existing direction fields remain unchanged. |
| Add SplitTime / Create Checkpoint | Append a native SplitTime Egg and its existing 0..3 visual companion templates, assign a fresh ID/name, translate their real centers, and set Radius. Template ExtraTime and unknown template fields survive. |
| Delete Selected SplitTime | Remove the selected native trigger Egg and its exact 0..3 companions. Unknown content inside those intentionally removed Eggs is removed with them; all other records survive. |
| Reorder Markers | Assign contiguous Split Time IDs in the existing XML source order. Egg names, source-order identity and unknown components remain unchanged. |
| Validate Route | Run the same complete Course validation, including bounded writer diagnostics. |

These inventory operations have **offline preservation/binding validation**.
New marker inventories still need owner gameplay acceptance. The existing
runtime-confirmed field edits and these new template operations have different
evidence levels. Marker Dir/camera semantics are not upgraded by the UI.
Studio refuses helper transforms that the bounded exporter would otherwise
ignore, rather than silently dropping an apparent direction/scale edit.

## Materials and surfaces

The existing DXT/PNG implementation and material preview are reused. Select a
native material to export upright PNG or stage a same-dimension PNG replacement.
The original 20-byte FEED header, UVs and material binding survive. Drafts are
written to a sibling `<output>-texture-drafts` directory; validation incorporates
them into the final resource transaction. Shared textures outside the isolated
course folder cannot be changed for a new registration without a qualified
binding remap. Source SHA is provenance and template integrity, not a texture
artwork whitelist.

Literal `$surfacetype(...)` and `$grnd(...)` tokens are linked to source material
candidates and shown on selected materials. Multiple candidates remain multiple
candidates. **Changing physical surface behavior is INSPECT_ONLY**: a material
name or visual shader does not prove the cooked physics mapping.

Atmosphere 6.17 does not require a manually copied per-Race-ID lighting profile.
Studio does not write Renderer profiles, hooks or global material catalogs.
Original bindings are retained; new shader/material families require independent
Renderer qualification. Blender material appearance is a preview, not parity.

## Collision Studio

The reader exposes real tag100 node indices, source offsets, parent/back/front
links, raw leaf fields, plane float4 and source code values. Navigation buttons
follow those native links. A selected plane is drawn as a **25-unit inspection
glyph**, not a bounded collision face or recovered triangle.

`Probe Actual BSP at 3D Cursor` partitions the vertical ray into exact native
solid/empty leaf intervals using the existing BSP branch and leaf contract.
Solid intervals are drawn as lines. `Check Marker / BSP Clearance` probes the
area/split anchors within +/-50 source units and warns when no upward
solid-to-empty boundary lies within 10 units. These are geometric sample
diagnostics, not a proof of collision completeness, seam closure, intersection
freedom or vehicle physics. Warnings identify their object in the Text report.

France1 contains 351,793 nodes and additional bytes following its parsed tag100
tree. Those bytes are kept intact and explicitly UNKNOWN. The existing BSP
writer is deliberately not enabled as a Studio terrain rebuild: a qualified
render/source-triangle mapping, subsequent collision structures, seam policy,
surface properties and gameplay checks are still needed. Visual terrain is
never relabeled as real collision.

## PS2 dressing, physical objects and triggers

Optional assets are selected explicitly; Course SDK and ordinary course export
work without a D3D8 proxy. No renderer code is imported or modified.

| Source | Representation | Editing/export |
|---|---|---|
| PS2RGD02 `.ps2rgd` | Real model triangles/UVs/textures, authored matrices, mass/MOI/trigger fields, exact convex hull points and plane-based hull faces | INSPECT_ONLY |
| PS2SPL01 `.ps2spl` | Source control polygon, model identity, loop/trigger/rest/speed/banking/config fields | INSPECT_ONLY; control polygon is not a baked Catmull-Rom animation |
| PS2BRD01 `.ps2bird` | Bird flight/spawn anchors, min/max flight/milling distances, randomization and list-presence gates | INSPECT_ONLY; no fabricated active flock or milling points |
| PS2GRS01 `.ps2grass` | All original mini-grass/shrub placement points, source bins and PSM/texture/PC provenance | INSPECT_ONLY; short vertical editor ticks mark source placements, not inferred billboard dimensions |
| RaceTest sound Eggs/components | Source sound anchor glyphs, original matrices/components and typed values | INSPECT_ONLY; icon size is not an inferred audible/trigger radius |
| Other native Eggs | Hidden diagnostic axes with source XML path, model name, matrices and component tags | INSPECT_ONLY |

Spline/bird/rigid assets bind to the exact course DX path, not an approximate
course name. Grass assets expose their source PC DX digest; mismatches remain
visible in feature metadata rather than being silently called a match. These
source digests are independent of the pixel-content replacement policy.

The current proxy validates its own prepared artifacts and selectors. Adding
or moving props/dressing in a new custom course requires an agreed writable
asset/selector contract with that proxy. Studio does not bypass those guards or
silently install altered assets. This is a specific COURSE-VIS2 integration gate.

## Routes and player freedom

Existing RaceLine and four Limit lists support the established position-only
writer. Source marker count, order and identity remain intact. AI proposals can
be created as independent editable curves and saved in
`mr-course-neutral-routes/1` (`editor-routes.json`). A separate PLAYER_REGION
role can describe player freedom. These proposal curves are editor-only and
do not claim native alternative-AI selection. Player movement is not constrained
to a proposed narrow AI line. SFL bytes and unknown field semantics survive.

## Validate > Stage > Export

Validation returns `ERROR`, `WARNING`, `UNKNOWN`, source/object path and a concrete
message. The Blender Text block `MR Course Validation` retains the report. Errors
block export. Warnings and unknowns remain in the output manifest; parse success
never becomes a claim that the Course is ready to play.

Export requires a **fresh directory outside the input resource tree**. It
checks source integrity, prepares a temporary tree, reopens it through the same
CourseProject loader, validates it and atomically publishes the directory.
No Retail/Pristine resources or saves are overwritten. Unknown course-side files
and HNT dependencies are copied. Resource bytes and checksums are deterministic;
absolute provenance/output paths naturally differ between destination trees.

The staged package contains:

- `course-studio.json`: explicit portable resource bindings, hashes, support,
  provenance, marker-operation audit and outstanding findings;
- `resource-root/`: complete bound dependencies and independent course bytes;
- `resource-overrides.json`: inputs for the accepted CAP2 composition mechanism;
- `courses.json`, when registering a new race: extended existing registry schema;
- `editor-routes.json`, when proposal paths exist: neutral, editor-only routes.

For an independent race, choose the **current accepted** CAP2 catalog, explicit
template Race ID and new portable name. Studio copies the course model/sidecars
into a new Course folder and creates a distinct Course key, RaceTest, HNT, AI
dataset and progress/menu entry. Original registrations and original model bytes
remain unchanged. The existing `tools/build_course_registry.py` performs native
composition; Studio does not introduce a second EXE patch mechanism.

CLI equivalent:

```powershell
python tools/course_studio.py <RaceTest.xml> --output <fresh-output> `
  --catalog <current-courses.json> --template-race-id <id> --name <NewName> `
  --compose-template <accepted-compose.json>
```

The generated `compose.json` can be passed to the existing CAP2 builder, which
requires its own fresh private worktree output. Old CAP2 catalogs lacking current
menu/screenshot bindings must be updated from the accepted catalog, not guessed.

Reopening a Studio project restores its linked catalog, stable registration ID
and neutral proposal curves. Exporting it again without a new name preserves
that registration. A source registration sharing a stock Course instead needs
a new name to create isolated model resources. Native local HNT texture paths
are redirected to the copied folder, keeping native texture slot names intact.

## Qualification and next gates

Synthetic tests cover byte-preserving XML templates, marker identities, exact
BSP ray partitions in both directions, source changes, invalid paths/topology,
atomic staging/reopen, textures and independent registry resources. Blender's
headless integration exercises real France1, material previews, field edits,
template add/delete/reorder, routes/limits, PS2 assets, neutral route export,
save/reload and register/unregister/close. Build reports carry source hashes.

The private candidate is **OFFLINE_VALIDATED / RUNTIME_NOT_TESTED** until the
owner completes gameplay acceptance. A suspended CAP2 preflight is a separate
gate and must report `game_thread_resumed=false`; it is not gameplay evidence.

COURSE-VIS2 gates are bounded: collision rebuild and post-BSP structures;
new cooked geometry/topology and native budgets; writable physical surface/water
properties; proxy asset additions/selectors; native SFL generation and alternative
route selection. Existing GXM/TXT source writers remain available separately but
are not automatically promoted to a qualified native terrain/BSP cooker.
