# R5V-J.2 runtime evidence — 2026-10-09

## Provenance and integrity

The supplied `2026-10-09.zip` contains 11 JSON captures and 11 raw Broker dump
sidecars. All 11 JSON-to-sidecar links, byte lengths, and SHA256 values were
recomputed from the archive contents and match the capture metadata. There
were no failed or missing sidecars.

| Item | Verified value |
|---|---|
| Archive SHA256 | `715c647e3602ec5635efb0fa5e90e00d6b8f498d8b2ad2fa10e983672aecf5ac` |
| Capture pairs | 11 |
| Process | PID 50160 for all captures |
| Observatory | 0.2.3-beta |
| On-disk executable | `D:\Game\Master Rallye\MRallye.exe` |
| On-disk executable SHA256 | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| On-disk size | 3,121,214 bytes |
| Effective live Dump walker | `native-hardened-null-safe-stubs-v1` |
| Live walker SHA256 | `16d85b7cae971b50f0ad1fd33425bae992cc758c0416c856199eb5ea3dfe2fe9` |
| Live dump verification | `verified`; both approved trampolines verified in every capture |

The capture metadata's `vehicle_registry_profile = pristine` describes the
executable file on disk. It does not state that the live process registry is
pristine and does not contradict the live `Race/CarN` addon records. The
Observatory JSON does not include the launcher executable hash. The candidate
launcher identity below comes from the canonical local J.1 bundle and its
runtime handoff, not from inference from Broker captures.

Machine-readable selected values and all sidecar hashes are retained in
[`runtime-evidence-2026-10-09.json`](runtime-evidence-2026-10-09.json). Raw
captures remain outside Git.

## Capture-by-capture result

| Label / capture | Raw sidecar SHA256 | Bytes | Evidence and limit |
|---|---|---:|---|
| `R5VQ-quickrace-menu` / `20261009-104623_R5VQ-quickrace-menu.json` | `937ce192234ed40d7ee16347124ea512be06384ef76a5fd90db007119cbeffcc` | 1,001,149 | Quick Race menu: stored `QuickRace/Car0 = 27`, `VehicleSelect/CarModel = 27`, visible string `R5V T2 QUALIFIER`; not a post-race restoration test. |
| `R5VQ-carselect-menu` / `20261009-104725_R5VQ-carselect-menu.json` | `ff0f485a141f1163b2c91af02f3133fef29f4d5025e2c5989b43cd6450125966` | 2,962,275 | Vehicle Select state shows ID27 and qualifier labels. |
| `Merc-carselect-menu` / `20261009-104800_Merc-carselect-menu.json` | `1bd4c3764af1fc9b4f9658d39fe3bcdc0734695a8a999c8b97857f72555d586d` | 3,923,087 | `VehicleSelect/CarModel = 26`; the Quick Race field still reflects the prior qualifier selection during this capture. It is not a completed selection-restoration sequence. |
| `Merc-quickrace-menu` / `20261009-104841_Merc-quickrace-menu.json` | `03e8e28eecace6268b5ee96ee33be90aaef35698a805269835ee263c81b858da` | 4,889,300 | Quick Race menu identifies ID26 and shows `MERCEDES ML-320`. |
| `Merc-quickrace` / `20261009-104951_Merc-quickrace.json` | `8f82cdad735ec5d60fd35c4f09c3b5537b751bf9691b55134b5ae7e4f2d4b9f1` | 5,973,601 | Player Car0 is physical ID26, T1, human; CarType/WheelType `Mercedes`; red record colour `[1,0,0,1]`. Four total participants. |
| `Merc-quickrace-AI` / `20261009-105201_Merc-quickrace-AI.json` | `07944f1c8acce709eb58c2c474b41eec2d999288a2dd9485b93bf4271ba90a81` | 7,064,365 | Natural AI Car3 is ID26/T1/AI, DriverID2, CarType/WheelType `Mercedes`, red record colour. Player is Frontera ID6. No forced-slot conclusion is needed beyond the verified candidate manifest. |
| `Merc-raceresult-AI` / `20261009-105320_Merc-raceresult-AI.json` | `2e340c2daf6402a86135892b0e4626d73c006101d3f5ffe3ba4f4aff20725875` | 8,137,165 | Results `NameList` contains `JEAN-PIERRE STRUGO`; native DriverID remains 2. This capture does not establish a complete external launcher identity by itself. |
| `R5VQ-quickrace-AI` / `20261009-105458_R5VQ-quickrace-AI.json` | `b4b7abfda2572970b9abd63b462093c80c4c1a3738abb9f129a51bf2b95eea5e` | 9,222,687 | Natural AI Car2 is physical ID27/T2/AI, DriverID5, CarType/WheelType `R5VQualifier`; live colour is magenta `[1,0,1,1]`. Four total participants. |
| `R5VQ-raceresult-AI` / `20261009-105605_R5VQ-raceresult-AI.json` | `546283699dc8418142e4c9f57bbc0937033903978e4b58d7a8cbe1e805458c05` | 10,295,919 | Results `NameList` contains `R5V TEST DRIVER`; same ID27 Car2 and DriverID5 remain present. |
| `R5VQ-rallyecup-AI` / `20261009-105758_R5VQ-rallyecup-AI.json` | `37975472d142e6f0b6003e8dca667b6d66cf9836c838402192a4080668356ca0` | 11,427,195 | Initial Rallye Cup Race Type 6 includes ID27/T2/AI at Car2, DriverID7, `R5VQualifier` family and magenta colour. |
| `R5VQ-rc-raceresult-AI` / `20261009-105913_R5VQ-rc-raceresult-AI.json` | `fc3126f3566b13fa848186409e118c643301b2a970322aa48605d6dc02aa49ac` | 12,509,465 | Initial Cup Results preserve ID27 Car2/DriverID7 and display `R5V TEST DRIVER`. This is the same stage's Results, not a later Cup stage. |

## J.2 evidence classification

Confirmed by the supplied runtime captures and owner report:

* The original retail EXE remains the file at the process image path and has
  the exact retail SHA above.
* The active process has the approved J.1 hardened native Dump walker; this is
  verified for the full 1,536-byte walker and both null-safe trampolines, not
  inferred from the disk EXE profile.
* The one combined J.1 bundle has working Mercedes ID26 and R5VQualifier ID27
  paths across separate Player, natural AI, Quick Race Results and initial
  Rallye Cup/Results runs.
* Native physical IDs, classes, player/AI roles, runtime families, Results
  labels, and both configured race colours are present in Broker state.
* Human observations confirm the vehicles render and drive in their tested
  Quick Race scenarios. The JSON by itself cannot prove image equality,
  driving quality, or visual HUD correctness.

Not established by this archive:

* both addon vehicles simultaneously in one SplitScreen session;
* the complete post-race Vehicle Select return/reopen test for ID27, ID26, and
  stock ID7;
* Rallye Cup next-stage roster reuse (the second capture is Results for the
  initial stage);
* Master Rallye new competition, native save, process exit, fresh-process
  resume, or following-stage reuse;
* removal/control launch and profile-isolation behavior;
* HUD/progress marker appearance or full visuals from Broker state alone.

Thus J.2 has meaningful combined-package runtime coverage, but remains
`PARTIAL_RUNTIME_CONFIRMED`; the outstanding release gates are listed in
[`human-qualification-handoff.md`](human-qualification-handoff.md).
