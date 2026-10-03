# PlayerState save owners — final narrow static tracing

## Conclusion and evidence boundary

`CONFIRMED_BY_EXE`: PlayerState writes are requested by **explicit frontend,
name-editor and results/progress owners**, not by the generic Broker setter.
There is no single automatic dirty-entry owner. `SavePlayerState=True` is
eligibility when mode 3 runs; it does not schedule a save on mutation.

The lowest-risk independently mapped normal trigger is **one-player, offline
Quick Race → Change Vehicle → SelectCar**. It can confirm the already selected,
unlocked car, without completing a race or changing tuning/progress.

Analysis input independently rehashed: pristine retail, 3121214 bytes,
SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Ghidra 12.1.4 via local bridge/PyGhidra tooling; a fresh isolated scratch program
was used to resolve previously missing or incorrect function boundaries.
Decompilation was checked against instructions and frontend corpus XML.
No live game commands, save writes or executable modifications were performed.

### Reproduce the bounded evidence checks

From this checkout, run:

```powershell
python tools/scanner/playerstate_save_evidence.py <pristine-retail-MRallye.exe>
```

This read-only verifier checks exact size/hash, all 26 direct E8 sites and 25
literal mode PUSH instructions against the committed map. It does not prove UI
semantics or native persistence. Selective Ghidra exports can be repeated with
`tools/scanner/broker_core_evidence.py --binary <pristine> --output
research-output/general-re/persistence/playerstate-trigger/fresh --project-name
PlayerStateTrigger --analyze --disassemble-missing --function <entry>`, using
the entries in the [function map](playerstate-function-map.csv). Raw decompilation
and scratch databases remain ignored. Names are proposals, not asserted source names.

## Selected normal owner and complete chain

`DataScene/FrontendScreens/QuickRace.xml` associates ChangeVehicle with Button
ID 4. `VehicleSelect.xml` associates SelectCar with standard Button ID 2.
The executable factory/screen vtable identifies the vehicle-selection tick
`00481340` (`gaFEScreenVehicleSelectAI`, vtable slot at `00690B18`).

```text
SelectCar / positive frontend button event 2
  → 0045D930(1) returns button ID
  → 00481340 cases 1/2, offline branch
  → 004ADDB0: Frontend/InQuickRaceMode must be True
  → 004ADF50(player_index, selected_car) at 00481456
  → 0045D910 queues next screen (one-player: 0x1B QuickRace)
  → PUSH 3 at 0048148B; PlayerState literal at 00481479
  → 005229B0 at 00481495
  → 0052D700 → 0052EFB0 → 005FE460 / 005FE580
  → XML / owned serialized bytes → queued resource job
  → main-loop pump → 0054A340 → 0054A4B0 native writer
```

`00522D80` is the resource-owner singleton getter, **not** the mode-taking
serializer. Arguments pushed before that getter remain for `005229B0`.
The serializer/filter executes in the request path; disk IO is deferred to the
resource pump. UI return is not a disk-success acknowledgement.

All fixed mode-3 sites below use logical `PlayerState`, normally normalized to
`DataGame/PlayerState.xml`. Existing file → overwriteable `PlayerState.xml#`
backup → `CREATE_ALWAYS` → write. Backup failure stops before truncation;
other write failures use the existing resource error/callback path. There is no
new per-screen retry/transaction/error dialog recovered at these save sites.
See [native writer](save-pipeline.md) for the already established error paths.

## Direct call census and meaningful owners

A raw E8 census of executable sections found 26 direct calls to `005229B0`:
20 literal mode-3 calls, four mode-2 calls, one mode-1 call, one dynamic SaveAs
call. Each literal mode was checked in its enclosing assembly. This is a
direct-call census, not proof that every possible indirect invocation is absent.
The [JSON map](playerstate-save-trigger.json) records individual call sites,
conditions, event chains, evidence and remaining reachability limits.

