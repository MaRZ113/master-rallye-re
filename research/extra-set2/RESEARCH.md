# EXTRA-SET2 research — tyres on the GENERAL page, native PS2/PC appearance switch

Status: research only, nothing implemented. Inputs: retail EXE `bf8aef32…`, EXTRA-SET1 sources
(`src/native/rmod1/extra_options_runtime.cpp`), owner Broker captures
`Master Rallye Pristine/Release-Assets/Observatory-0.3.1-beta/observatory-data/captures/2026-11-08`
(`veh_setup-general`, `veh_select`).

## Vehicle Setup pages

| Page | Scene | Screen class vtable (tick / init) | Command call to 0x45D930 | Broker group |
|---|---|---|---|---|
| FRONT SUSPENSION | `VehicleSetup.xml` | — | — | `Frontend/VehicleSetup/FrontSuspension/*` |
| REAR SUSPENSION | `VehicleSetup2.xml` | — | — | `Frontend/VehicleSetup/RearSuspension/*` |
| GENERAL | `VehicleSetup3.xml` | `0x690B4C`→`0x4830C0` / `0x690B50`→`0x482F30` | `0x483151` | `Frontend/VehicleSetup/Engine/{BrakeBias,CentreLSDBias,FrontLSDBias,RearLSDBias}` + `General/Screen*` |
| GEARBOX | `VehicleSetup4.xml` | `0x690B70`→`0x483D20` / `0x690B74`→`0x4839D0` | `0x483E23` | `Frontend/VehicleSetup/Gearbox/*` (EXTRA-SET1 host) |

The GENERAL init refers to `Frontend/VehicleSetup/General/Screen` (`0x48305B`); its text updater is
`0x4831A0` (`Engine/BrakeBiasText`). The GENERAL scene holds 4 sliders, one multistate (screen
selector), 2 arrows, 8 standard buttons, i.e. the same component set EXTRA-SET1 cloned on GEARBOX.
The same Init/Tick/Command hook shape used on GEARBOX applies unchanged to GENERAL.

The retail text tables still contain `TYRE TYPE` (`0x6CFCF8`, English) and `TYRES` (`0x6CD6C0`),
and the AI keeps `gaIContDriverLookUp :: TyreType %d Selected` (`0x42E0E0`, stores the index at
controller car `+0x74`). A tyre selector was planned by the original developers; the label can come
from the native localized text table instead of a new string.

## Tyre families

Broker `Vehicles/Tyres/*` holds `{tarmac,harddirt,gravel,grass,mud}0..4` (5 records × 12 fields,
EXTRA-SET1 audit) plus single records `Slicks`, `Grooves`, `Wets`, `Dirts`. Stock `TyreType` values
across the 39 car prefixes: `harddirt` 62 axles, `Slicks` 10 (Pajerostripe, Frontera, Kamaz, Bowler,
Custom), `tarmac` 2 (Landcruiser), `FrontTest`/`RearTest` 4 (Megane, SeatBuggy; no such record).
Readers: TyreType registration `0x490660`, string reader `0x490720` → `Vehicles/Tyres/<name>/<field>`
loader `0x490920`, second loader `0x491120`; suspension struct readers `0x496D20` (front) and
`0x498090` (rear) are the EXTRA-SET1 publication hooks (`0x493935`/`0x493942`).
Open: how a family name resolves to the per-surface record at runtime (the `harddirt` name has no
`Vehicles/Tyres/harddirt/` record of its own, and `FrontTest` has none at all). EXTRA-SET1 only
proved the publication; solver consumption needs a runtime probe (wheel tyre-parameter pointer or
grip A/B on one surface).

EXTRA-SET1 tyre state is already per physical CarID (256 slots) and not tied to the three livery
cars; its limits are the Quick Race single-player scope and the GEARBOX host page.

## Appearance (PS2 / PC)

The D3D8 proxy has PS2 fleet models for 26 families in `PS2Vehicles` (incl. Forklift, Wooldand) (`RaceFleet=1`,
`FleetAllCars=1`, `FrontendModel=1`). EXTRA-SET1 asks dinput8 through `MRExtraVisualV1/V2`
(`extra_options_graphics.hpp`); V2 returns 1 = PC bundle, 2 = PS2 bundle, 3 = PS2 geometry with PC
textures. Both exports only answer for the three families in `research/extra-set1/vehicles.json`
(`SeatBuggy`, `megane`, `Tata`). A generic two-state PS2/PC choice needs a CarID → family map for the
25 retail IDs plus SDK IDs, not per-car authoring; texture-transfer variants stay per car.
Known renderer limit (owner, 2026-11-02): switching depends on `ReflectionMode=4`.

Vehicle Select (`veh_select` capture): class multistate `Frontend/VehicleSelect/Vehicle` + arrows,
car carousel `Button0..11XPos`, preview `Frontend/VehicleSelect/CarModel`. Screen vtable tick
`0x690B18`→`0x481340`, init `0x690B1C`→`0x480B60`; class arrows updater `0x4819B0`. The large
preview reads the menu car, so an appearance row here gives immediate visual feedback.
