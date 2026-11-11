# G2 human test handoff

Candidate: `.research-output/r-mod3/g2/first-integrated-candidate-g2/first-integrated-candidate-g2.zip`.

Use a disposable copy of the supported game installation. Verify the retail executable SHA256 is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` before and after the test. Keep an existing renderer wrapper untouched. Do not overwrite another `dinput8.dll` proxy; if there is a conflict, use a clean test copy and report it. The package itself is verified not to contain `MRallye.exe`, `Data.sma`, vehicle assets, or `d3d8.dll`.

1. Copy the package files beside the original `MRallye.exe`, preserving the existing graphical `d3d8.dll`. Copy one profile from `profiles/` to `MRallyeRandomizer.ini`.
2. First install `safe-stock-v3.ini`; launch normally and confirm ordinary Quick Race selection and startup still work.
3. Install `forced-id12.ini`. Enter Quick Race Vehicle Select. Confirm the visible identity and `Frontend/VehicleSelect/CarModel` are ID12. If arrows remain active, test a left/right change and check whether displayed model/name still agree with the intended forced vehicle. Start only if the screen remains coherent. In the race verify `Frontend/QuickRace/Car0=12`, `Race/Car0/CarID=12`, `CarClass=1`, `PlayerType=human`, and Mercedes-independent native stock family identity for ID12 (Navara). Record `CarType`, `WheelType`, and DriverID rather than inferring them from the menu.
4. Install `random-t1.ini`. Enter the same screen and record the selected physical ID; it must be 0–6. Remain on the screen, redraw/focus without leaving, and confirm no reroll. Start and verify the visible and Race IDs agree. A fresh Vehicle Select re-entry may choose a new car, but it is not required to differ.
5. Optionally repeat with `random-t2.ini` and `random-full.ini` after the first two tests pass. Confirm strict class for T2 (7–13) and Full stock IDs (0–24).
6. Optionally run `g1-seven-ai-t1-regression.ini` to check that G1 duplicate-capable opponent behavior remains composed. Do not treat G2 synthetic tests as a repeat of G1 gameplay evidence.
7. Remove only this mod's `dinput8.dll`, `MRallyeRandomizerRuntime.dll`, `MRallyeRandomizer.ini`, and its log to disable the candidate. Keep all game files and the renderer unchanged.

For each run record candidate ZIP hash, log, visible menu identity, `VehicleSelect/CarModel`, `QuickRace/Car0`, `Race/Car0/CarID`, CarClass, PlayerType, DriverID, CarType and WheelType. The key failure condition is any disagreement between the selected/displayed vehicle and the race vehicle. Do not continue to broader modes or campaigns; G2 changes only Quick Race player 0.
