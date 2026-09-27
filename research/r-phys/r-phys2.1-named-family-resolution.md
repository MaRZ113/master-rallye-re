# R-PHYS2.1 — Named vehicle-family source resolution

**Scope:** retail `MRallye.exe`, one ordinary local race setup path. This is a focused follow-up to R-PHYS2. It does not trace downstream physics constructors and does not claim a runtime observation.

## Result

The retail code statically resolves a participant's integer `_CarClass` through a 25-entry named-family table, then uses the resulting family name to read `Vehicles/<family>` into the temporary vehicle-parameter record. The same participant index is later passed to the writer for `Vehicles/CarN`.

The missing live observation is narrow: no runtime capture has yet shown that a normally selected Navara reaches this call with `_CarClass == 7` and the string `Navara`. The source-to-reader and reader-to-writer paths are **CONFIRMED_BY_STATIC**; that exact in-game value is **UNRESOLVED**. Per the R-PHYS2.1 stopping rule, this phase stops at one read-only breakpoint procedure.

Retail executable used for the static audit:

- `MRallye.exe`: 3,121,214 bytes
- SHA-256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
- Ghidra project: existing disposable retail project; analysis was read-only

## Dataflow

```text
ordinary local race setup
  FUN_00449D40
    -> FUN_0044A320
       -> read Race/NumCars and Race/NumPlayers
       -> for participant index N in [0, NumCars):
          FUN_0044ED50(N, player-overlay-enabled)
            -> competitor _CarClass integer
            -> family catalog entry -> local_4e8
            -> same catalog name + /Player1 or /Player2 -> local_4e0
            -> FUN_00493E30(local_4e8, VehicleParams temporary)
                 -> FUN_00493770 -> Vehicles/<family>
                 -> read parameter groups
            -> optional FUN_00493FD0(local_4e0, VehicleParams temporary)
                 -> FUN_00493770 -> Vehicles/<family>/PlayerN
                 -> read Modifications overlay
            -> FUN_004938C0(N, VehicleParams temporary)
                 -> FUN_00493600 -> Vehicles/Car<N>
```

Evidence labels for the arrows:

| Link | Status | Evidence boundary |
|---|---|---|
| `FUN_00449D40 -> FUN_0044A320` | `CONFIRMED_BY_STATIC` | Non-network branch calls the ordinary per-car setup loop. |
| participant index `N -> FUN_0044ED50(param_1)` | `CONFIRMED_BY_STATIC` | `FUN_0044A320` passes its loop index unchanged. |
| `RaceData/Competitor[N]/_CarClass -> numeric class ID` | `CONFIRMED_BY_STATIC` | The call sequence prepares the competitor-property accessor with `FUN_004B0AF0`; `FUN_004B0630` calls `FUN_004B0490(N)` to select the indexed `RaceData/Competitor` record and reads its `_CarClass` property. |
| class ID -> family string | `CONFIRMED_BY_STATIC` | `FUN_0045A3C0` catalog entry at `+0x24 + ID*0x34`; `FUN_00458E70` initializes IDs 0–24. |
| ordinary selected Navara -> ID 7 / `Navara` at runtime | `UNRESOLVED` | Requires the read-only breakpoint below. The table maps 7 to Navara, but the live participant value was not captured. |
| `local_4e8 -> FUN_00493E30` | `CONFIRMED_BY_STATIC` | Assigned from the selected catalog name, copied to a working string, and used at `0044F0CD`. |
| `FUN_00493E30 -> Vehicles/<family>` | `CONFIRMED_BY_STATIC` | It calls `FUN_00493770` with the source-family string. |
| `FUN_00493E30 -> VehicleParams temporary` | `CONFIRMED_BY_STATIC` | Eight group readers receive the same temporary parameter object. The return status is ignored by this caller. |
| `local_4e0 -> optional FUN_00493FD0` | `CONFIRMED_BY_STATIC` | Derived separately from the same family table and participant index; called at `0044F170` under its branch conditions. |
| `FUN_004938C0(N) -> Vehicles/CarN` | `CONFIRMED_BY_STATIC` | Same `param_1` is passed from `FUN_0044ED50`; writer calls `FUN_00493600`. |
| resulting values consumed by ordinary physical-contact constructor | `UNRESOLVED` | Outside this narrow phase. |

## `FUN_0044ED50`: local values and source chain

