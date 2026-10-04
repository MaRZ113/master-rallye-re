# R-AI1.2 staged human test

Status: **READY FOR HUMAN RUNTIME**. This new implementation has no human
runtime pass yet. Maximum: five active participants; do not test six.

## Package and start

1. Use an isolated retail copy. Preserve its original EXE and PlayerState.
   Use a fresh normal T1 profile for Quick Race. Other modes require a profile
   where those modes are normally available; no unlock/save editing is required
   by this tool, and no fresh-profile T3 frontend access is assumed.
2. Copy the generated `package/four/MRallye.exe`, `MRallyeRandomizer.dll`
   and `MRallyeRandomizer.ini` beside the isolated game's data. Keep the
   package's module/patch manifests. Existing user config is not overwritten
   automatically. The five package uses the same DLL/config with a different
   exact EXE, only for the separate R-AI2 setup in Stage A.
3. Verify hashes before launching:

| File | SHA256 | Bytes |
|---|---|---|
| Four EXE | 60946990b685390032510c4bbed448674faebf33c929a46f52bc527e219dfc85 | 3121214 |
| Five EXE | 32a09c466b9bb40513d8a801e0e9f420e902d6486ceb7ae76b243c7408404629 | 3121214 |
| DLL | 517c4aa20e8dc80f2d51a64a79e59183d3ae27d47dbb3e0334ab458695c366f4 | 89600 |

From the repository root, set `$exe` to the staged isolated MRallye.exe and
`$obs` to the existing audited Observatory directory. `$pkg` below denotes
the generated package root. Example validation/start commands:

```powershell
python tools/r_ai1_2_randomizer.py verify "$exe"
# For the five EXE, add --five to verify and check-race.
python tools/r_ai1_2_randomizer.py verify-module "$pkg/MRallyeRandomizer.dll" "$pkg/module-manifest.json"
python tools/r_ai1_observe.py --observatory "$obs" --candidate "$exe"
```

Use Observatory **L** to launch; enable the game's native developer menus
as in the earlier tests. At the stated active-race point choose **3**, Capture
with label. Preserve JSON plus raw Dump sidecar, config used at generation,
and `MRallyeRandomizer.log`. Do not use Broker writes. Captures go to this
checkout's ignored `.research-output/r-ai1-2/observatory/` area.

## Stage A: actual AI count

Use `QuickRace=Mixed`, Race mode, one human, Ghost OFF, normal initial ID0/T1.
With the four EXE, generate races with one, two, three AI. Capture once after
the grid is live and cars are moving; labels below are checker inputs.

| Label | Visible opponents | Expected total | EXE |
|---|---|---|---|
| qr-mixed-ai1 | 1 | 2 | four |
| qr-mixed-ai2 | 2 | 3 | four |
| qr-mixed-ai3 | 3 | 4 | four |
| qr-mixed-ai4 | 3 (R-AI2 effective four AI) | 5 | five |

For ai4, close the process and stage the five EXE. Use the unchanged R-AI2
guard: **ID0/T1, Track10/ItalyS4, Race, one human, Ghost OFF, Opponents3**.
Do not edit NumCars or create participants manually.

Observe every active AI's distinct model/motion/progress and no extra actor.
Mixed permits class duplicates and can coincidentally produce the player class;
the complete module log proves that every active slot passed policy selection.
If visual cross-class evidence is absent, one new race is a valid extra sample.

For counts up to three, use another normally selectable car/class, course and
difficulty across the samples when available. A fresh profile need not unlock
T2/T3: use an already valid progressed profile only for that class-change check.
Record the intended human ID. The separate five-car guard stays unchanged.

On ai3, select Restart and capture **qr-mixed-restart**; composition must match.
Return to Quick Race and create a NEW race, capture **qr-mixed-new**; generation
is new and may vary. Restart is not a fresh randomization sample. Complete at
least one representative race through Results and frontend return, reporting
models/wheels, AI, physics/collision/damage, HUD, progression and stable exit.

## Stage B: policy controls

Return to the four EXE. Use one matched three-AI Quick Race:

| Config QuickRace | Label | Expected |
|---|---|---|
| Stock | qr-stock | native same-class selection, no policy game RNG draws |
| Mixed | qr-mixed-ai3 may be reused | each AI independently selects eligible class; duplicates allowed |
| Diverse | qr-diverse | first three AI cover T1/T2/T3 in RNG-selected order |

Edit only the mode value before NEW race creation; save each generation's
config alongside its capture. Invalid/missing config is fail-safe Stock;
no unknown-build bypass is supplied. The module is not a driver randomizer.

## Stage C: new mode coverage

Use the four EXE, one human, normal mode selection. Use a profile with each
mode normally accessible. No network/split-screen/Attract/Replay setup tests.

