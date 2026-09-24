# Class-2 capacity and P0 gates

Retail frontend constructor `0x480A20` stores class capacities 7/7/11 at object `+0x20/+0x24/+0x28`. Navigation at `0x481F50` uses the active class capacity, so a later class-2 11→12 change is required to reach local 11 by normal next/previous input. `0x481E20` converts local 11 to absolute ID25 without a separate `<25` guard. `0x4819B0` indexes the allocated record25 for stats/unlock/preview selection, and its display-name selector for ID25 is separate from the resource name (prior B.1 finding).

`0x481950` iterates 12 positions (`i < 0xC`) to write `Frontend/VehicleSelect/Button%dXPos`. The loop uses a local key buffer, not an indexed twelve-button object array. Retail `VehicleSelect.xml` binds marker widgets only through `Button10XPos`; `Button11XPos` has no scene widget. The missing marker is a visibility/layout issue, not evidence of a buffer overflow in `0x481950`. It remains unproven that keyboard/controller focus, stats and marker behavior allow a twelfth entry to be selected cleanly without an additional UI change. No capacity/layout value was changed.

ID25 follows a real unlock case in `0x45A150` using flag 15. The selected-ID write in `0x4819B0` writes `-1` when locked, which prevents the preview mover from loading a model. This is a **P0 gating condition** until flag 15's retail state or a legitimate test setup is proven. Registry indexing itself permits ID25; the class-2 capacity and unlock result are separate gates.

| P0/P1 gate | Classification | Basis |
|---|---|---|
| registry capacity 26, record stride 0x34 | SAFE_FOR_ID25 after normal initialization | existing 26 allocated records; B.1 initializer ABI |
| class-2 navigation capacity 11 | PATCH_REQUIRED in future phase | `0x480A20`, `0x481F50` |
| ID25 unlock flag 15 | UNKNOWN for retail test state | `0x45A150`, locked branch in `0x4819B0` |
| twelve X-position keys | SAFE_FOR_ID25 in this loop | `0x481950` local string loop |
| twelfth scene marker/focus | UNKNOWN | no `Button11XPos` scene binding |
| preview index | SAFE_FOR_ID25 if record initialized and unlocked | `0x44C4C0`, only `-1` reject observed |
| race ID→CarType/physics indexing | SAFE_FOR_ID25 if normal record initialized | `0x44A510`, `0x44ED50` |
| dynamic render-name branch | UNKNOWN at P1 actor creation | `0x4B6B17` tests `Frontend/Active` |