`param_1` is the current `FUN_0044A320` loop index. At entry, the two managed string locals are initialized empty. The function eventually releases both strings. The high-level names below follow Ghidra's stack-local labels; `FUN_004D1990` is the string assignment operation in these call sites.

### Base family: `local_4e8`

On the ordinary non-attract, non-mode-7 branch:

1. `FUN_004B0AF0` lazily initializes the shared competitor-property descriptor object (`FUN_004B03A0` registers `_Name`, `_CarID`, `_CarClass`, `_DriverID`, and race-stat property names). It does not select the participant. `FUN_004B0630` calls `FUN_004B0490(param_1)`, which resolves `RaceData/Competitor` and selects element `N`.
2. `FUN_004B0630` applies the registered `_CarClass` property descriptor at accessor-object offset `+0x14` to that record and returns the integer value. The `_Name` descriptor at `+0x0c` is also used by the generic property-access path; it is not the class-name source in this call.
3. `FUN_0045A3C0()` returns the vehicle catalog. The code indexes `catalog + 0x24 + class_id*0x34` and reads the entry's family-name string.
4. `FUN_004D1990` at `0044EDFE` assigns that value to `local_4e8`.
5. The family string is copied to a temporary string and passed to `FUN_00493E30` at `0044F0CD`.

There is an alternate branch when the ordinary branch guards fail. It calls `FUN_004AC660(param_1)` instead of the `_CarClass` getter, then indexes the same catalog and assigns a family string. `FUN_004AC660` reads a different record field at object offset `+0x68` through the `_Name` property descriptor. This phase does not assign a stronger semantic name to that alternate value. The `FUN_0044ED50` broker call remains the same.

### Player modification namespace: `local_4e0`

Both branches then call `FUN_0044E400(output, param_1, class_id)`. It fetches the same catalog family name and appends the exact suffix `/Player1` when `param_1 == 0`; every nonzero participant index gets `/Player2`. `FUN_004D1990` assigns the result to `local_4e0` at `0044EE2D` on the ordinary branch, with the equivalent assignment in the alternate branch. The output is later passed to `FUN_00493FD0` only when the player-overlay gate and a separate object flag permit it.

The two locals are independent string copies. A later experiment that changes only `local_4e8` immediately before `FUN_00493E30` would read Trooper's base configuration but would leave `local_4e0` as `Navara/Player1`; that would not be a whole-family redirect. A future one-identity runtime redirect must affect the shared family-name source before both locals are constructed, or redirect both locals while preserving their managed-string representation. No mutation is prepared here.

## Race iteration and index meaning

`FUN_00449D40` enters `FUN_0044A320` on its non-network route. `FUN_0044A320` obtains its loop bound from `FUN_004AC040` and loops `N=0` to `N < NumCars`. The two registered keys are `Race/NumCars` and `Race/NumPlayers`; the corresponding getter helpers read the participant setup object at offsets `+0x38` and `+0x3c`.

For each `N`, the loop passes that exact index to `FUN_0044ED50(N, ...)`. The same function later calls `FUN_004938C0(N, &VehicleParams)`, and `FUN_00493600(N)` formats that number as `Vehicles/Car%d`. Therefore `param_1` is the race participant/car index in this setup path, not the family/type ID. For example, Navara's catalog type ID is 7, but the first race participant writes to `Vehicles/Car0`.

The overlay-enable argument is true only for the first `NumPlayers` participants and is cleared by attract-mode or mode-7 conditions. Player zero therefore uses `Player1` in its normal local-race overlay path; the function's exact helper behavior assigns `Player2` to every nonzero index.

## Vehicle family/type catalog

`FUN_00458CD0` initializes a catalog array with capacity for 26 records, then calls `FUN_00458E70`. The latter explicitly initializes 25 family/type records, IDs 0–24. The associated names and IDs are:

| ID | Family | ID | Family | ID | Family |
|---:|---|---:|---|---:|---|
| 0 | Landcruiser | 9 | Jump | 18 | Megane |
| 1 | Pajero | 10 | Rmonster | 19 | Mattserati |
| 2 | Tata | 11 | Patrol | 20 | Bruno |
| 3 | Terrano | 12 | Newrav | 21 | SeatBuggy |
| 4 | Chevyblazer | 13 | Kiasportage | 22 | Kamaz |
| 5 | Xtrail | 14 | Wildcat | 23 | Icecream |
| 6 | Frontera | 15 | Simmbugghini | 24 | Ufo |
| 7 | Navara | 16 | Astero |  |  |
| 8 | Forester | 17 | Kangoo |  |  |

