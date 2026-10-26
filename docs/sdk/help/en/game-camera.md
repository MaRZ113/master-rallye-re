# Game Camera Lab and Race Progress Marker

Open Physics / Camera / Vehicle Details → Gameplay Camera → Open Game Camera
Lab. Select Original, Donor or Modified, then Gameplay Camera Preview. Original
uses the native stored model bounds; Donor uses the imported camera override if
one exists, otherwise Original. Modified uses this project's current override.

The preview executes a shared first-update framing rule checked against the
original retail x86 follow updater and matrix writer. It is qualified only for
a static, flat, upright target with pitch disabled. Native follow-array indices
0–2 and split-screen setup values are readable, but their dynamic pitch,
acceleration and smoothing behavior is NOT simulated. Final D3D8 projection,
live target movement and renderer overrides remain unqualified. This is not a
gameplay-perfect camera simulator. Source FOV is read-only; D3D9 uses an explicitly
approximate aspect-scaled projection. Free Inspection remains the normal editing
camera, with orbit, pan, zoom, bookmarks and surface selection unchanged.

G switches Gameplay / Free in a Lab-launched Previewer. Mouse orbit/pan/zoom is
locked in Gameplay mode. Free Inspection + guides shows eye crosses, target
crosses, aim lines and illustrative frusta: red Original, green Modified. Guide
range, grid and aspect are diagnostic choices, not native clipping planes.
Capture selected view produces a private GPU snapshot of the chosen pose.

Only follow half-length and height extent inputs are editable. They are NOT
direct camera distance or height: source Dist Back / Dist Up are separate terms.
Apply, Save, Undo, Redo, Reset Original and Reset Donor use shared project history.
Changing these inputs never changes collision, physics, geometry or global
Cameras.xml. Build emits the existing source-pinned per-CarID adapter. CarID0
and unqualified families remain unsupported. No per-car FOV/smoothing patch is
claimed. A changed visual baseline requires requalifying the camera source hash.

Vehicle Details / Race HUD edits an independently registered addon's RGB progress
marker tint. Enter #RRGGBB, select a preset or use the RGB picker. Preview shows
Original and proposed Current on dark/light backgrounds using the genuine local
HUD frame when available; a synthetic fallback is labeled. Apply persists the
per-CarID race_colour_rgba value. Alpha stays at its original qualified value.
Save, Undo/Redo, Reset, Restore and Build are reversible. Stock registration color
is read-only. No HUD image, body paint or Vehicle Select/Results artwork changes.

Fresh SDK roster builds copy DataGame/PlayerState.xml from the original EXE's
installation into isolated runtime state when present. Bytes/hashes are preserved;
no unlocks are manufactured. Missing save is reported. Invalid/linked saves are
rejected; existing candidate saves are never overwritten. Normal runtime save
mutability and sealed gameplay-asset validation remain separate.

The optional Softened Whine named preset reduces only transmission response
gain/pitch, preserving Accepted Original and all Engine/Spool/BOV sources. Audition
uses scripted load/RPM and native engine DSP, not DirectSound/gameplay acoustics.
Compare it in game later; it is not a global default change.