| Owner | Mode-3 call sites | Event / condition |
|---|---|---|
| `004501D0` | `004502FC` | Results tick `0047F6F0`, button 1, game mode 7: update result/record then save |
| `00450310` | `00450452` | Same results owner: conditional trophy/unlock branch |
| `00452640` | `00452FCD` | MasterRallye progress serialization; `00452370` results button 1 / mode 5, and `00452590` via campaign vehicle confirmation |
| `00458870` | `00458939` | `0047D4C0`, event -2, modes 1/2/3; record time improves or ties (including player 2) |
| `0045B170` | `0045B227`, `0045B2BD` | Results button 1, modes 6/8: stage update; additional save at completion |
| `004606F0` | `004607CE` | Cup selection callback, positive 1/2; writes RallyeCup class/cup, then save |
| `00461C00` | `00461CDC` | Game Options tick `00461A90`: events 1/2/3/6; also 4/5 **before** entering name editor |
| `004669B0` | `00466E63` | `gaFEScreenNameAI` destruction, ordinary name branch; local text → selected Broker target → save |
| `0047A8C0` | `0047A9A2` | `0047A070` positive mode selection: QuickModeSelect values → QuickRace settings → save |
| `0047AB30` | `0047AC08` | QuickRace init, only if VehicleSetup/SaveSetup True; apply setup, clear flag, save |
| `0047BB00` | `0047BBC5` | RaceDetails init, same conditional setup transfer |
| `0047EA20` | `0047EAD0`, `0047EB24` | Track selection positive 1/2; network branch or offline QuickRace branch |
| `00481340` | `004813F7`, `00481495`, `004816EC`, `004817C5` | Vehicle selection positive 1/2; network, QuickRace and campaign branches |
| `004841B0` | `004841DC` | Setup confirmation `00484260`, SureChooser active and SureIndex=0; saves transferred tuning |
| `005B03D0` | `005B0526` | Calibration helper, Frontend/XYButton/NoReduction False; normal reachability UNKNOWN |
| `005B18A0` | `005B1B08` (dynamic) | Developer `005B0990 → 005B1370`, command 0x36 → SavePlayerStateAs(3), accepted filename dialog |

Developer SavePlayerStateAs is distinct from fixed-target normal saves. Cancellation
does not write; selected filename/read-only checks and mode handling precede the
generic save. It remains outside the Observatory command allowlist. No separate
developer control experiment is needed while a normal trigger is available.

## Normal event matrix

NO below means no dedicated save in the examined central path, not that an
arbitrary invoked screen destructor can never request one.

| Requested event | Result | Evidence / boundary |
|---|---|---|
| Startup | NO dedicated save | `006766A0 → 005AFB20`: loads configuration/options/PlayerState; no mode-3 request in central startup |
| Shutdown | NO dedicated save | Fully resolved central teardown below |
| Frontend entry | CONDITIONAL | QuickRace/RaceDetails init saves only pending VehicleSetup/SaveSetup |
| Frontend exit | UNKNOWN as a universal event | Name-screen destruction does save; no universal exit owner recovered |
| Game Options exit | CONDITIONAL | `00461A90` positive 1/2/3/6 → `00461C00`; negative -3 skips it |
| Quick Race selection | YES on mapped confirmations | Mode, track and vehicle positive handlers above; merely scrolling/changing a field is insufficient |
| Entering race | UNKNOWN as a universal event | Selection/setup may already save; do not attribute their write to race startup |
| Leaving race | CONDITIONAL | `0047D4C0` event -2 and mode/record predicates, not every departure |
| Race Results | CONDITIONAL | `0047F6F0` button 1 and game modes 5/6/7/8; replay button 2 lacks that save path |
| Campaign/progress completion | YES on mapped branches | `00452370`, `0045B170`, `00450310`; mode/stage/trophy predicates |
| Explicit profile/progress update | CONDITIONAL | Name destructor, cup selection and progress owners; no generic mutation hook |
| Reset | NO dedicated save in central reset | `00522910` resets Broker/context; downstream state-specific callbacks are not blanket-proven |
| Developer Save Player State | YES after dialog acceptance | Command 0x36 is SavePlayerStateAs mode 3 |

## Shutdown: no guaranteed final save

`006766A0 → 005AFE30` frame loop ends on Game/Quit, then calls `005AF920`.
Teardown closes debug/native windows and editors, releases application state,
calls `00522800`, then application +0x38 object's vtable +4.

- `00522800 → 004046E0` gets the singleton whose vtable is `0068F4AC`.
  Slot +4 is `00404710`, a **RET-only** routine.