The catalog directly gives the control mappings Navara -> ID 7 and Jump -> ID 9. Three family names are passed through untyped data symbols in the Ghidra listing; their raw bytes were separately checked in the retail image. The focused audit emits those bytes as `RAW_FAMILY_STRING` records.

Identity layers remain separate:

| Question | Result |
|---|---|
| Does the `Trooper` family/config name exist? | Yes, in retail `vehicles.xml` and in the player modification XML. |
| Is `Trooper` one of the 25 names initialized by `FUN_00458E70`? | No. No Trooper mapping is present in this initializer. This does not prove no other hidden/dynamic mapping exists anywhere in the executable. |
| Is there a selectable Trooper slot? | `UNRESOLVED`; no frontend/selectability work was done here. |
| Does the same retail family/type initializer contain `forklift`? | No. The separate R-PHYS1 resource inventory found a forklift model directory, but no same-named retail family config. |

The catalog has capacity 26, but only IDs 0–24 are initialized by `FUN_00458E70`. This is not evidence that index 25 is a valid Trooper or forklift ID. The forklift inverse case therefore remains: model directory present, type-name mapping absent in this initializer, physics family config absent. If code were manually given `forklift`, the named path builder would format it, but required group reads have no matching XML family; no fallback behavior was established.

## Named path builders and broker symmetry

`FUN_00493770(output, family_string)` starts with the literal `Vehicles/` and appends the string object's character data at `+4`, using its length at `+8` subject to the engine's maximum-string limit. It does not perform an alias lookup or normalize the family spelling. Examples are `Navara -> Vehicles/Navara` and `Trooper -> Vehicles/Trooper`.

`FUN_00493600(output, index)` starts with `Vehicles/Car`, formats the index using `%d`, and appends it. It therefore produces `Vehicles/Car0`, `Vehicles/Car1`, and so on.

The wrapper call order and helper pairings are:

| Parameter group | Named-family reader in `FUN_00493E30` | Runtime writer in `FUN_004938C0` | Static result |
|---|---|---|---|
| Dimensions | `FUN_0049B0C0` | `FUN_004940A0` | Matched group |
| Chassis | `FUN_0049B940` | `FUN_00494730` | Matched group |
| Steering | `FUN_0049C950` | `FUN_00495460` | Matched group |
| Engine | `FUN_0049CEF0` | `FUN_004958E0` | Matched group |
| Suspension/Front | `FUN_0049E970` | `FUN_00496D20` | Matched group |
| Suspension/Rear | `FUN_004A01D0` | `FUN_00498090` | Matched group |
| DamageParams | `FUN_004A1A30` | `FUN_00499400` | Matched group |
| Modifications | `FUN_004A32F0` | `FUN_0049A800` | Same 13-field group helper; source namespace depends on the call |

The two wrappers invoke the same eight group families in corresponding order. This establishes a parameter-record broker at the helper/group level. The named reader returns a status, but `FUN_0044ED50` does not branch on the `FUN_00493E30` return value; it proceeds to its overlay logic and calls `FUN_004938C0` unconditionally.

The `Modifications` helper reads or writes 13 values: front/rear SpringRate, DamperRate, AuxRollStiffness and RideHeight; plus Engine BrakeBias, CentreLSDBias, FrontLSDBias, RearLSDBias and GearRatioDiff. In `FUN_00493E30` it is first called on the base `Vehicles/<family>` namespace. The optional `FUN_00493FD0` call uses the separately generated `Vehicles/<family>/PlayerN` namespace and the same helper. The separation is in the path passed to the helper, not a different field group.

## Retail config completeness and overlay behavior

The read-only config audit used these retail inputs:

| Input | Size | SHA-256 |
|---|---:|---|
| `DataGame/vehicles.xml` | 757,388 | `a6762bb20999c7224c71b9f5d1d7edca55bcea147ff9f973300a8cf8d350aee0` |
| `DataGame/Modifications.xml` | 135,772 | `16df5a3a6b0c50c40f4ee74186e47b40294e6cb4ac11e0a3d7d20dafb8a5a65d` |

