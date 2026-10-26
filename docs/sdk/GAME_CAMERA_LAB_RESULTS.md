# Game Camera Lab, Race Progress Marker and private runtime state

26 October 2026. Branch `research/vehicles`, starting source milestone
`59becef67db940e0c9d300ae96b62c9ebdddc4b0`. No game launch, original EXE/DLL/retail
write, new capacity expansion, visual recipe rebuild or physics tuning.

## Delivered functionality

| Capability | Implemented boundary |
|---|---|
| Gameplay Camera Preview | Shared Core first-update eye/target/up rule; original x86 updater AND matrix-writer CPU replay |
| Free Inspection | Existing orbit/pan/zoom, selection, bookmarks, reload and model switching preserved; G toggles modes in Lab-launched viewer |
| Original / Donor / Modified | Actual source-bound original, immutable imported override or original fallback, current per-CarID custom |
| Static source setup | Follow arrays0–2 and split XML parameters inspectable; FOV/distances/smoothing/pitch read-only |
| Camera authoring | Existing guarded half-length / height-extent override; source hash/family/CarID guard; Save/Undo/Redo/Reset, inherited roster override removal |
| Guides and captures | Eye/target crosses, aim lines, illustrative frusta/ground; private matched GPU snapshots; guides hidden in Gameplay view |
| Race HUD marker | Picker/presets/live HEX preview/normalized RGB, original/current local HUD frame, fixed original alpha, history/reopen/reset/build |
| Stock marker registration | Read-only; independent addon registration only |
| Softened Whine | Separate named per-Lancer preset and candidate; accepted original retained; gain/pitch response only |
| PlayerState | Fresh shared roster builds seed exact original installation save; no fabricated unlocks or existing-save replacement |

Open Rally Workshop → Physics / Camera / Vehicle Details → Gameplay Camera →
Open Game Camera Lab. Vehicle Details / Race HUD holds the marker controls.
The normal existing Studio and CLI still share SDK Core; no duplicate GUI
native patcher or sound engine. Offline Help includes `game-camera`.

## Native evidence and limitations

See [exact camera map](../../research/vehicles/vsdk2/game-camera-lab.md).
REA/Ghidra12.1.4 identified exact constructor, serializer, source-copy, manager
and matrix-writer bodies. The follow updater lacks a Ghidra function definition;
its original decoded instructions are replayed directly. Do not turn a failed
decompiler lookup into invented source.

The static pose is qualified for flat upright first update, pitch disabled,
no acceleration/history correction. Sixteen translated/yawed extent cases and
four actual resource pairs are checked. Native world orientation is checked
before renderer axis adjustment. Final D3D8 projection, live target origin,
speed/acceleration helpers, pitch/terrain and smoothing history, rear view,
replay and mode-switch lifetimes remain UNKNOWN / PENDING_OWNER. D3D9 source-FOV
projection and guide frusta are conspicuously approximate. No invented dynamic
slider or unsupported per-car FOV/distance/smoothing authoring is exposed.

Source follow0 DistBack3.5 and DistUp.65 are separate from model extents.
Lancer source terms2.619833/2.019470 give eye(0,2.669470,-6.119833), while test
terms2.25/1.5 give eye(0,2.15,-5.75), both target(0,0,14). This establishes a
bounds contribution to high framing, not the entire live camera cause.
Megane, frozen/current Subaru and GT4 Pajero are separately inspected/captured;
Subaru is read-only and its exact frontend repeated wheels supply rest pose.

## Isolated owner candidates

Private root: `.research-output/vehicles/camera-lab/`. Run each candidate's
`Launch-SDK-Roster.cmd` separately, with no existing game instance.

| Folder | Change vs accepted Fidelity Classic/Auto baseline | Game asset differences | Native payload |
|---|---|---:|---|
| `t/a/candidate` | Lancer28 marker `#20D9E8` only | 0 | 9 differing bytes, same166304-byte size |
| `t/b/candidate` | Lancer28 follow inputs2.25m /1.50m only | 0 | prefix unchanged,573 appended bytes;166877 total |
| `t/c/candidate` | Lancer28 Softened Whine response only | 0 | 13 differing bytes, same166304-byte size |

All369 sealed resource paths match the accepted Classic baseline. Owner-mutable
PlayerState/options and backup files are reported separately, not counted as
model/physics regressions. CarIDs26/27/28/29 and 30-entry class mapping retained.
Geometry, source paint, tyres/glass, crew, lights/damage, wheel anchors, UI art,
physics and accepted Engine/Spool/BOV resources remain byte-identical.

Marker data is NOT merely a GUI image: emitted native initializer targets
registry+4+28*52 and supplies RGBA float32 bytes
`8180003edad9593fe9e8683f0000803f`. Other registered rows unchanged. Existing
original initializer writes record+24..+30; original participant paths publish
Race/CarN/Colour, consumed by the shared HUD marker (R5V-E0.1d.2 research and
prior owner ID25 red A/B). The delivered emitted initializer is CPU-executed
with native string/record-constructor seams mocked, exact ID/destination/tail
arguments checked. This proves candidate emission, not new gameplay tint proof.

Camera candidate executes its DELIVERED combined payload through18 guarded
original-initializer cases: selected, other IDs sharing model, stock, boundary
slots, malformed names, absent Broker, disabled extents and changed source model.
Native stack/register/x87 preservation checked. No extra runtime camera hook.

