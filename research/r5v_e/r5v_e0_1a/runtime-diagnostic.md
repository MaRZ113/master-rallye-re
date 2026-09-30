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

## Runtime observations

| Item | Owner-reported result |
|---|---|
| Top-left image beside `1P` | Forklift frame 29 |
| Bottom progress marker | Aquamarine, unchanged |
| Race Results player image | Forklift frame 29 |
| Trooper gameplay | Normal and unchanged |

The owner reports **FULL PASS** for the selector diagnostic. This confirms that
`VehicleRecord[25] + 0x1C` controls the observed top-left participant icon as
well as the separately proven Race Results icon. The progress marker did not
follow the SmallCarSheet selector.

The game was not launched by the analysis tooling. Retail executable and
`Data.sma` source files remain untouched. The original ignored candidate and
manifest remain unchanged.
