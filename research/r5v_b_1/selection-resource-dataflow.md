# Selection and resource dataflow — retail

All established edges below are `RAW_GHIDRA_SUPPORTED`; no ReAgent semantic reconstruction was permitted.

1. Screen object holds class index at `+0x10` and class-local indices at `+0x14/+0x18/+0x1c`. `0x481E20` adds base 14 for class 2, so local 11 maps to absolute ID25. `0x481E50` performs the inverse without a 24 cap.
2. `0x4819B0` calls `0x481E20`, computes `singleton+4+ID*0x34`, and passes that record to unlock switch `0x45A150`. The switch has a real ID25 case using progress flag 15. If unlocked, `0x4819B0` writes **numeric ID25** to `Frontend/VehicleSelect/CarModel` through `0x4D8000`; if locked, it writes -1. The selection object's local index and this config integer are the exact observed selected-ID carriers.
3. `0x47BB00` reads `Frontend/VehicleSelect/CarModel` and stores its integer into `MasterRallye/PlayerT3Car0` in a class-2 branch. This proves one campaign transfer, not the requested quick-race/race model lookup.
4. `0x443D40` constructs `Vehicles/<name>/car` with a name obtained via `0x4D0570`, but the Ghidra export reports zero direct callers. No raw path from `CarModel=25` or record `+0x20` to this function was established. Neighboring wheel/complete resource strings exist; they do not prove their ID/name providers.
5. `0x4AD840`, previously suspected as general selection plumbing, writes `FrontEnd/Network/selectedCar`; treating it as preview registration would be inaccurate. `0x436700` remains semantically untyped.

**Open edges:** `CarModel` → preview object → `complete.dx`; selected quick-race ID → race setup/model resource; record `+0x20` → `0x443D40` name source; model name → `wheel.dx` and textures. Thus an ID25 initialized with `Astero` is not yet proven to reach Astero preview or race assets. The unlocked/locked UI path should be distinguished: current record25 lacks a stored ID and is not a valid test object as-is.

Display name: the locked branch of `0x4819B0` selects localization group 6/index 26 for ID25; the retail English table's 26th entry is `Forklift` (prior R5V-B evidence). This is a selector observation, not proof of the active-language rendered text. The unlocked branch uses separate manufacturer/model localization groups and ID-based lookup; its ID25 result is not established. The localization selector is distinct from record `+0x20` internal resource name.
