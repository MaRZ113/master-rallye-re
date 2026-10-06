# Stock Attract chooser

**CONFIRMED_BY_EXE**, pristine retail. `0x449E90` dispatches Race/Type14 through
`0x44A128`: sets NumCars4 and NumPlayers0, pushes false, obtains chooser owner
at `0x458950`, calls `0x4584F0` at `0x44A16D`. Replay record/playback are
disabled. `0x44A450` gives Attract zero human slots and configures AI PlayerType2.

`0x4584F0(false)` builds one eligible pool of **absolute IDs0..20**. It then
conditionally appends22,23,24,21 via stock reward flags12,13,14,11, using
`0x4B0310 -> 0x4AFB70`. This is separate from frontend class availability.
Ordinary T2/T3 vehicles can therefore become AI vehicles on a fresh profile.
The Type15 branch passes true; its different count/lifecycle are outside this
phase, and no capacity conclusion is drawn from it.

An empty remaining pool triggers game range(0,65535), CRT srand, native shuffle
`0x450580`, copy eligible->remaining and clear eligible. Pop the last ID, record
it in used, erase remaining tail. Thus Type14 does not repeat IDs within its
four-slot ordinary pool. It permits duplicate **classes**; no balancing rule
requires one car from each class. Pool populations and native shuffle biases
affect class frequencies. Calling it “independent random-class choice” would
misdescribe the stock implementation.

Each slot uses separate driver helper `0x458980` over one driver0..9 pool.
Publication uses CarID setter `0x4ACAF0`, registry class at `base+0xC+ID*0x34`,
CarClass setter `0x4ACC10`, DriverID setter `0x4ACCD0`. No class-local mapping
is involved. The loop starts at **Car0**, through current NumCars; invoking
the entire chooser from Quick Race would overwrite the human vehicle.

Verdict: **PARTIALLY REUSABLE**. Reuse native shuffle, vector operations, driver
choice and ID-derived identity. Retain Quick Race's human boundary and apply
independent class inputs to its existing inline class-filtered pool builder.

## Verified capture

`20261004-144429_attractmode` has pristine image SHA
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Raw SHA `67783905d14d0703b3c97b9fe83ae59b0ae302747c151077f0c5d4dca11b1059`;
selected block SHA `683d815ab50ae048bc853d33035cdfbc7f601cc2e5b3b1c4b4de3002e378efca`.
The audited parser reproduces JSON entries and selected complete block exactly.

| Slot | ID | Class | Family | Driver | PlayerType |
|---|---:|---:|---|---:|---:|
| Car0 | 1 | 0/T1 | Pajero | 4 | 2 |
| Car1 | 5 | 0/T1 | Xtrail | 1 | 2 |
| Car2 | 12 | 1/T2 | Newrav | 3 | 2 |
| Car3 | 14 | 2/T3 | Wildcat | 2 | 2 |

NumCars4, NumPlayers0, Type14, Attract2, AttractModeTrue; neither replay flag
is enabled. **CONFIRMED_BY_RUNTIME** for this stock live composition.
