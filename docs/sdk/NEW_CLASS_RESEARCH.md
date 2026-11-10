# Additional vehicle class (CLASS-T4) — research and pilot

Status (11 November 2026): **PASS OFFLINE / OWNER D3D8 PENDING.** A fourth
Vehicle Select class is implemented as a reversible SDK layer on top of the
owner-accepted V-DEF4.1 33-record roster. Pilot build: 35 records, T4 = Dakar 2
Mitsubishi Pajero #205 (ID33) and Dakar 2 Nissan Pickup #203 (ID34). See
[CLASS_T4_PILOT_RESULTS.md](CLASS_T4_PILOT_RESULTS.md) for the vehicles.

Retail executable SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Evidence: REA/Ghidra 12.1.4 on the retail image, plus capstone disassembly of the
image reconstructed from the accepted V-DEF4.1 patch manifest (J.2 + G.1 + ID26/27
caves + SDK33 payload). Pseudocode is supporting evidence only; every patched
byte below is checked against its exact preimage at build time.

## Where the three classes live

| Consumer | Finding |
|---|---|
| `gaFEScreenVehicleSelectAI` (vtable `0x690B08`) | Heap object of **0x34 bytes**, allocated at `0x480A96` and `0x401BE2` (`PUSH 0x34`). Layout: `+0x10` current class, `+0x14` selection[3], `+0x20` count[3], `+0x2C` PlayerID, `+0x30` number of published classes. The arrays are back to back, so class index 3 would read count[0] — a fourth class needs relocation, not a bigger count. |
| Class list `0x480B60` | Builds Broker list `Frontend/VehicleSelect/VehicleList` from localization group `0x1E` entries 1..3 (`T1 (UNMODIFIED)`, `T2 (MODIFIED)`, `T3 (CUSTOM)`), gated by `Progress/OpenedModes/T2Cup`/`T3Cup` and cheats; sets `+0x30` = 1/2/3. Championship modes (5, 6, 8) lock the class (`Frontend/VehicleSelect/LockClass`). |
| Class navigation `0x481EB0` | Upper bound is the **length of VehicleList**, not a constant. Appending a fourth string is enough to reach class index 3. |
| Car carousel `0x481F50`, arrows `0x481C8D..0x481D43`, publisher `0x481950` | Index selection[class] and count[class]; right class arrow uses `+0x30`. |
| Forward/reverse maps `0x481E20`/`0x481E50` | Already replaced by the SDK33 explicit map; retail fallbacks and ID26/ID27 caves address the arrays with fixed displacements. |
| Vehicle Select scene | `gaFrontendXYButtonAI` eggs choose their row by `Y ID` (T1=0, T2=1, T3=2) and column by `X ID`/`ButtonNXPos`. A row 3 needs no engine change. |
| Race class | The 52-byte registry record keeps a class at `+8` (13 readers, all publishing `Race/CarN/CarClass` or MasterRallye championship keys). Opponent chooser `0x458090` switches over 5 cases; case 3 is the empty pool `0x4582D5`, case 4 aliases T3. Group `0x4F` (`t1`/`t2`/`t3`) and championship slots `PlayerTnCar*` have no fourth entry. |

## Chosen design: T4 is a frontend class that races in the T3 record class

* Object grows to **0x54 bytes**; selection[4] moves to `+0x34`, count[4] to `+0x44`.
  30 displacement bytes are rewritten (`sdk_capacity_native.T4_DISPLACEMENTS`):
  constructor, G.1 count stub, XValue publication (retail and J.2 re-entry), publisher,
  arrows, carousel, retail forward/reverse fallbacks and the ID26/ID27 map caves.
  A scan of the whole Vehicle Select code and all inherited caves finds no other
  indexed use (the remaining `[r+r*4+0x14]` at `0x481BE0` is the vehicle registry).
* The G.1 constructor stub tail (`0x68E643`) now enters `ctor4`: selection[3]=0,
  count[3]=number of T4 vehicles.
* The J.2 jump at `0x481152` (just before `VehicleList` is published) enters `t4list`:
  only when all three retail classes are published (`+0x30 == 3`) it appends the
  label (default `T4 (RAID)`, roster `t4_label`) via the game's own string constructor
  `0x4D11D0` and list insert `0x407B30`, frees the temporary with `0x5B4C00` and sets
  `+0x30 = 4`. Championship paths (class locked, `+0x30 == 1`) never show T4.
* The SDK33 explicit forward/reverse maps gain class index 3 at the relocated fields.
* Registry records of T4 vehicles keep **class 2 (T3)**. Opponents, `CarClass`,
  Results, audio and championship code therefore stay on qualified T3 paths; no
  jump-table or localization edit is needed. AI insertion of T4 vehicles is disabled.
* Widgets `T4_CarN` are cloned from `T2_Car8` with `Y ID = 3`, placed after the
  last T3 egg; unlock mirrors the audited stock ID10 oracle like every SDK vehicle.

## Verification (offline)

* Unicorn emulation of the built 35-record image: all 35 forward/reverse map
  positions round-trip (T4 local0 -> 33, local1 -> 34); carousel stops at the T4
  count; `t4list` inserts exactly one `T4 (RAID)` item, keeps ESP/ESI balanced and
  skips when only two classes are published.
* Launcher `--verify`, `--verify-launch-environment`, `--self-test-native-allocation` PASS.
* Synthetic tests: `tests/synthetic/test_class_t4.py` plus the existing roster/SDK suites.

## Known limits and next steps

* Owner D3D8 test pending: class switch, T4 carousel, race, Results, menu re-entry.
* T4 is offered only after T3 is unlocked (the class index must equal the list position).
* No T4 championship/cup, no T4 AI pool, no native localized class name (the label is
  an SDK string). A true race-side class 3 would need jump-table entry `0x4584D8+12`,
  group `0x4F` index 3 and championship key sets.
* The profile admits 34 or 35 records (one or two T4 vehicles); more needs only the
  same widget/frame budget review.
* The launcher refuses unknown loader wrappers next to the EXE; the installed
  `dinput8.dll` (Extra Options ghost build) is not admitted, so the pilot runs from an
  isolated hardlinked host (`tools/make_isolated_game_host.py`). Porting this layer into
  the single dinput8 release loader is the planned product path.
