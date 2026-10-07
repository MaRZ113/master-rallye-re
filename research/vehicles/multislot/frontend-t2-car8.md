# R5V-I.0 Vehicle Select T2_Car8

The overlay is deterministically generated from the exact retail
`DataScene/FrontendScreens/VehicleSelect.xml` (SHA256
`ec7fd6372fe5008b1039eb0e09890ef3b37396dad1581568af439cbb611b58e1`) through
the already qualified G.1 overlay and appends one `T2_Car8` Egg cloned from
stock `T2_Car4`. All existing G.1 scene bytes remain intact.

The appended slot uses X ID 7 / Y ID 1 and
`Frontend/VehicleSelect/Button7XPos`. It retains the native T2CupCar1,
UnlockCars and UnlockAll button gate. Locked artwork uses frame 15; the
unlocked diagnostic image uses frame 23, the stock Navara carsheet frame.
This is donor art for the slot test, not ID27 authentic artwork. The T2 class
itself must be available through normal progression; the overlay does not
unlock the class.

The deterministic overlay SHA256 is
`0b8c61efd2959a5b3b5dcef0d3810c2b445e021c465816627e87b9e3da2b4490`.
The runtime package stages it at
`DataScene/FrontendScreens/VehicleSelect.xml` beside the exact candidate and
the already qualified H.2 resource set. Package verification hashes the
effective staged scene and compares it with a fresh deterministic rebuild.

The existing `T2_Car8` found in the demo 9.3.1 scene is evidence that a later
frontend authored this slot; it is not evidence that retail instantiated an
ID27 vehicle or supplied an independent T2 model.
