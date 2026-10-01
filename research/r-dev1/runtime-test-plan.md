# R-DEV1 runtime-test record and remaining plan

The flag-isolation test below is now recorded from the owner's runtime report. It must not be repeated as a pending question. Remaining tests are proposals only and have not been performed in this phase.

## Common staging

1. Use retail EXE SHA256 bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4 from corpora/retail. Keep that corpus and Data.sma read-only.
2. Create one untouched pristine staging copy and four independent case copies outside the repository. Preserve the archive and all original files. Record recursive hashes before each launch.
3. In each case, add a loose DataGame/dev.xml copied from corpora/retail/Data.sma_unpacked. Change only Menues/Enabled and DebugWindow/Enabled. Keep Game.xml, Editors.xml and other data unchanged. R-EXE1 established loose requested path precedence over archive fallback.
4. Monitor writes under each case directory and any user-profile/registry side effects. If writes escape the copy, stop and move subsequent testing to a disposable Windows profile/VM.
5. Launch and close normally. Do not send WM_COMMAND, inject messages, patch the executable, invoke editor/build/save/convert commands, or alter other broker values.
6. Use the window helper in --list mode to record HWND titles/classes. If Tesseract is available, capture Debug text to an output path outside the game copy; otherwise use a screenshot.

## Test A — 2×2 gate isolation — owner result recorded

Build/data: exact build and staging identity were not supplied by the owner. Target: startup 005AFB20 and the two values in DataGame/dev.xml.

| Case | Menues/Enabled | DebugWindow/Enabled | Expected comparison |
|---|---:|---:|---|
| A | false | false | no Debug window reported when Menues is false |
| B | false | true | DebugWindow toggle had no observable effect |
| C | true | false | Debug window reported when Menues is true |
| D | true | true | no additional observable effect from DebugWindow |

Owner-reported outcome: **CONFIRMED_BY_RUNTIME** that `Menues/Enabled` gates the native Debug window in the tested configuration; changing `DebugWindow/Enabled` produced no observable change. The test build, exact four case results, screenshots/log captures and integrity manifest were not supplied, so this record intentionally does not invent them. The result supports the static consumer path and classifies `DebugWindow/Enabled` as `ORPHANED_OR_REDUNDANT_KEY` (**STRONG_HYPOTHESIS**), not absolutely dead.

## Test B — passive Debug logger observation

Build: retail, fresh D copy. Target: 004D0620 and 0064E4C0–0064EC50.

Launch to the normal front end, do not open editors/start a race, and capture the Debug window during startup. Expected logs depend on model/cache decisions: “Loaded cached DX texture” may occur on cache hit; Reading GXM/build-stage messages only when source/build paths are taken. Missing one stage is not failure. Compare recognized text to debug-message-producers.json and preserve executable spelling moSortPlane.

Allowed actions: observe windows, capture output outside the case copy, close normally. Do not change cache flags, force rebuild, invoke BuildData, or edit/save broker values.

## Deferred tests

- BuildData 0x58 is recursive and can overwrite DX/DXT. Its normal UI route is not found; do not synthesize WM_COMMAND. Revisit only if a legitimate entry appears, using one tiny DataGx source in a disposable copy with no existing cache target.
- Flow Builder 0x30 and local conversion/build IDs can write files, but the opener is absent from the mapped main menu. Do not inject the ID. If a legitimate route is found, use a fresh copy/new basename and monitor the full tree.
- Game/Scene XML Save uses CREATE_ALWAYS and is not in the mapped menu. If an ordinary route appears, save only to a new name in a disposable copy.
