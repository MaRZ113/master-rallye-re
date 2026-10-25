# Addon manifest v1

The normative machine-readable contract is
[`schema/addon-manifest-v1.schema.json`](schema/addon-manifest-v1.schema.json).
The compiler also performs semantic checks that JSON Schema alone cannot:
target-build capacity, cross-addon collisions, explicit/automatic ID conflicts,
known AI-pool boundaries, and class-local placement.

Each JSON manifest has `manifest_version: 1`, stable `addon_id`, provenance
`description`, `vehicle_class`, and an ID policy (`explicit` or `auto`). V1
only appends vehicles to the native class list. `identity` keeps runtime,
model, wheel, and physics names independent. Model assets use a unique
`DataGx/Vehicles/<model_family>` root; physics identity uses a
`Vehicles/<family>` path.

Each runtime/model/wheel family token is 1–64 ASCII characters, begins with a
letter, and contains only letters, digits, or underscores. This bound is
validated before native strings or resource paths are generated.

`frontend` separates manufacturer, model and combined names from stats,
Vehicle Select art frame and SmallCarSheet frame. `race_colour_rgba` is an
independent normalized four-component color; it is not inferred from body
textures. `unlock` supports only always-available or a mirror of a stock
unlock predicate. `audio` supports a tuned retail `stock_profile` ID 0..24.
`ai_eligibility` names native mode-generation boundaries; it is independent of
player unlock. Challenge remains authored, and Invitation requires an explicit
ordinary-T3 decision. `results` has a fixed display-only name, independent of
native DriverID selection.

UI art defaults to `stock_frame`. Optional `project_frame` appends a hash-pinned
user image through the author project's `ui-assets.json`; see
[UI assets](ui-assets.md) for the admitted bank profiles, custom RGBA8 PNGs and
the optional local GT3 extraction adapter. The SDK does not bundle or require
GT3 assets.

The current target capability profile reserves physical IDs 0..25 and permits
only addon IDs 26 and 27. That is a verified target profile, not a generic SDK
limit. The resolver reads the profile instead of hardcoding 28. A later target
profile may declare additional capabilities only after separate qualification.
Unknown or unqualified IDs fail validation under the current profile.

Examples: [Mercedes ML-320](examples/mercedes-ml320.json),
[R5VQualifier T2](examples/r5v-qualifier-t2.json), and the metadata-only
[Glacier Sprint T2 author example](examples/glacier-sprint-t2.json). Glacier
Sprint demonstrates a different family and frontend name; its ID27 resolution
is a synthetic plan, not a runtime-qualified vehicle. R5VQualifier explicitly
uses race-marker color `[1,0,1,1]`, which the 2026-10-09 live Broker capture
confirms for ID27. Visual HUD/progress-marker appearance remains a separate
human evidence gate; see [J.2 runtime evidence](j2/runtime-evidence.md).

For the donor author workflow, `addon init --name ...` creates a project
containing this manifest contract plus an existing `vehicle-project.json`.
The bridge validates and compiles with the frozen Vehicle Authoring SDK rather
than implementing new DX/DXT or collision writers. See [J.3 manifest guide](j3/manifest.md).