| Family | Type ID in initializer | Base `vehicles.xml` fields | Group counts | Base `Modifications/*` | Player1 overlay | Player2 overlay |
|---|---:|---:|---|---:|---:|---:|
| Navara | 7 | 147 | Dimensions 8; Chassis 16; Steering 5; Engine 45; Suspension 48; DamageParams 25 | 0/13 | 13/13 | 13/13 |
| Jump | 9 | 147 | Dimensions 8; Chassis 16; Steering 5; Engine 45; Suspension 48; DamageParams 25 | 0/13 | 13/13 | 13/13 |
| Trooper | none in initializer | 147 | Dimensions 8; Chassis 16; Steering 5; Engine 45; Suspension 48; DamageParams 25 | 0/13 | 13/13 | 13/13 |
| forklift | none in initializer | 0 | no named family root | 0/13 | 0/13 | 0/13 |

Trooper has all six direct base groups used by the reader. The base-family `/Modifications/...` values are absent in these XML inputs for the tested families. The optional player modification namespace is separate and complete for Trooper, Navara, and Jump. Static code shows the reader can return false when a field is missing, while the ordinary caller ignores the base reader's result. It does not prove what values remain in missing base modification fields before the overlay, or how another config source may affect them. The normal player overlay is not bypassed by the proposed whole-family design; it must be redirected to Trooper together with the base family.

## Trooper redirect feasibility and current gate

The low-level mechanism is feasible in principle: make the shared family name resolve to `Trooper`, then let the existing reader, optional player overlay, and CarN writer run. No EXE patch or individual float edits are justified by this phase.

The next safe action is observation only. The whole-family mutation is **not ready to run yet**, because the normal selected Navara's live `_CarClass` value and resulting string have not been captured. After that observation, a redirect must preserve both paths:

```text
base:    Trooper -> Vehicles/Trooper/*
overlay: Trooper/Player1 -> Vehicles/Trooper/Player1/Modifications/*
output:  participant 0 -> Vehicles/Car0/*
```

Changing only the argument at `FUN_00493E30` would leave the independently built Navara overlay unchanged. A later runtime plan should choose a single common family-source substitution before `local_4e8` and `local_4e0` are produced, or explicitly redirect both managed strings. Keep it process-local and restore the original state on exit; do not write a persistent EXE change. The string object has engine-managed storage, so do not overwrite `Navara`'s six inline characters with the longer word `Trooper`.

## One read-only x32dbg observation

Use the exact retail EXE hash above and a normal Navara local race participant. This only reads registers and memory.

1. Set a software breakpoint at `MRallye.exe+93E30` (`00493E30` at image base `00400000`).
2. When it hits, check `[ESP]`; the ordinary `FUN_0044ED50` call should return to `0044F0D2`. If the return address differs, record it and do not treat the hit as the target path.
3. Record `EBP` as the participant index. `FUN_0044ED50` loads its `param_1` into EBP at `0044EDD2`; the callee preserves EBP. For the first player this should be `0`.
4. At the callee entry, `[ESP+4]` is the family string object argument. The object layout used by `FUN_00493770` stores its character pointer at `+4` and length at `+8`. In x32dbg's expression/dump view, inspect `poi(poi(esp+4)+4)` as ASCII. Record the string and the value at `poi(esp+8)` as the VehicleParams destination pointer.
5. For the normal Navara control, expected observation is participant `0`, string `Navara`, with subsequent write path `Vehicles/Car0`. Do not change memory. A Jump control may be used only if Navara does not exercise the ordinary branch; expected table mapping is ID 9 -> `Jump`.

`FUN_0044ED50` also has an alternate class-source branch. The return-address check distinguishes the broker call site but not every earlier branch; record whether the stop was reached through the `FUN_004B0630` or `FUN_004AC660` source path if the debugger call stack/trace makes that clear.

## Reproduction and artifacts

Repository-root commands; corpus inputs are read-only and outputs are ignored:

```powershell
python tools/scanner/r_phys2_1_family_config.py `
  --corpora-root 'D:\Game\Master Rallye\corpora' `
  --output-dir '.research-output\r-phys2.1\config'
```

The focused static audit source is `tools/ghidra/RPhys21NamedFamilyAudit.java`; it targets only the ordinary race setup, family catalog, broker wrappers, group readers/writers, and their supporting accessors. Its text output belongs under `.research-output/r-phys2.1/static/` and is not committed.

## Current status

- No game was launched by the analysis process.
- No runtime mutation was made or prepared.
- No vehicle slot was created.
- No proprietary asset was modified or added to Git.
- Remaining blocker: one human read-only capture of the normal Navara family string and participant index at the ordinary broker call.
- Recommended next phase: after the observation, prepare one runtime-only whole-family substitution that redirects both the base family and its player modification overlay, then ask the human to run it.
