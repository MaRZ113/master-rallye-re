# R5V-F.2e — final Mercedes ML-320 integration

## Current result

**STATIC BUILD PASS; P0/P1 HUMAN ACCEPTANCE PENDING.** The final ID26 candidate and isolated retail runtime package are prepared and hash-locked. No human runtime test has been claimed for this exact candidate.

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

The supplied R5V-F.2e prompt reports prior cache-only portability and collision/external/internal damage runtime success. I record those as **OWNER-REPORTED**. The checked-in R5V-F.2d cache manifest still says its runtime gate is waiting for a human log, and no matching DebugView capture was available in this repository. Therefore this phase claims neither a local cache-only runtime capture nor final-candidate P0/P1 success. Run the exact isolated candidate using [runtime-test-plan.md](runtime-test-plan.md).

Collision tag101 structural checks, zero-edit roundtrip, and cooked DX hashes remain as documented in [R5V-F.2b collision validation](../r5v_f_2b/collision-validation.md). The supplied phase prompt reports the earlier usable collision and damage test; final candidate gameplay acceptance remains pending.

## Scope

ID26 remains test-unlocked for offline acceptance. Campaign/save persistence, AI/event pool integration, multiplayer, authentic Mercedes SmallCarSheet art, and tuned ID26 audio are not established here. No ID27, tracks, R5V-G implementation, or push was performed.
