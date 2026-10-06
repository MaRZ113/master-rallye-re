# R5V-G.1 human runtime handoff

Status: **READY FOR HUMAN RUNTIME**. This is a locked-state comparison, not a
request to fake progression or edit a save.

Use an isolated retail game copy containing the already-validated F.2f
Mercedes runtime assets/data and the generated G.1 candidate EXE. Preserve the
original install and keep one genuinely fresh profile plus one existing
naturally progressed profile. Do not modify `PlayerState.xml`, use Broker
Editor writes, or enable unlock cheats for the comparison.

1. With the fresh profile and cheats off, open Quick Race Vehicle Select.
   Confirm T1 is reachable; T2/T3 are not. Verify stock ID3 / T1 CupCar1 is
   locked and Mercedes ID26 receives the same locked state. The native locked
   path may replace the vehicle-name presentation with its lock text, so do not
   require `MERCEDES / ML-320` to remain visible while locked. Capture
   `g1-fresh-vehicle-select`.
2. With a naturally progressed profile where
   `Progress/UnlockedCars/T1CupCar1=True`, verify both stock ID3 and Mercedes
   ID26 are selectable. Capture `g1-progressed-vehicle-select`.
3. In the progressed profile select Mercedes local7. Confirm the UI still says
   T1 / `MERCEDES` / `ML-320`, then launch a short offline Quick Race.
   Capture `g1-mercedes-race`; verify `Race/Car0/CarID=26`, class 0,
   `CarType=Mercedes`, and `WheelType=Mercedes`.
4. Switch to a stock vehicle and back if convenient. Confirm ordinary stock
   selection still behaves normally and no `GALOCAL UNKNOWN` returns.

If no naturally progressed profile with T1 CupCar1 is available, stop after the
fresh comparison and preserve that evidence. Do not manufacture the flag. The
progressed comparison can be completed after normal gameplay opens the stock
vehicle.

For each Observatory JSON capture, run:

```powershell
py -3 tools/r5v_g1_unlock.py path\to\capture.json
```

The checker summarizes Broker values and reports missing/duplicate values as
UNKNOWN/AMBIGUOUS. It does not verify rendered text/icon, native hook execution,
or actual selectability; the human must visually verify those points.
