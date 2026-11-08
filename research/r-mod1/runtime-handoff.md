# R-MOD1-F human runtime handoff

## Safety and candidate selection

Test each checkpoint package independently, in a disposable copy of the retail
game directory and an isolated save/profile. Do not combine files from the
three package directories. Do not install Observatory or Vehicle SDK for this
test. The supported file is the original `MRallye.exe` with SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and size
3,121,214 bytes. Do not continue if package verification or launcher
preflight fails. The executable on disk must remain byte-identical before,
during and after the run.

| Checkpoint | Package directory | Plan SHA256 | Operations | Status |
|---|---|---|---:|---|
| F1 | `.research-output/r-mod1/first-integrated-candidate-v14-f1-r3` | `06597e1ea451df7427482fde97fbc707b5b7f48e12ad4ffc87acb5f421dac049` | 7 | Ready for separate human test |
| F2 | `.research-output/r-mod1/first-integrated-candidate-v15-f2` | `c972078639f9b76c7e3eb9aa4d6729aa85709248fed232df0389b2c73d3e0d98` | 13 | Ready for separate human test |
| F3 | `.research-output/r-mod1/first-integrated-candidate-v16-f3` | `3c760a475b854fd1435584f04450eada4dd90647ed7bbb7144fbf101e375d89d` | 17 | Ready for separate human test |

For each package, first run from the package directory:

```powershell
.\MRallyeRandomizerLauncher.exe --verify --game-dir 'D:\path\to\isolated-game'
.\MRallyeRandomizerLauncher.exe --preflight --game-dir 'D:\path\to\isolated-game'
```

Require `SUSPENDED_PREFLIGHT_PASS`, no native writes during preflight, and
child termination before resume. Then launch through the supplied launcher.
Do not launch a package by copying its DLL into the retail game directory.

## F1 — Quick Race V2 and live policy reload

Use `quickrace-t1-v2.ini` for the initial check. Start a new Quick Race and
record its policy/config hash. Return to the menu, change only
`QuickRace = 1` to `QuickRace = 4` in the runtime INI, then create a fresh
Quick Race. The new roster should report Full policy and the new config hash.
If the game has an active or prepared race, its roster must remain unchanged;
the edit applies at the next fresh roster-generation boundary. Also test an
invalid or half-written temporary INI: it must retain the last valid snapshot.

Confirm displayed class choices agree with `Stock`, `T1`, and `Full` semantics
for several newly generated races. Do not infer uniform distribution from a
few outcomes. This candidate's new claims are Quick Race ConfigVersion=2 and
stable live policy snapshots only; it does not newly qualify counts above the
previously runtime-confirmed four AI.

## F2 — Cup, Master Rallye and Invitation generation owners

Use a fresh isolated progression profile. Do not resume an existing Cup or
Master Rallye as the first inclusion test.

1. With `cup-mixed-v2.ini`, create a genuinely new T1 Rallye Cup. Record each
   participant's physical CarID, CarClass and DriverID in stage 1. Advance to
   stage 2 and verify the roster is unchanged; no reroll should occur.
2. With `master-diverse-v2.ini`, create a genuinely new Master Rallye
   competition. Record its native roster. Save, exit the process, start a fresh
   process and Resume. Verify the same roster is restored; advance a stage if
   practical and verify it remains unchanged.
3. With `invitation-t3-v2.ini`, test a new Invitation. Verify the native
   ordinary T3 pool and its stage reuse; bonus/progression T3 vehicles must
   not be injected by the Invitation policy.

The randomizer operates at each mode's new-roster owner, not on later stage
materialization. A previously generated stock-only event is expected to
remain stock-only.

## F3 — Challenge preview/race identity synchronization

Use `challenge-full-v2.ini`. Enter a Challenge and compare the visible preview
vehicle name/model with the physical opponent CarID published for the actual
Challenge race. The same selected opponent must survive preview redraw and
Start; it must not reroll between the preview and race. Edit the policy while
the preview remains open: the displayed and launched opponent should stay the
same. Back out and re-enter: a new preview may use the updated policy. With
Stock policy, the authored event opponent must remain unchanged.

The Challenge title, human vehicle, driver, objectives and event rules remain
native-owned. Test preview-name and preview-model correspondence as separate
observations; a correct name alone is not proof of the correct physical model.

## Quick Race regression for cumulative checkpoints

For F1, F2 and F3, run ordinary Quick Race at one and three AI and the
previously owner-confirmed four-AI/five-total case on a previously tested
course. Confirm Randomizer policy and Opponent Extender remain independent:
the policy can be selected with the extender disabled, and Stock policy does
not disable the count feature. One–Seven menu navigation does not itself prove
grid safety. Counts above four AI still require the separate course/start-grid
runtime qualification in [`grid-safety.md`](grid-safety.md); do not attempt an
unqualified high-count race as part of this policy smoke test.

## Evidence to return

For every tested checkpoint, report the exact candidate ID, package hashes,
active INI SHA256, process path and unchanged on-disk EXE SHA256. Separate
launcher logs from Broker captures and human gameplay observations. For races,
capture `Race/Type`, `Race/NumCars`, `Race/NumPlayers`, and each active
`Race/CarN/{CarID,CarClass,DriverID,PlayerType,CarType,WheelType}` where those
Broker values are available. Preserve captures and raw sidecars unchanged.

Do not claim runtime PASS for any checkpoint or newly covered mode until the
owner has completed that checkpoint's actual game test. Stop on a crash, a
missing participant, a mismatched Challenge preview/race identity, or a
changed original executable; preserve the candidate directory and diagnostics
for review.
