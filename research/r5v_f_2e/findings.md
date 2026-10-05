# R5V-F.2e — final Mercedes ML-320 integration

## Current result

**SUBSEQUENT OWNER-REPORTED CORE GAMEPLAY PASS; Race Options identity still defective.** The F.2e candidate's Vehicle Select presentation and short-race behavior were later tested by the owner. Its Race Options manufacturer/model strings still resolve to `GALOCAL UNKNOWN`; R5V-F.2f adds the missing narrow presentation hooks. This document preserves the F.2e build facts and chronology.

Candidate package manifest: `research-output/r5v_f_2e/candidate/candidate-manifest.json` (ignored build output). The isolated runtime to test is `research-output/r5v_f_2e/runtime/`.

| Item | Result |
|---|---|
| Clean retail executable SHA-256 | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| Final candidate SHA-256 | `1fb0a1f1ba02cd05fa25f0c94558cf1b281fd12affcdc37bb3c1ca538e6c65af` |
| Deterministic rebuild | PASS; exact candidate bytes, manifest, and categorized diff rechecked |
| Patch operations / cave | 72 operations; 617-byte payload at `0x0068E2A0` |
| Registry | 27 records; T1=8, T2=7, T3=12; T1 local7 ↔ ID26 |
| Existing vehicles | ID0 not targeted; ID25 remains Trooper |
| Profile | ID26 / T1 local7; Mercedes runtime, model, wheel, and physics families |
| Visible name | Vehicle Select `MERCEDES` + `ML-320`; Quick Race `MERCEDES ML-320` |
| Presentation | Stats 4/3/6/5; historical slot art; SmallCarSheet frame9 fallback; custom red marker |
| P0 | WAITING FOR HUMAN |
| P1 | BLOCKED UNTIL P0 PASS |

### Later runtime update and superseding handoff

The owner subsequently reported that ID26/T1 local7 displays `MERCEDES` / `ML-320`, the model/textures and 4/3/6/5 stats are correct, and a short race passes model loading, controls, physics, collision and damage. ID25/Trooper remains separately selectable. This is a core gameplay pass; no full-stage/results/return lifecycle is claimed for this exact F.2e candidate.

Three Broker Observatory JSON + raw pairs are under the ignored `research-output/r5v_f_2e/captures/` directory. They prove the Quick Race field lifecycle: Vehicle Select retains a stale `TOMMEK DIRTBEAST`; Race Options writes `GALOCAL UNKNOWN` to both vehicle and manufacturer strings; active race later refreshes the combined group-0x35 vehicle string to `MERCEDES ML-320` while the separate manufacturer remains unknown. The active race still reports physical `CarID=26`, class 0, `CarType=Mercedes`, `WheelType=Mercedes`, and the red ID26 colour canary.

The old F.2e P0 handoff is **SUPERSEDED FOR FRONTEND IDENTITY** by [R5V-F.2f runtime handoff](../r5v_f_2f/runtime-handoff.md). The F.2e executable remains useful as its recorded historical candidate; do not treat it as having passed Race Options identity.

## Model, materials, and package

The three retail-native Cook A/B outputs are byte-identical for the exact pinned inputs/build:

| File | SHA-256 | Revision | Modern parser |
|---|---|---:|---|
| `complete.dx` | `ddad0c7b13be70388a60a541255eaaf3af7f9b1815f5aa02f2b60050862dc28b` | 135 | PASS |
| `car.dx` | `5ec5f7480ddfc1380131a012b300a4cdeb28b869a1668b6f8bbe97210893ff44` | 135 | PASS |
| `wheel.dx` | `8707d887a75c452eb739775e21f94109521d9fc6be07726cee28a8e911c590ff` | 135 | PASS |

The isolated Mercedes folder has exactly 28 files: three DX and 25 DXT. No Mercedes GXM, GXI, or TXT is present. The fresh DX/DXT inspection parsed all three DX files, resolved 69 texture bindings, and reported zero unresolved references. The validated DXT hashes were rechecked against the R5V-F.2b cache manifest.

The final `Data.sma` is structurally valid. Compared through the project's retail-SMA compatibility reader, it preserves all 7,595 source file members, adds only the 28 expected Mercedes members, removes none, and changes only `DataScene/FrontendScreens/VehicleSelect.xml`. The retail input uses its custom `SM` end marker; the comparison used the repository SMA reader rather than assuming a standard ZIP EOCD.

## Physics and known warnings

The current retail `vehicles.xml` and `Modifications.xml` were re-read. `Vehicles/Mercedes` is `COMPATIBLE`: 144 values, all 120 fixed schema paths, six gears, six torque entries, and 13 Player1 overlay fields. This is static schema evidence. Runtime binding, steering, suspension, and grip still require P1.

The known `Vehicles/Tyres/tarmac5/PeakMu` warning remains unclassified until handling is observed. The `gaAiVehicleSound` ID26 warning remains a known add-on audio fallback unless it causes a functional issue. Neither has been patched speculatively.

## Evidence boundary

The later owner-reported F.2e gameplay results and three paired Broker captures support the CORE GAMEPLAY PASS and physical identity above. They do not establish a full stage/results/return lifecycle. Cache-only portability and the earlier cooker details remain as documented for their original phases; this frontend cleanup does not reopen them.

Collision tag101 structural checks, zero-edit roundtrip, and cooked DX hashes remain as documented in [R5V-F.2b collision validation](../r5v_f_2b/collision-validation.md). The supplied phase prompt reports the earlier usable collision and damage test; final candidate gameplay acceptance remains pending.

## Scope

ID26 remains test-unlocked for offline acceptance. Campaign/save persistence, AI/event pool integration, multiplayer, authentic Mercedes SmallCarSheet art, and tuned ID26 audio are not established here. The dedicated unlock and configurable audio-family requirements are recorded for R5V-G.1 and G.2; no such work is performed in F.2f.
