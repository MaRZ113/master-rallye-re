# R5V-E0.2 Vehicle Select P0 test

## Candidate

Use the existing isolated installation and executable that already passed
the R5V-E0 ID25/Trooper check. Keep that executable unchanged. In that
separate test installation, use this candidate as its `Data.sma`:

```text
research-output/r5v_e0_2/runtime-test/Data.sma
SHA-256 BB3C69CB97ADD992BF261F64C6ABAFAABAB946AB5CAE7E496D2D486C31A18020
```

The archive was built from the retail extracted tree with one override:
`DataScene/FrontendScreens/VehicleSelect.xml`. Do not use the user's main game
directory as the test install. To restore the test install, put back its
baseline `Data.sma`.

The candidate adds `T3_Car12` at local index 11 / absolute ID25 using frame 5,
the existing Astero diagnostic donor. It does not include Trooper-specific
art, make an executable patch, change registry capacity, change T1/T2, or
alter Trooper model/physics/collision configuration.

## Test steps

1. Launch the isolated, already working ID25/Trooper test installation with
   this candidate `Data.sma`.
2. Open T3 Vehicle Select and navigate to local index 11 / ID25.
3. Confirm a carsheet icon is visible in the twelfth T3 slot. For this
   diagnostic, the expected artwork is the Astero donor frame, not Trooper.
4. Move away from ID25 and back several times; switch to T1/T2 and return to
   T3; leave and re-enter Vehicle Select.
5. Confirm the selected ID still reaches ID25, the screen remains stable, and
   existing vehicle icons stay in their original slots. Do not start a race;
   race rendering and progress-marker colour are outside this P0.

## Report one result

- **FULL PASS:** frame5 is visible at T3 local11 / ID25 after repeated
  navigation and re-entry; existing entries remain correct.
- **COSMETIC PARTIAL:** the icon binds to the right slot and remains stable,
  but the donor position/layout needs adjustment.
- **FAIL:** icon absent/wrong slot, crash, navigation instability or existing
  icons displaced.

Also report whether the correct ID25/Trooper preview/name/stats remain selected
while the donor icon is shown. This confirms that the scene icon is an
independent frontend channel. The test result should be recorded as
human-reported unless a reproducible capture/log is provided.
