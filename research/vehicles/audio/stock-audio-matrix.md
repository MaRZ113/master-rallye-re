# Retail stock engine-audio matrix

The source is pristine retail `MRallye.exe`, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
The table records resource family, raw scalar bits and the native curve-table
pair selected by `FUN_00408F20`. Float semantics are not named without stronger
evidence.

| ID | Class / local | Retail vehicle | Sample family | Sample `+0x1C` bits | Tuning `+0x14` bits | Curves |
|---:|---|---|---|---|---|:---:|
| 0 | T1 / 0 | Landcruiser | rev9 | `3fc00000` | `3f733333` | A |
| 1 | T1 / 1 | Pajero | rev9 | `3fcccccd` | `3f733333` | B |
| 2 | T1 / 2 | Tata | engine3 | `3fb33333` | `3f6b851f` | C |
| 3 | T1 / 3 | Terrano | rev9 | `3fcccccd` | `3f866666` | D |
| 4 | T1 / 4 | Chevyblazer | engine4 | `3fcccccd` | `3f7d70a4` | B |
| 5 | T1 / 5 | Xtrail | rev9 | `3fc00000` | `3f83d70a` | A |
| 6 | T1 / 6 | Frontera | rev9 | `3fb9999a` | `3f87ae14` | B |
| 7 | T2 / 0 | Navara | rev9 | `3fc66666` | `3f851eb8` | A |
| 8 | T2 / 1 | Forester | engine3 | `3fcccccd` | `3f8147ae` | A |
| 9 | T2 / 2 | Jump | rev9 | `3fcccccd` | `3f800000` | B |
| 10 | T2 / 3 | Rmonster | engine3 | `3fb33333` | `3f8a3d71` | B |
| 11 | T2 / 4 | Patrol | engine3 | `3fd9999a` | `3f8147ae` | A |
| 12 | T2 / 5 | Newrav | rev9 | `3fd47ae1` | `3f88f5c3` | B |
| 13 | T2 / 6 | Kiasportage | rev9 | `3fbae148` | `3f8147ae` | C |
| 14 | T3 / 0 | Wildcat | rev9 | `3fbae148` | `3f8147ae` | A |
| 15 | T3 / 1 | Simmbugghini | engine9 | `3fbae148` | `3f87ae14` | A |
| 16 | T3 / 2 | Astero | rev9 | `3fae147b` | `3f851eb8` | A |
| 17 | T3 / 3 | Kangoo | rev9 | `3fc7ae14` | `3f83d70a` | A |
| 18 | T3 / 4 | Megane | engine3 | `3fbae148` | `3f8147ae` | C |
| 19 | T3 / 5 | Mattserati | engine9 | `3fc7ae14` | `3f8147ae` | A |
| 20 | T3 / 6 | Bruno | engine3 | `3fae147b` | `3f8147ae` | D |
| 21 | T3 / 7 | SeatBuggy | engine3 | `3fbae148` | `3f8147ae` | B |
| 22 | T3 / 8 | Kamaz | engine3 | `3fae147b` | `3f333333` | A |
| 23 | T3 / 9 | Icecream | engine3 + separate icecream object | `3fbae148` | `3f333333` | A |
| 24 | T3 / 10 | Ufo | ufo | `3fae147b` | `3f333333` | A |
| 25 | — | No initialized pristine retail record | rev9 fallback if passed | default `3fc00000` | default | A fallback |

IDs 0–24 all have explicit audio cases. Physical ID25 is uninitialized in
pristine retail; the active project later uses this slot for Trooper, but that
does not create a tuned retail sound case. Physical ID26 likewise takes the
fallback unless the G.2 audio-only selector is enabled.

There are five explicit sample families and 25 distinct composite tuned
profiles across IDs 0–24. Vehicles share sample families, but no exact
composite profile is duplicated across the recovered sample, scalar, tuning
field and curve-pair selectors. See the machine-readable matrix for raw table
addresses/hashes and asset hashes.
