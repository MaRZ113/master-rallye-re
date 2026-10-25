# Rally Workshop — V-SDK3 Studio Foundation

## Launch

Windows, Python3.10+ with Tk, CMake and the existing supported MSVC toolchain.
Tested here with Python3.15/Tk9, Visual Studio18 and Windows SDK10.0.26100.
This is a runnable source-based Windows application, not a self-contained installer.
No new pip/framework dependency or external model application is needed.

```powershell
python tools/build_rally_workshop.py
.\Rally-Workshop.cmd
```

The root launcher builds the asset-free native viewport on first use if missing.
An already built launcher is also at
`.research-output/rally-workshop/Launch-Rally-Workshop.cmd`.
Application binaries and user workspaces are separate:

- `.research-output/rally-workshop/`: native viewport and app launcher/build files.
- `.research-output/rally-workshop-workspace/`: private library/project pointers.
- `.research-output/workshop-builds/<job>/`: short-path isolated SDK build jobs.

The current local workspace is seeded with the user's own Subaru/Lancer converted
families, a Pajero author project and a qualified stock Megane project. This
onboarding data is not in Git, the source archive or a public asset bundle.
A fresh checkout starts with an empty library and real file-picker workflows.

## Interface

Left: actual local project library, grouped by stock/addon/converted family.
Center: latest real GPU capture, explicitly not an embedded interactive canvas.
**Open interactive3D** opens a managed native window; no `SetParent`/fake viewport
embedding is used. Right: actual mesh/material IDs, shader flags, semantics,
texture slots/dimensions/BGRA usage and supported texture edits. Bottom: actual
operation diagnostics, source provenance and build/preflight results.

Supported actions are enabled only when their state/input is available. Future
modules are described as unavailable rather than exposed as inert editing buttons.
Loading, compilation and rendering run outside the Tk event thread.

### Native 3D controls

| Input | Action |
| --- | --- |
| LMB drag | Orbit around focus |
| LMB click | Nearest geometry draw selection / amber wire highlight |
| MMB drag | Pan camera and orbit focus together |
| Wheel | Zoom |
| F / Home | Focus selected draw / reset complete view |
| 1–6 | Front, rear, side, three-quarter, top, opposite side perspective presets |
| Ctrl1–6 / Shift1–6 | Persist / recall view bookmarks |
| F3 | Native preview data: CarID when known, source, draw/triangle/texture counts, BGRA bytes, Previewer FPS |
| R | Reload resources and retain orbit/focus/selected stable draw |
| Tab / E / B / W / D / L /0 | Model / reflections / brake / wireframe / diagnostic color mode / isolated layer / all layers |
| F1 | Complete key help |

Picking is geometric, not alpha-texel/cull-aware shader picking. Selected native
draws report their actual source model/material to the inspector, including
wheel instances. An altered topology is not guessed into the previous selection.
D3D9 world lighting/sorting/inherited instance behavior remains approximate.
Preview navigation is distinct from the native per-car gameplay camera profiles.

## Addon workflow

1. **Open project**: select an existing SDK author directory containing
   `addon.json` and `vehicle-project.json`. Workshop creates a private copy,
   pinned rendered baseline, content-addressed texture layers and undo history.
2. Inspect a real draw/texture. Apply an RGB multiplier or replace it with a
   supported same-size RGBA PNG. Multiplier acts on the whole image, including
   baked logos: it is deliberately not advertised as masked/base-coat repaint.
3. **Configure build inputs**: choose an existing qualified roster candidate
   directory, original retail `Data.sma` and its matching unpacked tree. The
   roster must contain exactly one matching author entry. The existing frozen
   base-only addon cannot be silently converted into a new author registration.
4. **Save → Validate → Build**. Existing SDK author compilation and roster
   composition produce a new candidate and execute launcher preflights.
5. **Undo**, **Restore texture** or **Restore all** reverts Workshop edits.
   Each build snapshots its inputs, so later Restore does not change that build.

Physics, audio, UI and other existing project sidecars are retained; no hidden
donor/class/CarID/fitment adjustment is made by the material UI.

## Stock workflow

1. **New stock**: choose user-supplied unpacked retail data, then Megane/18 or
   Pajero/1. Existing validated stock COW projects can also be opened.
2. Inspect and edit an actual DXT; source files stay untouched. Existing stock
   texture overrides are retained, not silently discarded. Prior geometry
   overrides are rejected by this texture-only import path instead of lost.
3. Choose the baseline roster candidate in Build inputs. Save/Validate/Build
   generates a changed-only stock override and an isolated sealed candidate.
4. Restore and rebuild: zero edits emit zero stock overrides and native resource
   passthrough returns. Registry/class/unlock/AI/save identity is unchanged.

Stock IDs beyond the two verified pairs are not enabled. Stock physics/audio
authoring and Camera Studio UI remain deferred; existing CLI profiles still work.

## Converted family inspection

**Open DX family** accepts actual converted `car.dx`/`complete.dx`/`wheel.dx`
and sibling DXT resources. Source runtime manifests can supply a declared CarID
for inspection. These generic projects build resource packages only, explicitly
not a new installed CarID. Use an SDK author project plus a qualified roster for
a launchable addon candidate. Existing provenance-bearing preview sidecars are
retained where available; no wheel positions are guessed from arch appearance.

## Service and extension boundaries

`master_rallye.workshop.service.WorkshopProject` is the GUI-independent facade:
`create`, `inspect`, `tint`, `replace_png`, `save`, `validate`, `build`, `undo`,
`restore`, `configure_build`. Widgets do not implement another converter or
native runtime. Existing SDK methods remain the authoritative compiler/validator.

`workshop-project.schema.json` reserves authoring metadata for panes, masks,
transforms, audio presets and adapters. The format registry distinguishes actual
MR DX/FEED BGRA/PNG support, qualified GT3/GT4 CLI adapters and planned Blender
round-trip. Reserved metadata has no invented native execution semantics.

## Validation and next human checks

Actual Windows UI automation answers file pickers, invokes real buttons/dialogs,
waits for worker jobs and compiles native launchers. It does not mock SDK builds.
Private evidence: `.research-output/vehicles/vsdk3/gui-delivery/` and its report.
Both edited GPU captures visibly differ; both Restore captures match their
original byte-for-byte. The stock flow additionally rebuilds a zero-override
candidate after Restore. Separate synthetic and native GPU/navigation regressions
are listed in [REGRESSION_MATRIX.md](REGRESSION_MATRIX.md).

Run edited candidates in Master Rallye yourself to verify actual material/glass,
reflections, damage, brake lights, sound, camera modes, AI/Results/re-entry and
unrelated stock/addons. GUI and D3D9 evidence is not native gameplay confirmation.
V-SDK4–7 have not been started.
