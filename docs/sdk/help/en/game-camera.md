# Gameplay Camera 2.0

Physics / Camera / Vehicle Details → Gameplay Camera → Open Game Camera Lab.
Modes0–2 are the three source Follow presets;3–4 are source Fixed0/1.
They are five player choices, not five independent camera classes.

Select Modified → Open Live Preview. FOV, Follow Front/Back/Up and aspect changes
update the SAME running D3D9 window. LMB drags Follow eye height/back, Ctrl+LMB
changes forward target, wheel changes FOV. G switches to free inspection;
Shift+drag edits the camera while inspecting its live amber frustum/target guides.
Original/Donor comparison is read-only. Unknown smoothing, pitch, terrain and
replay controls remain read-only. Fixed position comes from the source native
bounds initializer; only its FOV is authored.

Live changes are UNSAVED drafts. Apply Live Draft records this mode through the
shared project history; Cancel discards it. Save/reopen, Undo/Redo, Reset selected
mode, Reset Original and Reset Donor are separate reversible actions. Build uses
the saved/current project state, never silently applies an open draft.

Auto-frame Follow draft / Frame car projects the full staged vehicle and adjusts
supported draft parameters to leave a10% margin. This corrects lower-window
clipping without translating meshes or physics. Original retains exact source
framing. The neutral floor, one-metre grid and displayed height reference use
the assembled REST POSE; they do not simulate suspension or game terrain. They
also make height visible from the Fixed/bonnet view. Diagnostic ground/guides
do not affect model bounds, source selection or gameplay resources.

Native mode overrides are per-CarID and per-preset but intentionally affect
NORMAL AND SPLIT setup for that preset. No global Cameras.xml change is made.
FOV20–140, Front .1–50m, Back .1–30m, Up −5–10m are SDK safety ranges, not native
engine limits. CarID0 authoring remains unsupported pending owner-key qualification.
Original model hash, resource key and bounds remain guarded. Existing separate
Follow half-length / height-extent inputs are preserved.

Flat static poses, source mode switching, FOV/aspect arithmetic and copy ABI are
checked using original x86. The viewer uses D3D9 and a RH camera convention;
the original projection helper is LH. Actual dynamics, interpolation, terrain,
rear/replay/split lifecycle and final D3D8 composition require gameplay comparison.
See GAMEPLAY_CAMERA2_RESULTS.md for addresses, cases and the owner checklist.

CLI: workshop_vehicle.py PROJECT game-camera --mode 3; set-camera-mode JSON
--mode 0; export-game-camera --mode 0 --view modified. Empty JSON{} resets that
mode. Existing validate/build/undo/redo commands use the same Core.

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
