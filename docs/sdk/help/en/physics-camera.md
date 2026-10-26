# Physics, Camera and Vehicle Presentation

Open a project, then select **Vehicle Studios** in the main toolbar. This
modeless workspace shares the current project, Save, Undo/Redo, Validate and
Build services. Switching projects switches its contents; no second author
project or alternative native compiler is created. Originals remain immutable.

## Physics Studio

For an addon with a qualified independent physics profile and configured
retail inputs, choose **Inspect qualified sources**. The Core verifies the
original retail archive and matching unpacked members before exposing fields.
The tree groups both native vehicle initialization and qualified player deltas.
It shows the original retail donor, current authored value, selected reference,
type, units and validation boundary. Select a field, edit its typed value and
choose **Apply selected typed field**. Invalid values fail before saving.

Reference families are schema-qualified sources from the verified archive.
Select a reference, inspect it, then **Copy selected reference group** to copy
compatible fields into this addon's existing independent family. Dimensions,
ride datum and count-driven engine arrays are retained. The copy report lists
retained fields. A failed dependent check rejects the whole copy; originals and
another addon's profile are never changed. Reset physics restores this project's
original profile; Undo/Redo also applies to reference copies.

Units marked **native units; per-field semantics not qualified** must not be
interpreted as SI merely because the field has a familiar name. Bounds are SDK
authoring guards, not measured maximum engine capabilities. MomentOfInertia is
the configured radius vector in non-cuboid mode, not a direct inertia tensor.
Player values are deltas and are validated with effective base values. Engine
array counts and damage fields remain read-only. There is no arbitrary XML edit.

This compiler authors initialization data, not a live dynamics simulator.
Wheelbase, track, radius and suspension can affect native wheel anchors; no
geometry, collision, visual fitment, audio source or camera is silently adjusted.
Changing RevLimit does not retune Audio Studio sources/presets automatically.
Stock physics authoring is not supported here; stock copy-on-write passthrough
and the established Material/Paint workflows remain available.

## Gameplay Camera

This is separate from Previewer orbit/pan/bookmarks and from UI-art framing.
**Inspect exact source and bounds** resolves the same mechanical, collision-fit
and visual-resource stages as the SDK build. Follow half-length and height are
native model-bound extent inputs, **not direct camera distance or height**.
The side-view Z/Y rectangles compare original bounds with authored extents.
They do not predict the full dynamic chase camera.

Target CarID must match the project. Family and exact built car.dx SHA256 are
pinned; the roster builder checks them again against actual output. A changed
model requires requalification, not a silent hash update. Existing qualified
stock copy-on-write pairs may use the same adapter; unsupported identities and
CarID0 fail closed. Reset removes this project's override. FOV, follow smoothing,
look-at and replay controls are unsupported. No new native patcher is used.

## Vehicle Details and friendly texture names

Addon manufacturer, model, combined display label and Results label are editable
printable ASCII. The shown 32/64/96/64 character budgets are conservative SDK
guards, not proven native buffer lengths or a promise of screen-width fit.
Description is project metadata. CarID, addon identity, runtime family, class,
resource namespaces and native texture filenames are locked. Stock game display
names remain read-only.

Select a texture and save a friendly alias. Search accepts either the alias or
original filename; inspect opens the original Texture Studio resource. An alias
does not rename files or change draw bindings, and does not identify every use
of a shared atlas. Associations use immutable source hashes. Compatible visual
versions retain aliases; changed or omitted textures produce explicit conflicts.
All original manual layers remain in the parent project.

## Generate Vehicle Art

Choose Frontend complete.dx or Race car.dx. Frontend includes its wheel assembly;
Race uses the existing explicit, provenance-bearing presentation wheel instances.
These are rest-pose presentation transforms, not simulated suspension equilibrium.
Yaw/pitch overrides and bounded render padding control framing. Blank angles use
the existing role-specific original-MR-style camera defaults.

Generate both or either image: Vehicle Select **128×128**, Results **32×16**.
The existing CPU diffuse renderer and **mr-native-v1** composer are reused. It is
an approximate offline presentation, without native environment/reflection parity.
Generation is bounded and does not edit the vehicle. Compare original and
generated images, then explicitly **Apply generated art to vehicle**. Raw source
renders are pinned so the native compiler applies composition exactly once.

Save/reopen retains applied images and provenance. Regenerating one role leaves
the other intact. Undo/Restore returns original UI sources. Build uses the
existing append-only bank allocator, dimensions, frame references and CRC checks;
only this addon's allocated frames change. Stock image generation can be
inspected, but replacing stock bank frames is unsupported. A generated preview
is not installed until Build succeeds; its D3D8 presentation remains an owner test.

## Versions, validation and recovery

Physics, names and compatible aliases transfer as separate authoring layers to
new Source Fidelity/Classic versions. They do not become the new Restore baseline.
Camera model hashes and artwork require requalification/regeneration for a new
visual baseline and are reported as conflicts; the parent remains intact. Audio
sources and presets transfer through their established independent service.

Save, Validate and Build preserve all four audio layers, crew/wheels, native
damage and brake lights. Build creates a private candidate; the installed game
is untouched. Compare separate physics-only, camera-only and combined candidates.
Offline/native CPU and Windows Previewer evidence cannot prove actual race
handling, chase dynamics, UI text fit, AI lifetime or sound playback. Test those
in the game later, including exit/re-entry, Results and unrelated stock/addon cars.
