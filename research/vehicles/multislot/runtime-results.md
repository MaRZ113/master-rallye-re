# R5V-I runtime results

## R5V-I.0 — second sparse slot proof

**FULL PASS / CLOSED** for the ID27/T2-local7 slot and two-addon coexistence.
This closes the runtime slot question; it does not treat I.0's Navara donor
alias as a second independent vehicle.

All four capture JSON records identify the same I.0 executable image:

* Profile: `i0-two-addon-slots-id27-t2-diagnostic`
* EXE SHA256: `50ff267d2758c1ff894d91bcdafd7dba4a2fa278d678a075e7767120727abbea`
* EXE size: 3,121,214 bytes
* Observatory: 0.2.2-beta
* Process: PID 35124 for all four pairs
* Capture root: `MasterRallye-Observatory-0.2.2-beta/observatory-data/captures/2026-10-08`

| Capture | JSON SHA256 | Raw sidecar SHA256 | Evidence |
|---|---|---|---|
| `20261008-002154_I0_1-vehicleselect` | `139cb0ff0bd903b4e9f75c03a41ea1ef45584f08d071df59f54bcca5416128cf` | `b692a562483cdd072ecb8e0a8f3fa7da6a44325df2416b5932021e2c3ff617e9` | Vehicle Select CarModel 27, T2-local7 identity; human view confirms T2_Car8 preview/navigation |
| `20261008-002342_I0_3-Race` | `094beb72d33689d821a0de518d65f875a5a904d07bfca073c2736e4b5606870a` | `4a3c59e8e05fbc10d87b5e1a4bdd70196958401d623ed0118949ee32fe6a766f` | Single-player active race; Car0 ID27/T2/human, Navara model/wheels, cyan canary; AI IDs 7/11/13 |
| `20261008-002906_I0_plus_splitscreen-menu` | `6fb35638b1bafd8a42b7b7f13aebe86b81e6e415e21bd52f0570d14329384271` | `bdc8f61128fe24f5443cb11f67b8f5e5e96140083583a094904ab49f53da4034` | Menu selections show IDs27 and 26; stale/inconsistent race fields are not actor proof |
| `20261008-002944_I0_plus_splitscreen-race` | `80e4c161533e78ee619fefd01405a1b54098a03afd4291a8efc0ccf53b0f6bfa` | `5af6cf41c8e505daa9272bf69169ce758363a3a055eda9956a59086048cdc04c` | Active SplitScreen: Car0 ID27/T2 human; Car1 ID26/T1 human; AI IDs11/9; owner confirms both views work |

I.0 runtime classifications:

* T2 local7 / physical ID27 frontend slot — `CONFIRMED_BY_RUNTIME`.
* Physical ID27 player actor — `CONFIRMED_BY_RUNTIME` (`Race/NumCars=4`,
  `Race/NumPlayers=1`, `Race/Type=2`, `CarClass=1`, `DriverID=30`).
* ID27 -> T2 and T2 local7 != ID14 — `CONFIRMED_BY_RUNTIME`.
* ID26/T1 and ID27/T2 as distinct simultaneous SplitScreen human vehicles —
  `CONFIRMED_BY_RUNTIME`.
* ID27 donor model/wheels/physics movement, HUD icon and progress marker —
  `HUMAN_RUNTIME_PASS`, as reported by the owner.
* The owner did not report a complete stage/results, explicit collision/damage
  qualification or full cleanup pass for this exact I.0 run; none is claimed.
* ID25/Trooper slot and frontend mapping remain present, but the Trooper model
  payload is absent from this package.

## R5V-I.1 — authored independent-family T2 qualification

**CORE FAMILY ROUTING AND NATURAL AI MATERIALIZATION: CONFIRMED_BY_RUNTIME.**
The exact candidate and six rehashed capture pairs are summarized in
[`i1-runtime-evidence.json`](i1-runtime-evidence.json).

The player-race capture reports Car0 physical ID27, class T2, player type,
`CarType=R5VQualifier`, and `WheelType=R5VQualifier`; the owner reports the
normal player-family runtime test. A separate natural Quick Race capture
records `Race/NumCars=4`, `Race/NumPlayers=1`, `Race/Type=2`, with ID27 as T2
AI Car3 (`DriverID=1`) and `CarType`/`WheelType=R5VQualifier`. The candidate
manifest lists the natural T2 pool `[7,8,9,10,11,12,13,27]` and
`id27_forced_participant=false`. This confirms natural AI participant
materialization, not a completed AI race lifecycle or final position.

Two public runtime-release gates remain bounded: the Vehicle Select scene
re-entry mismatch and the new race marker color. The re-entry captures retain
`Frontend/QuickRace/Car0=27` in both states, while one displays Navara at
T2/local0 and the control displays R5VQualifier at T2/local7. The exact native
writer is unknown; the later Navara capture does not prove automatic commit.
The captured ID27 marker is white `[1,1,1,1]`; the SDK request for magenta
`[1,0,1,1]` has not been runtime-tested.

* Profile: `i1-id27-r5v-qualifier-independent-t2-family`
* Source retail SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
* H.2 parent SHA256: `de5e81c0b126619574834f25ac941cd491139235fd2f89086d8e125f063dcac9`
* Candidate SHA256: `90abfbf9825f1cc7acebb3a1a2811a179e6474f2406433854e1ffdbc60bdd955`
* Candidate size: 3,121,214 bytes
* Package: `.research-output/vehicles/multislot/i1/runtime-package`
* Package status: automated `VERIFIED`; 243 resource inventory entries.
* Tracked derived patch inventory:
  [i1-candidate-manifest.json](i1-candidate-manifest.json) (81 sites with
  exact offsets, lengths and before/after hashes; no raw EXE patch bytes).
* Vehicle Select overlay SHA256:
  `0b8c61efd2959a5b3b5dcef0d3810c2b445e021c465816627e87b9e3da2b4490`
* Separate `R5VQualifier` family: 98 DX/DXT resources; model hashes are in
  the generated package manifest. `paintjeep-tga.dxt` is recolored magenta
  from source SHA `1d25b132568e8f30ae7ec8049de2289ec95727051df18868693fb251f5f9436c`
  to `76e3e81a7bf9dd32c7d96a1131d3343e4586459bbbc0d52af7f783c3a1e6d44d`
  while retaining its 20-byte header and 16×16 dimensions.
* `DataGame/vehicles.xml` has 147 Navara-derived family rows under
  `Vehicles/R5VQualifier`; `DataGame/Modifications.xml` has 26 cloned rows.
  No semantic physics delta or unique collision hull is claimed.
* ID27 remains physical ID27 / class T2 / local7. ID26 Mercedes, ID25 mapping,
  T2 AI pool membership, audio profile7, ID10 unlock oracle, native DriverID
  selection and participant count are preserved.

The original pre-runtime handoff and protocol are retained in
[i1-qualification.md](i1-qualification.md) as historical provenance. Its
runtime checklist is superseded by the verified captures summarized above.
