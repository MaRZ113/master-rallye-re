# ID25 SmallCarSheet runtime diagnostic

## Candidate

The ignored candidate is:

```text
.research-output/r5v_e0_1a/runtime-test/MRallye_slot25_trooper_smallsheet29_test.exe
.research-output/r5v_e0_1a/runtime-test/patch-manifest.json
.research-output/r5v_e0_1a/runtime-test/TEST_INSTRUCTIONS.txt
.research-output/r5v_e0_1a/runtime-test/binary-diff.txt
```

The base profile `trooper` reproduces the existing runtime candidate byte for
byte. Retail source SHA-256 is
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`;
Trooper baseline candidate SHA-256 is
`3022bdc6eb07d1e388f9c8ef693b83ce1c20c12c2c1a62719aad1cc59a1b1f13`;
diagnostic candidate SHA-256 is
`e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`.

Compared directly with the reproducible Trooper baseline, the diagnostic
executable differs at exactly one byte:

```text
file offset 0x28E2D5 / VA 0x68E2D5
initializer argument: 0x00 -> 0x1D
VehicleRecord[25].smallcarsheet_index: 0 -> 29
```

The class2 capacity, unlock override, registry hook, Trooper name, stats,
float values, model/physics/collision source selection and every other
executable byte are identical to the Trooper baseline. The profile value is
an input to the existing initializer call; 29 is not embedded as a separate
hardcoded patch branch. The manifest preserves the legacy `meta` field and
adds the semantic `smallcarsheet_index` field for this diagnostic profile.

## Expected observations

| Screen/item | Existing Trooper profile | Diagnostic expectation |
|---|---|---|
| Vehicle Select preview | Trooper | Trooper, unchanged |
| Stats/name | existing ID25 values | unchanged |
| Race 3D model, wheel, physics and collision | Trooper | Trooper, unchanged |
| Top-left image beside `1P` | owner reports Astero-like | Forklift frame 29 if the TimeDiffs hypothesis is correct |
| Bottom progress marker | generic hud-template frame 3 | unchanged |
| Race Results player image | selector 0 / Astero-like frame | Forklift frame 29 |
| Other vehicles | available in E0 report | unchanged |

The Race Results expectation follows a proven static producer/consumer path.
The top-left and progress expectations remain hypotheses until the human test
is performed. Record the exact result using the matrix in `TEST_INSTRUCTIONS.txt`.

## Runtime state

`WAITING FOR HUMAN RUNTIME TEST`. No game was launched in this phase. Keep the
source retail executable and `Data.sma` untouched. Launch the diagnostic
candidate against the same working game installation and Trooper data state
used for the successful R5V-E0 test; use the retail installation directory as
the process working directory.
