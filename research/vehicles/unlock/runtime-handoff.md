# R5V-G.1 correction — human runtime handoff

Use an isolated retail install and a disposable genuinely fresh profile. Stage
the exact candidate EXE and its loose `VehicleSelect.xml` overlay together;
keep the original game EXE and retail data untouched. Do not use a progressed
save for the locked comparison, and do not enable either car-unlock cheat.
Use the already runtime-qualified Mercedes DX/DXT package from the F.2e/F.2f
test setup unchanged; this correction contains no asset changes or recook.

The pair prepared for this test is:

* EXE profile `mercedes-g1-stock-t1-cup-car1-unlock-locked-state-correction`,
  SHA256 `3346eb00442b88cca3f76f7a65606ca56006c5b981acdbf0ee4ad16412e5b055`.
* Loose scene overlay SHA256
  `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`, staged
  at the game's normal relative path `DataScene/FrontendScreens/VehicleSelect.xml`.

## A. Stock locked ID3 oracle

1. Launch the staged candidate with the fresh profile.
2. Enter T1 Vehicle Select and highlight local3 / stock ID3 (Terrano).
3. Note both locked text lines, the small slot art, and the missing main model.
4. Try the normal accept action. Record whether it commits or opens Vehicle
   Setup; if it does, stop and capture the unexpected behavior.

## B. Locked Mercedes ID26

1. Highlight T1 local7 / ID26.
2. Confirm the first line is `CAR LOCKED`, the second line matches the ID3
   requirement exactly, the thumbnail uses the same locked state, and the main
   Mercedes preview is absent.
3. Try the same accept action. The locked Mercedes must remain uncommitted and
   must not enter Vehicle Setup or a race.
4. Capture a Broker snapshot labelled `g1-locked-id26` if convenient. The
   visible interaction is the deciding evidence, not `selectedCar` alone.

## C. Naturally unlocked Mercedes

Use a naturally progressed profile with `T1CupCar1=True` and cheats off.

1. Confirm ID3 and ID26 are both selectable; ID26 shows normal frame/model.
2. Enter Vehicle Setup. The visible name and
   `Frontend/VehicleSetup/CarName`, if captured, should be `MERCEDES ML-320`.
3. Return to Quick Race and Race Options once; existing Mercedes identity
   should remain `MERCEDES ML-320` on Quick Race and `MERCEDES` / `ML-320` on
   Race Options.

## D. Short race regression

Run one short offline race as Mercedes. Confirm normal model, textures, controls,
and handling. Broker identity should remain `Race/Car0/CarID=26`,
`CarClass=0`, `CarType=Mercedes`, and `WheelType=Mercedes`; the intentional red
ID26 colour canary remains `1,0,0,1`. This is a regression smoke, not a new
full-stage/results qualification.

Preserve the candidate EXE SHA, overlay SHA, captures, and any concise notes.
Do not claim full lifecycle completion from this short test.