| Mode | Config | Label | Expected total / lifetime |
|---|---|---|---|
| Challenge | Stock first | challenge-stock | 2, original fixed matchup and driver |
| same Challenge event | explicit Mixed | challenge-mixed | 2, same human/event/rules, native driver route, randomized AI vehicle |
| RallyeCup | Diverse | cup-stage1 | 4, first three AI T1/T2/T3 |
| Invitation | Diverse | invitation-stage1 | 4, intentional cross-class opt-in; core vehicles only |
| MasterRallye | Diverse | master-new | 4, T1/T2/T3 AI once at NEW competition |

For Challenge, the human vehicle is fixed by the event; **do not assume ID0**.
Take its intended ID from the matched Stock capture, and require that same
human in the opt-in capture. Driver selection remains native; separate NEW
events may draw different DriverIDs. Restart must retain the current driver.
Complete this event to test objectives;
vehicle balance changes intentionally. No all-events completion claim follows
from one event. Cup/Invitation need stable race/results and normal stage advance.

## Stage D: native roster lifetime

Cup: after stage1, preserve its config/log, edit `RallyeCup=Stock` and advance
to stage2. Capture **cup-stage2**. IDs/classes/DriverIDs must match stage1.
The change must apply only to a later newly created cup. Invitation uses the
same native three-stage owner; capture **invitation-stage2** on normal advance.

Master uses Diverse here so the saved roster necessarily includes cross-class
AI, rather than depending on one Mixed draw. Complete the new race to a natural native save point. Preserve
`master-new` and the generation config/log. **Exit the whole game process**.
Change `MasterRallye=Stock`, launch again and Resume the saved competition.
Capture **master-resume** in its active race, then continue normally and capture
**master-next** if an additional stage is exercised. Existing randomized
IDs/classes/DriverIDs must persist under the changed config. Do not select NEW
competition for the Resume test. Keep the original generation config for
checking the reused roster, even though the current file now says Stock.

Required Master proof: save succeeds, full process exit, fresh process load,
same roster, playable next race/progression. Native transfer emulation alone
does not satisfy this. Cup/Invitation disk-resumable rosters are not promised.

## Checker commands

Set `$json`, `$raw` and `$log` to preserved capture/sidecar/module-log files;
`$cfg` is the config used when THIS roster was generated. `$mode`, `$total`
and `$player` come from the tables and intended normal human selection.
The checker handles paths/identity/canaries; manual inspection of every Broker
path is unnecessary. Use `--five` only with the five EXE.

```powershell
python tools/r_ai1_2_randomizer.py check-race "$json" --raw "$raw" --candidate "$exe" --observatory "$obs" --module "$pkg/MRallyeRandomizer.dll" --module-manifest "$pkg/module-manifest.json" --config "$cfg" --log "$log" --mode "$mode" --count $total --player $player > .research-output/r-ai1-2/<label>-checked.json

python tools/r_ai1_2_randomizer.py compare-roster .research-output/r-ai1-2/qr-mixed-ai3-checked.json .research-output/r-ai1-2/qr-mixed-restart-checked.json
python tools/r_ai1_2_randomizer.py compare-roster .research-output/r-ai1-2/cup-stage1-checked.json .research-output/r-ai1-2/cup-stage2-checked.json
python tools/r_ai1_2_randomizer.py compare-roster .research-output/r-ai1-2/master-new-checked.json .research-output/r-ai1-2/master-resume-checked.json
python tools/r_ai1_2_randomizer.py summarize-mode .research-output/r-ai1-2/qr-mixed-ai3-checked.json .research-output/r-ai1-2/qr-mixed-new-checked.json
```

Replace `<label>` with an actual filename, not literal angle brackets. Counts
are total participants; ai1/2/3/4 means total2/3/4/5. `compare-roster` checks
identity only, not times/positions. `summarize-mode` reports observed variation
without requiring that one pair differ or claiming uniform RNG. A complete
matching diagnostic group may be from an earlier generation/reused save;
human lifecycle labels establish whether it was NEW, Restart or Resume.

Automatic verdict is **BROKER_STATE_MATCH_ONLY**, runtime_full_pass=false.
Actor/gameplay/progression and fresh-process persistence require your report.
Named vehicle/physics fields are checked where present against existing stock
evidence; persistent path presence alone never proves actors.

Native Results Dump uses the already proven NULL-safe formatter. Textual `{}`
still cannot distinguish NULL from allocated-empty. Preserve raw/JSON/logs
locally; do not commit saves, screenshots, game binaries or dumps.

Removal: all-Stock config or removal of DLL disables selection on future NEW
rosters. Restore pristine EXE to remove research bridge/hardening/capacity.
Native saved Master rosters remain intact. Stop after these tests; no six-car
test or R-AI2.1 work is authorized here.
