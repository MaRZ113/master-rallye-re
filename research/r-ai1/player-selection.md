# Player selection into an ordinary race

**CONFIRMED_BY_EXE**, exact pristine build; game execution pending for this phase.

1. Selection-screen member +0x10 stores native class 0/1/2. Members
   +0x14/+0x18/+0x1C store independent class-local choices.
2. `0x481E20` converts class/local to absolute ID: local, local+7, local+14.
   `0x481E50` performs the inverse and updates
   `Frontend/VehicleSelect/VehicleClass`. These are not AI pool choosers.
3. Entry `0x481340` is the selection acceptance function. Its call at
   `0x481391` returns an absolute ID into EDI at `0x481396`.
4. `0x481417` writes that ID to Race/CarN/CarID through `0x4ACAF0`, using the
   screen participant index +0x2C. `0x481435` derives class from registry object
   `+0xC+ID*0x34` and writes CarClass through `0x4ACC10`.
5. The Quick Race branch at `0x481456` stores the same **absolute ID** in
   Frontend/QuickRace/Car0 through `0x4ADF50`. `0x47B780` restores it through
   `0x4ADFB0 -> 0x4ACAF0` and derives class again from the registry; there is
   no second local-to-absolute conversion on this restore.
6. Ordinary preparation `0x449D40 -> 0x449E90 -> 0x44A320` sets one player's
   DriverID30 and configures each existing participant. `0x44A450` assigns
   human/AI types; `0x44A510` derives family and wheel identity from each ID.
7. `0x44ED50 -> 0x493E30 -> 0x4938C0` reads the selected named Vehicles family
   and publishes its own Vehicles/CarN parameters. `0x4B6A00` on the
   Frontend/Active path loads the participant's CarType body and WheelType
   wheels. See [downstream audit](downstream-consumers.md) for lifecycle gates.

`0x45A150` marks IDs0..2, 7..9 and 14..17 available by default. Player ID14
therefore requires neither bonus unlocks nor a custom vehicle. Its frontend
local index is T3/local0. The patch does not alter this path or player identity.