Softened Whine: drive.75→.60, coast.45→.36, reference RPM4000→4480,
pitch min.20→.18 / max1.8→1.62. Fade/neutral and source waveform remain unchanged.
`Accepted Original` and `Softened Whine` presets survive reopen/load. Private
`original-whine-only.wav` / `softened-whine-only.wav`: peak8122→5750,
RMS1745.25→1202.37 PCM16 under the same scripted sequence. Combined auditions
remain hot/clipped at near-listener full mix, as before; diagnostics expose this
and do NOT silently normalize accepted Engine/Spool/BOV. Actual listening is an
owner choice, not an asserted acoustic match.

## Player save and runtime housekeeping

`DataGame/PlayerState.xml` comes from the original EXE installation root.
Three fresh candidates copy167314 bytes exactly, source/output SHA256
`656a8c99c789803d0c90069e4a7831421527fc4c9079e470342bd1d9a4a77361`.
Unlock availability follows that save; SDK never edits progression. Missing
source is explicit, malformed/DTD/linked/oversize sources rejected; destination
exclusive creation prevents overwriting an existing candidate save. Originals
remain immutable. This reuses the existing mutable runtime-state exception,
not an asset-integrity exemption. Native verifier accepts modified private save,
rejects changed DXT SHA, and passes after restoring the DXT/save test bytes.

Five old V-SDK4D `runtime` leaves moved (not deleted), total1,950,483,496 bytes,
to `.research-output/runtime-quarantine/2026-10-26/`; source projects, reports,
launchers, current candidates and frozen runtime dependencies retained. Their
old launchers no longer resolve the moved runtime. Owner may delete quarantine;
moving on the same disk does not itself free physical disk space. Extra current
regression-only runtime leaves are also retired there with a separate manifest
after validation; owner-facing a/b/c remain in place.

## Windows/offline evidence

- `tests-release.log` (also full-tests-final.log):901 tests,2 existing optional skips (missing legacy J1
  bundle and old V4.11 wheel fixture); no fabricated historical runtime.
- `windows-release/windows-validation.json`: actual Tk marker preview/apply,
  Save/Undo/Redo/reset, native Camera Lab edits/reset/donor, snapshots, reopen,
  validation, stale-popup rejection, owned standalone viewer replacement/cleanup.
- Actual D3D9 event harness: orbit, zoom, pan, picking/focus, bookmarks, controls,
  model switch, reload, culling GPU states; Gameplay input lock/G toggle checked.
- `real-projects.json`, `native-static-pose-matrix.json`: actual model reports,
  original code pose/basis replay. Private `*-original.png`, Lancer modified,
  `camera-guides.png`, source scene hashes retained for reproduction.
- `native-marker-roster.json`: emitted roster mapping/AI append/display/audio
  ABI and exact per-ID marker arguments with typed native seam mocks.
- `native-camera-guard.json`:18 delivered guard/ABI cases.
- `native-source-presets.json`:24 static pitch-disabled replays using all six
  actual setup/split parameter sets across four model bounds; no dynamic pitch claim.
- `shadow-gui/validation.json` and `shadow-native-three-models.json`: actual
  Shadow Studio history/reset/captures and58 native cases each for3 models.
- `native-engine.json`:124 engine replay cases; `native-sfx.json`:28 SFX cases
  and10001 gain checks; `native-multi.json`:24 voices freed, stock passthrough,
  reentry/isolation; `native-failures.json`:3 allocation-failure checks.
- `regressions/windows-regressions.json`: actual Audio, Paint/Crew, stock material
  reference and Texture Studio25–400% embedded/detached Windows workflows.
- `.research-output/vehicles/gcm/gui-validation.json`: real selected-surface
  RGB/texture-binding/reflection, GPU Undo/Redo/Restore, addon/stock isolated
  builds and restored stock zero-edit build.
- `.research-output/vehicles/gcp/windows-validation.json`: real Physics/Camera/
  names/art/aliases workflow, exact resource diffs and unchanged geometry/audio.
- `candidate-differences.json`, `save-integrity.json`: sealed resource/native
  differences and fail-closed integrity evidence. Launcher verify/environment/
  native-allocation preflights pass for all3 owner candidates.

CPU, GUI, package and GPU results do not prove D3D8 gameplay, AI acoustics,
live camera lifetime or HUD appearance. PERF2 runtime operations/resources are
preserved; no new measured frontend timing claim.

## Short owner checklist

1. Existing accepted Fidelity Classic is control. Test a: Lancer cyan progress
   marker, normal other car colors, player and AI; no artwork/paint changes.
2. Test b: same track/start position/display aspect/camera and stock options;
   stationary, acceleration, coast/brake, bump/jump and collision. Record camera
   mode, CarID, screenshots, then rear view, split/replay if used, Results/reentry.
   Compare static posture to Lab, not its empty diagnostic background or exact
   renderer projection. Verify Subaru/Pajero/stock cameras remain unchanged.
3. Test c versus control at identical Engine/SFX settings: drive/coast/neutral
   Whine, lower pitch/gain, accepted Engine/Spool/BOV preserved; player/AI,
   race exit/reentry and Results. No mandatory new global balance.
4. Confirm copied owner progression offers intended unlocks; all save changes
   remain in the chosen isolated candidate. Originals are not the active save.

Stop here for owner/source review. No Heritage Garage, GT corpus/generalization,
new import, native multiband audio, Blender Bridge or Fleet Builder started.
