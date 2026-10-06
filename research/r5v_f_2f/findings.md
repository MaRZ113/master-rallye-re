# R5V-F.2f — Mercedes frontend identity writers

## Status

**CLOSED / CONFIRMED_BY_RUNTIME.** The owner reports the exact F.2f frontend test passed. Race Options displayed `MERCEDES` and `ML-320`; leaving and re-entering the screen preserved both fields, and no `GALOCAL UNKNOWN` returned. The candidate preserves the Mercedes physical identity and its already-confirmed core gameplay path.

## F.2e runtime evidence carried forward

The owner reports that T1 local7 remains physical ID26, Vehicle Select shows `MERCEDES` / `ML-320`, the Mercedes preview and textures render, the displayed stats are 4/3/6/5, and a short race loads the Mercedes model with normal steering, acceleration, braking, suspension, grip, collision and damage. ID25/Trooper remains separately selectable. This is a **CORE GAMEPLAY PASS** for the exact F.2e candidate, not a full stage/results/return lifecycle claim.

The three paired Broker captures below all identify executable SHA-256 `1fb0a1f1ba02cd05fa25f0c94558cf1b281fd12affcdc37bb3c1ca538e6c65af` and the same process. Each JSON `source.raw_sha256` matches its `.dump.bin` sidecar hash.

| Capture | Relevant Broker state | Evidence |
|---|---|---|
| `20261005-233544_retail-merc-id26-menu` | `Frontend/VehicleSelect/CarModel=26`; `Frontend/QuickRace/CurrentVehicleString=TOMMEK DIRTBEAST` | CONFIRMED_BY_RUNTIME / CORPUS |
| `20261005-233655_retail-merc-id26-raceoptions_unknown` | `CarModel=26`; both Quick Race identity strings are `GALOCAL UNKNOWN`; `Race/Car0/CarID=26`, class 0 | CONFIRMED_BY_RUNTIME / CORPUS |
| `20261005-233755_merc-id26-race` | `CarModel=26`; `CurrentVehicleString=MERCEDES ML-320`; manufacturer remains unknown; `Race/Car0/CarID=26`, class 0, `CarType=Mercedes`, `WheelType=Mercedes`, colour `[1,0,0,1]` | CONFIRMED_BY_RUNTIME / CORPUS |

The last capture proves that the red record-colour canary and runtime identity still belong to physical ID26. The Race Options display defect is presentation-only; changing CarID, class, runtime type, wheel type, or the registry record would regress the proven vehicle.

## F.2f owner runtime closeout

The owner subsequently confirmed that the F.2f candidate showed the correct
manufacturer/model identity in Vehicle Select, Quick Race, and Race Options,
including after a second Race Options entry. The stock-vehicle switchback and
ID25/Trooper selection remained correct. The existing capture set establishes
`CarModel=26`, active selected ID26, `CarType=Mercedes`, `WheelType=Mercedes`,
class 0, and the red ID26 colour canary. The owner did not report a full
stage/results/frontend-return run for this exact candidate, so F.2f is closed
for frontend identity and core gameplay only; it is not a full lifecycle claim.

Exact candidate recorded by the preceding R5V-F.2f validation: SHA-256
`1fbb3489208de9bc0af3802902a8611ea9a149c245031d1563960bd91b430c14`,
3,121,214 bytes. The later R5V-G.1 profile derives from the same pristine
retail source and carries this presentation fix forward.

## Writer result

The retail Ghidra 12.1.4 string-reference export lists every code reference to these exact Broker keys:

- `Frontend/QuickRace/CurrentManufacturerString`: one reference, in `FUN_0047A540`.
- `Frontend/QuickRace/CurrentVehicleString`: two branch references in `FUN_0047B040` and one reference in `FUN_0047A540`.

`FUN_0047A540`, called by `FUN_00479BB0`, is the Quick Mode Select / Race Options refresh path. It obtains the selected physical ID from `FUN_004ADFB0`, retains it in ESI, looks up group `0x33` for the manufacturer field and group `0x34` for the vehicle/model field, then writes each resulting string to its respective Broker key through the existing string/Broker construction path. ID26 is passed directly to both stock localization lookups, which return `GALOCAL UNKNOWN`.

`FUN_0047B040`, called by `FUN_0047AB30`, is a separate Quick Race summary refresh path. Its three group-`0x35` contexts populate combined vehicle text. The existing F.2e wrapper already returns `MERCEDES ML-320` for ID26 in this path. It does not reference or write `CurrentManufacturerString`, which explains why the active-race capture has a correct combined name but retains the previous manufacturer value.

The three symptoms classify as **STALE VALUE** at the early Vehicle Select capture, **INDEPENDENT LOOKUP** in the Race Options writer, and **SPLIT IDENTITY PATH** between manufacturer/model and combined Quick Race text. The captures and references show no evidence of a correct ID26 string being written and then overwritten with UNKNOWN; **POST-OVERRIDE OVERWRITE is not supported**.

Groups `0x33` and `0x34` are independently used by the already-patched Vehicle Select manufacturer and model controls. Their native split is therefore retained: Race Options gets manufacturer `MERCEDES` and model `ML-320`. The combined `MERCEDES ML-320` remains the group-`0x35` Quick Race form.

See [frontend-writer-map.json](frontend-writer-map.json) for addresses and [runtime-handoff.md](runtime-handoff.md) for the human gate.
