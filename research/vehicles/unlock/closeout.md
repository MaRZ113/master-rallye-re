# R5V-G.1 final closeout

## Final candidate

* Source: pristine retail, SHA256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
* Candidate: `MRallye_g1_final_racedetails.exe`, SHA256
  `722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`,
  3,121,214 bytes, 78 patch operations.
* Vehicle Select overlay SHA256:
  `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`.
* Effective runtime Root:
  `.research-output/vehicles/unlock/runtime-package/`.

## Locked and unlocked ID26

On a fresh profile with cheats off, ID26 follows the stock T1 `T1CupCar1`
gate: `CarModel=-1`, `CAR LOCKED`, requirement `UNLOCK BY WINNING 2 T1 CUPS`,
native locked slot art, `UI/Enabled=False`, and normal accept is blocked. After
the native requirement is met, `T1CupCar1=True`, `CarModel=26`,
`MERCEDES` / `ML-320`, the normal thumbnail, and enabled selection return.
The locked-to-unlocked transition is **CONFIRMED_BY_RUNTIME**.

`FrontEnd/Network/selectedCar` is the highlighted/current frontend identity in
this context. It is not a commit oracle: a highlighted locked slot can publish
its ID. The tested commit oracle is `UI/Enabled` together with observed normal
accept behavior.

## Frontend identity and Race Details

Frontend identity is split across distinct producers: Vehicle Select groups
`0x33`/`0x34`, Quick Race and Race Details group `0x35`, Race Options groups
`0x33`/`0x34`, and Vehicle Setup group `0x35`. The Race Details producer is
shared writer `FUN_0047C080`; it uses absolute
`RaceData/CompetitorN/CarID` and has three bounded ID26-only hooks at
`0x0047C0F5`, `0x0047C181`, and `0x0047C200`. Stock IDs keep the original lookup.

The final Master Rallye and Rallye Cup captures both report
`Frontend/RaceDetails/CurrentVehicleString="MERCEDES ML-320"`,
`RaceData/Competitor0/CarID=26`, `Race/Car0/CarID=26`, and class 0. Raw files
match the metadata hashes:

| Mode | Capture | Raw SHA256 | Race text in this capture |
|---|---|---|---|
| Rallye Cup | `20261006-173057_g1-racedetails-rallyecup` | `ec88c4c88c7517929b71e091fe433a195c97c550e5fa203f17c352d4aeffad02` | `RACE 1/3` |
| Master Rallye | `20261006-173146_g1-racedetails-masterrallye` | `6ca9ebf726c1be8f871091a5704fa45fef22a6d8122a3af1a1f2b39b5c0d16a7` | `LEG 1/10 - FRANCE` |

The human confirms correct visible rendering in both modes. The event text is
capture-specific, not a fixed invariant. Stock ID0 Race Details regression is
PASS by owner report. Full stage and Results on the final candidate are PASS by
owner report. Frontend return was not separately reported. No human
split-screen test is claimed; both branches are statically covered.

Known, qualified ID26 frontend consumers have no remaining
`GALOCAL UNKNOWN` result. Challenge and Trophy consumers are explicitly
outside the ID26 qualification scope.

## Architectural result

R5V-G.1 distinguishes class reachability from per-vehicle availability. It
mirrors stock ID3's native availability predicate and requirement string for
ID26 without changing its physical record or runtime identity. Correct locked
UX required the availability predicate, locked model state, requirement text,
locked thumbnail, and disabled commit control together. Presentation remains
separate from physical ID: CarID 26, class T1/local index 7, and Mercedes
runtime family are preserved. No global `gaLocal` behavior or donor identity
was changed.

**R5V-G.1 VEHICLE UNLOCK + FRONTEND IDENTITY ARCHITECTURE: FULL PASS / CLOSED.**

## Mercedes integration boundary and roadmap

Mercedes ID26 has passed physical resource, model, preview, physics,
collision/damage, qualified frontend identity, and native unlock integration.
Audio identity remains the next known missing integration layer; a prior
`gaAiVehicleSound` warning reported an untuned sound for CarID 26. Audio is
not analyzed here. Immediate next phase: **R5V-G.2 — Vehicle Audio Identity /
Sound Family Architecture**. Catalog/order refinement is deferred until
multiple add-on vehicles make it useful. Later phases: R5V-H AI pools, R5V-I
multi-slot registry expansion with a real additional T2 vehicle, then R5V-J
generic Addon Vehicle SDK. Do not infer audio, AI eligibility, generic ID27+,
or generic SDK behavior from this closeout.
