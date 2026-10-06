# Unlock layers and terminology

| Layer | Meaning | Retail owner / evidence | G.1 conclusion |
|---|---|---|---|
| Class reachability | Whether the player can navigate to T1/T2/T3 in Quick Race | `FUN_00480B60`, Quick Race mode state, `Progress/OpenedModes`, cup cheats | Separate from any individual CarID predicate |
| Per-vehicle availability | Whether a physical vehicle entry is enabled in Vehicle Select | `FUN_0045A150`, called at `0x004819CE`; reads `[record+4]` | ID-based switch to named progress flags, with global cheat bypasses |
| Mode/event eligibility | Whether a vehicle/class is valid for a chosen event or roster | Campaign/event records and mode setup; not centralized in the availability helper | Separate and partly unknown by mode |
| Runtime materialization | Whether the chosen identity resolves to model, wheel, physics and race actor | Vehicle registry and downstream runtime loaders | Already proven for ID26 in F.2/F.2f; not an unlock test |

Do not collapse these into one `unlocked` boolean. In particular, a stock
vehicle can pass its per-vehicle predicate while its class is unreachable, and
a selectable player vehicle is not thereby eligible for every authored event
or AI pool.

## IDs and selector domains

`FUN_0045A150` receives a pointer to a `VehicleRecord`; its input is the
absolute physical `CarID` at record offset `+0x04`, not class-local index.
Vehicle Select first maps `(class, local index)` to an absolute ID, then looks
up the corresponding registry record and calls the predicate. R5V-F maps T1
local7 to physical ID26, while keeping the two identity domains separate.

The native registry initializes IDs 0..24. Its allocation reserves an extra
default record at ID25 and the availability switch has a Bonus2 case for ID25,
but pristine retail has no initialized named stock vehicle in that record.
R5V-E supplies Trooper at ID25. ID26 is a later sparse extension and falls
through the pristine helper's default-available branch; G.1 intentionally
replaces that one Vehicle Select decision with a stock T1 predicate.
