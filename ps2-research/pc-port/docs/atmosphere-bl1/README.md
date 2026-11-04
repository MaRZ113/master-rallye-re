# ATMOSPHERE1-BL1 — first-load baseline repair

**Targeted runtime acceptance passed:** Cloud3 is selected on the first cold race,
then survives Restart and menu/re-entry. Cold0/5 and native Auto/Disabled controls
also pass within the resource/D3D evidence below. Screenshots and the broader
compatibility matrix remain separate pending gates.

Worktree master-rallye-re-general, branch master, base9ff5d4868415d5fd8e13458a2e36bc935e34c29f.
Current package: `.research-output/atmosphere-bl1/candidate-first-load-v2/`.
DLL SHA256: `f2b51e0d41adeadf245bbd87c2e5f6362eb9b5324bfef5eae934bfdc0f9717ba`.

## Root cause and original native evidence

Diagnostic PID29176 reaches the expected gaAiCloudSetUp getter on the first race.
NumNetworkPlayers is already typed int0, but NetworkSyncActive ID10 has not been
published; the previous guard returns original0. Actual Cloud0/Layer0 serial747/748
and world fogFFDDDBDB follow. Restart publishes bool false, selects3, loads the
Cloud3 pair serial886/887 and fogFF8E5B3D. This rules out an uninstalled hook or an
alternate first-load getter. See diagnosis.json, original logs retained unchanged.

Original EXE: PE32 x86 base0x400000, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

- Sky call0x4B123C returns0x4B1241; native getter0x4D6760 runs before choosing the
  effective value. Later0x4B1374 reads CloudNumberUsed. Native model/palette/replay/
  Used writes and six-preset cycle remain in place.
- Network initializer0x48E3AA calls0x4AD930 to read FrontEnd/Network/Browse
  (0x6E5744), then publishes NetworkSyncActive (0x6B15F4): true at0x48E3D6 or
  false at0x48E473.
- PID39180 showed Browse remains assigned native null(tag12) even after native
  Sync=false publication. Original bool getter assigns the key ID at0x4D660C,
  checks tag0 at0x4D6610 and returns AL0/RET4 at0x4D6622 for a non-bool. Native
  constructor0x4DD980 supplies payload0/tag12. A typed-bool-only first candidate
  therefore failed cold acceptance and is preserved as superseded evidence in
  candidate-v1-runtime.json.

The revised early proof supports only a typed Browse=false or its exact readable
assigned-null state (matching key ID, payload0, tag12). It does not generalise other
wrong types or missing/unreadable entries to false. The absent Sync scalar itself
is never treated as false: its slot must exactly match native unconstructed
id0/payload0/tag12. Every early admission also requires typed NumNetworkPlayers0,
NumPlayers1, Type1/2, PlaybackReplay=false, current unpoisoned executing RaceTest job
of the same request/race, observer thread, native layer0/vtable0x691090 and the exact
CloudNumber call. All other early contexts retain the native value. Already
published typed Sync=false retains the prior path.

The original getter executes once per original call with preserved side effects
and RET4 ABI. No Broker write, extra model/texture load, fog-only swap, scene reload
or delayed mutation is introduced. All guard proofs are read-only.

## Actual game results on the final DLL

| Profile / PID | First native sky pair | First world fog | Later observations |
| --- | --- | --- | --- |
| Sky3 / 46188 | Cloud3/Layer3, frame195 | FF8E5B3D, frame196 | Restart816; menu/re-entry1404: same pair/fog |
| Sky0 / 42880 | Cloud0/Layer0, frame359 | FFDDDBDB, frame360 | cold control |
| Sky5 / 35132 | Cloud5/Layer5, frame318 | FFE0EFF9, frame319 | cold control |
| Auto / 26216 | Cloud0/Layer0, frame349 | FFDDDBDB, frame350 | native original1 remains1 on Restart; Cloud1/fogFF91A8CC |
| Disabled / 51080 | native pair134/114, serial747/748 | FFDDDBDB | no atmosphere hook/events; Restart serial886/887/fogFF91A8CC |

