# Driver profile and vehicle coupling

`Drivers.xml` contains10 Drivers/Driver0..9 `gaIContDriverParams` profiles.
The inspected profile data has no VehicleID/CarClass restriction:
**CONFIRMED_BY_CORPUS**. The chooser's separate driver pool is
**CONFIRMED_BY_EXE**; it is not selected through the vehicle's class/local table.

The factory beginning `0x42AA3D` reads Race/CarN/DriverID and clamps to0..9.
Its single controller-init CALL at `0x42AAD6` reaches `0x42CDB0`, which binds
Drivers/DriverN and this participant's CarN, Controller/CarN and Finished state.
No mandatory ID14/driver pairing or T1/driver pairing was found.

`0x42D0D0` reads **Vehicles/CarN** Engine/Gears, Gear%d, GearRatioDiff,
RevLimit and Dimensions/WheelRadiusFront to compute the participant's own
physical ceiling, then combines it with the driver profile's limit. This is
per-vehicle initialization, not player-family substitution.

## Race-class balance assumption retained

`0x42CFF1` pushes participant0 before the CarClass getter CALL at `0x42CFFA`.
The AI object caches this **player/race class** at+0x44. `0x42E020` initializes
its float+0x3C to1.4/1.3/1.2 for classes0/1/2 (default1.5), with further
difficulty-dependent reductions using+0x40.

This field reaches a floating calculation at `0x42DEC9` in `0x42DDE0`, alongside
vehicle/curve-related terms passed to `0x5C2F80`. Assembly contains stack FP
arguments incompletely represented by the decompiler; the precise steering/
speed-control formula is not claimed. This phase does not reconstruct steering.

The T1 target therefore uses its own vehicle ceiling with the existing T3
race balance scalar. Retaining this scalar keeps the race rules and two AI
controls unchanged. It does not force the target ID/class back to T3.

**STRONG_HYPOTHESIS:** a stock driver0..9 can initialize the stock T1 target in
this T3 race. **UNKNOWN:** its driving quality/stability through finish, which
must be observed in the controlled human test. Do not turn profile independence
or successful initialization code into a runtime result.