- App constructor `005AF5C0` sets member +0x38 to an object with vtable
  `00692F50`; slot +4 is `0064DBB0`: KillTimer, DestroyWindow, clear fields.
- No PlayerState save exists in these resolved teardown edges.

Thus shutdown alone does **not** guarantee saving a changed name. A state-specific
destructor can have its own save; that is not a universal shutdown write.

### Historical boundary correction

Earlier notes left `005B0505/005B0526` in an unnamed application routine, and an
old scratch program incorrectly forced function entry `005B0500` inside an
instruction. Fresh pristine analysis establishes entry **005B03D0**:
`005B0505` is **mode 2 Options**, `005B0526` is mode 3 PlayerState. Its gate is
Frontend/XYButton/NoReduction, with force-feedback calibration writes. No direct
E8 callers were recovered. It must not be cited as a shutdown/startup save.

## Player1Name: real edit buffer, ordinary Broker destination

Game Options event 4 first calls `00461C00`, then stores the **destination path
string** `Settings/Player1Name` in `Frontend/Name` through `004D8720` and opens
name screen 3. Event 5 selects Player2Name. `Frontend/Name` is **not** the edited
text itself. Name init `00467340 → 00467620` dereferences that selected target to
populate a local text object; `00467810` appends characters in object +0x44
(text pointer +0x48, length +0x4C).

Scalar deleting destructor `00466990 → 004669B0`, vtable `00690758`, handles
reserved-name branches separately. For ordinary input such as U3TEST:

1. `00466DF5..00466E15`: read Frontend/Name and obtain the destination path ID.
2. `00466E17..00466E2C`: intern local edited text at object +0x48.
3. `00466E31..00466E42`: generic String setter `004D85F0(destination,text)`.
4. `00466E59..00466E63`: mode-3 PlayerState request.

This is a **specific UI lifetime save**, not a special serializer exception for
Player1Name. Input termination in `00467CB0`, object +0x70, causes `004677C0` to
request return screen 0xE. Exact prior U3 destruction/pump timing is not known.

Literal xrefs at `006B15DC` and the initialized path-ID consumers were inspected:
race/player construction, results/display, vehicle setup/selection, network
name handling and Game Options. `004AD7D0` is another ordinary Settings/Player1Name
String writer; `00449380` supplies session/player names, and `00469C60` has an
empty-name fallback from a backend name. No unconditional reset to `1P` before
the mapped offline QuickRace save was recovered. This does not prove absence of
every computed-key write. No normalization/fallback explains U3TEST's loss yet.

| Player1Name literal/ID xrefs | Owner / role |
|---|---|
| `0044AF1B`, `0044B19F` | `0044A8E0`: race construction/name transfer |
| `0044942B`, `004AD7FF` | `00449380` / `004AD7D0`: session name read and ordinary name writer |
| `00469CFA` | `00469C60`: empty-name fallback |
| `0044F95A`, `0047CBDF`, `004811F9` | setup, race-details and vehicle-select display |
| `00461B0A` | Game Options selects Player1Name as Name UI destination |
| `0046BD9B`, `0046BDE0`, `0043720C` | network/name consumers; no save from these literal accesses |
| `004814CB`, `00481666` | campaign vehicle-selection name consumers |
| `00432B50` → ID `006F5AE8` → `00434509`, `0043453D` | static path-ID initialization and `004343C0` network/name consumers |

This list covers all recovered literal references and that initialized ID,
not every dynamically constructed Settings path.

## Interpretation of U3 and closeout

See [accepted U3 evidence](u3-runtime-result.md) and the
[single next test](u3-save-trigger-test.md). Native name UI **already has** a
mode-3 request, so “the UI never saves” is disproved as a blanket explanation.
The missing runtime proof is where this particular session fell between request,
queue pump, file output and reload. The observed QuickRace/Car0 generation change
cannot timestamp that write relative to the name edit.

**R-BROKER1: ONE RUNTIME TEST REMAINS for this PlayerState gap.** The static trigger
owner question is answered; the observed U3 loss is not yet causally explained.
Unrelated SCENE bulk-clear and other previously bounded unknowns remain outside
this task. No U3 FULL PASS, developer persistence control, U4 or new phase began.