For Sky3, first requested3/original0/effective3 events are lines718/719 of
session-20261103-080500-46188.jsonl. Actual content hashes match the native registry:
Cloud3 `9ac31c63dc0ff827a5fa65a88d0ab0ca36638ada382fcc0301121bf76bef34e3`,
Layer3 `aced3edf44d7c3cbb05d03acc6403956e97d7212408ff702ceaad1d94da9086e`.
First serial747/748 are reused after Restart and menu, with actual134/196 and114/180
vertex/triangle submissions. Owner lifetimes1/2/3 and race generations6/10/15 correlate.

Nine final F10 captures across five processes are complete,386 draws each,zero
lost records and no malformed JSON. Sky3 frames556/1132/1757; Sky0 frame864; Sky5
frame827; Auto frames838/1498; Disabled frames550/1189. Disabled intentionally adds
no pixel-hash observer: that control confirms hook absence and native draw/fog/serial
sequence, not a pixel-exact Classic comparison. Exact log hashes/content observations
are in v2-runtime.json and controls-runtime.json. Original logs were not modified.
The user restored Atmo-copy Enabled1/SkyPreset3; installed DLL matches the final SHA.

## Diagnostics and baseline independence

Selection logs include requested/original/effective, every refusal reason, native
AI/egg/layer, scene/job/race/owner and Broker readiness including native-null versus
unpublished slots. Actual sky observation records content SHA, serial/format, both
geometry submissions and reset/race identities. World-pass fog is read from the
actual device. Logs are bounded by resource/race/reset or changed fog; counters
separate matched/rejected sky draws and world admission failures.

WorldLighting/LightProbe now use an Atmosphere-owned original-PC base_noise identity
helper constructed with GroundDetail requested=false. Identity no longer depends
on enabling the PS2 GroundDetail feature; native hash/material/lifetime checks and
state restoration remain. Actual terrain lighting/probe game draws are still pending.

The overlay also quotes freecam activation_result correctly: earlier supplied logs
contained malformed JSON, whereas all final sessions/captures parse. Frozen renderer
sources and its baseline DLL are unchanged; integration lives in audited patches.
Reflection UV/Reflection4/VehicleLighting1, dinput8, EXE/assets/saves were not edited.
No night/sun/headlight work, commit/push or agent deployment was performed.

## Build, package and remaining gates

24/24 baseline CTest,46/46 PS2 CTest,177/177 Python tests passed, including exact
original-EXE bytes/branches/strings and all early-guard rejection cases. The compiled
final bridge independently preserves argument order and RET4. Frozen baseline DLL:
`eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4`.
validation.json binds the current build report/patches/DLL and runtime results.

```powershell
$env:MRR_ATMOSPHERE_EXE='D:\Game\Master Rallye\MRallye.exe'
python ps2-research/pc-port/overlay/build_overlay.py
python ps2-research/pc-port/tools/package_atmosphere_bl1.py --output .research-output/atmosphere-bl1/candidate-repro
python ps2-research/pc-port/tools/analyze_atmosphere_bl1.py --logs 'D:\Game\Master Rallye Atmo-copy\MRRRenderer\logs' --output .research-output/atmosphere-bl1/repro-runtime-audit.json
```

Packaging requires a fresh directory and matching source/patch/DLL hashes; never
deploys. Profiles0/3/5/Auto/Disabled and Russian test/rollback instructions are included.
The immutable as-built manifest says runtime-pending; the later exact-SHA acceptance
is in this report/validation.json. Diagnostic and v1 packages remain superseded.

Remaining explicit gates in runtime-matrix.json: screenshots/pixel comparison,
other courses/modes, presets0/5 restart/menu, replay/reset/MSAA/FOV/FreeCam/HUD,
props/collision, terrain WorldLighting/LightProbe with PS2-Off, independent DLL
combinations and accepted PS2 reflection/grass/water compatibility. The targeted
first-load pass does not close those gates or authorise night/sun/headlights.
