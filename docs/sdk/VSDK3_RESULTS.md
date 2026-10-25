# V-SDK3 — Rally Workshop delivery

2026-10-25 · `research/vehicles` · no push/publication.

## Delivered

Run **`Rally-Workshop.cmd`** at the checkout root. The local native binary is
already built under `.research-output/rally-workshop/`; the launcher rebuilds
it if missing. Python with Tk and the existing CMake/MSVC toolchain are required
for a fresh source checkout. This is a source-based application, not an installer.

The graphite/amber application provides a persistent vehicle library, real
DX/material/texture inspection, reversible RGB texture editing and qualified
same-size PNG replacement. Save, Validate, Build, Undo and Restore call the shared
SDK through `master_rallye.workshop.service`. Stock authoring remains bounded to
the existing qualified Pajero1/Megane18 mechanism. Source families can be inspected
without pretending that a resource-only export is a registered runtime addon.

The center panel shows an explicitly labelled GPU capture. **Open interactive
3D** opens the managed native Previewer window. It supports orbit, middle-button
pan, zoom, geometric picking/highlighting, F/Home, presets, persistent bookmarks,
F3 measurements and camera-preserving reload. The original fixed-function
diagnostic renderer is reused; this is not proof of original-game visual parity.

The local private library contains Subaru, Lancer, Pajero and Megane. A clean
source checkout starts with file-picker onboarding and contains none of these
proprietary assets. Builds snapshot project inputs; later Restore cannot mutate
an already generated build recipe. Short SDK-owned build paths avoid the Windows
toolchain path-length failure reproduced during validation.

## Evidence

All detailed evidence is private under `.research-output/vehicles/vsdk3/`.

| Check | Result | Evidence |
| --- | --- | --- |
| Full synthetic regression suite | 790 tests, 1 skipped, PASS | `tests-release.txt` |
| Real GUI addon editing | Inspect, tint, Save, Validate, sealed Build, Restore; 11,005 GPU pixel bytes change | `gui-delivery/gui-validation.json` |
| Real GUI stock editing | Megane body tint; 211,546 GPU pixel bytes change; Save/Validate/Build/Restore | same report |
| Restore | Original GPU capture restored byte-for-byte for both projects; third build after stock Restore emits zero overrides | same report |
| Native navigation | Picking, focus, pan, bookmarks, overlay, orbit, zoom, reload, camera retention, presets, model switch PASS | `navigation-delivery.json` |
| Renderer smoke | UV asymmetry, handedness/culling, transparent depth, reflections and brake states PASS, including stock Megane | `gpu-delivery/validation.json` |
| Candidate isolation/reproducibility | Addon changes one DXT; stock adds one DXT override; restored stock changes nothing; native payload identical | `candidate-preservation.json` |
| Original EXE/graphics DLL | SHA256 unchanged against input snapshot | same preservation report |

GUI automation supplies file-picker answers only; it executes actual Tk controls,
resource codecs, background jobs, GPU renders and native runtime builds. The
report's historical status label mentions two SDK builds; its action log also
records the third, restored-stock build.

### Local demonstration candidates

Relative to this checkout:

- Addon edit: `.research-output/workshop-builds/68294430903e/candidate/Launch-SDK-Roster.cmd`.
- Stock edit: `.research-output/workshop-builds/66f707b64f7f/candidate/Launch-SDK-Roster.cmd`.
- Restored stock: `.research-output/workshop-builds/a20af39a372c/candidate/Launch-SDK-Roster.cmd`.
- GUI captures: `gui-delivery/addon-edited-gui.png` and `stock-edited-gui.png`
  beneath the evidence directory.

These deliberately obvious blue texture edits demonstrate reversible authoring;
they are not new canonical vehicle visual milestones. Both library projects were
restored to their original state after testing.

## Scope and remaining checks

- Whole-texture multiplication preserves alpha but affects baked decals too.
  Masked repaint/basecoat editing is deferred. Picking intersects geometry without
  sampling alpha texels. Renderer reflection/lighting remain documented previews.
- Imported source extraction still uses existing CLI adapters. Physics, Audio,
  Camera Studio, Blender Bridge and the later editors remain planned; the GUI
  does not expose fake native controls for them.
- A source-specific stock geometry override is rejected by this texture-only
  import path rather than silently lost. Unknown/ambiguous layouts fail closed.
- No geometry, physics, wheel placement, runtime capacity, audio hooks or gameplay
  camera policy were changed. One generic Previewer brake-case decoder fix handles
  stock Megane's lit-first two-case ordering; native game resources are untouched.
- The owner must launch edited candidates and confirm menu/race, AI, audio,
  camera, damage/glass, brakes, finish/Results/re-entry. Offline and GUI tests do
  **not** constitute gameplay qualification.

The 43 accumulated pre-Studio phase commits are listed in `COMMIT_LEDGER.md`.
Shared files were committed as their actual accumulated final state; no fictitious
intermediate revisions were reconstructed. V-SDK3 is a separate following commit.
The handoff archive contains tracked source/docs/tests only, excludes private game
inputs, captures and compiled binaries, and records its exact Git source boundary.

Further instructions: `RALLY_WORKSHOP.md`, `CAPABILITIES.md`,
`REGRESSION_MATRIX.md`, `MASTER_PLAN.md`.
