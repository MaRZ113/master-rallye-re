# R5V-H runtime evidence ledger

## First H attempt — failed, preserved

The first test used an EXE-only candidate and a pre-existing resource root.
ID26 showed locked text but wrong thumbnail/commit behavior, and Car1 was not
observed as ID26. The active resource root and Car0 ID were not captured, so
the failure remains **FAILED / CAUSE UNKNOWN**. It is not evidence that the
publication hook itself failed. The later exact-root H.0 package and test
supersede this handoff, not this historical record.

## Corrected H.0 forced-ID26 runtime — core proof pass

The corrected human test ran candidate profile `forced-id26-proof`, EXE
SHA256 `dc821c096dea1db00c91ddf41e85cfac1f5369eaf56bd821ed0b904cbe246e13`
(3,121,214 bytes). The Observatory source metadata identifies that same image
hash and path. The accompanying raw sidecar SHA256 is
`84a5cc32520d4a279fe9d5e660e131c5d2a4609a79099b31878a62c9332395fb`; its
header Root is the candidate's `runtime-package` directory. Capture:
`20261007-111017_h0-forced-id26-ai` from Observatory 0.2.1-beta.

The capture records the active race state:

| State | Observed value | Evidence |
|---|---|---|
| `Race/NumCars` | 4 | `CONFIRMED_BY_RUNTIME` capture |
| `Race/NumPlayers` | 1 | `CONFIRMED_BY_RUNTIME` capture |
| Car1 `CarID` | 26 | `CONFIRMED_BY_RUNTIME` capture |
| Car1 `CarClass` | 0 / T1 | `CONFIRMED_BY_RUNTIME` capture |
| Car1 `DriverID` | 8 | `CONFIRMED_BY_RUNTIME` capture |
| Car1 `PlayerType` | 2 / AI enum in this build | observed capture; enum interpretation corroborated by controls |
| Car1 `CarType` / `WheelType` | `Mercedes` / `Mercedes` | `CONFIRMED_BY_RUNTIME` capture |
| Car1 `Colour` | `1.00,0.00,0.00,1.00` | ID26 registry canary in capture |

The complete four-participant roster in that same active-race capture is:

| Slot | CarID | Class | DriverID | PlayerType | CarType / WheelType | Colour |
|---|---:|---|---:|---|---|---|
| Car0 | 0 | 0 / T1 | 30 | 1 / human | Landcruiser / Landcruiser | `0.08,0.42,0.25,1.00` |
| Car1 | 26 | 0 / T1 | 8 | 2 / AI | Mercedes / Mercedes | `1.00,0.00,0.00,1.00` |
| Car2 | 3 | 0 / T1 | 2 | 2 / AI | Terrano / Terrano | `0.65,0.71,0.72,1.00` |
| Car3 | 2 | 0 / T1 | 9 | 2 / AI | Tata / Tata | `0.84,0.85,0.72,1.00` |

These are captured Broker values; the independent visible actor and behavior
claims below come from the human observation, not from path presence alone.

The human observed a distinct Mercedes actor, AI control, normal movement and
race progress, a finish, and a Race Results row. This closes the forced
materialization proof as **CONFIRMED_BY_RUNTIME** for the tested Car1/T1/
three-AI Quick Race path. It does not add ID26 to a natural pool or prove other
modes, slots, or classes.

The original un-hardened H.0 run showed `GALOCAL UNKNOWN` in the Results row.
That capture was from active race and contained no Results `NameList`, so the
old symptom remains classified as a human observation. The later H.0.1
Results-screen captures below directly show the corrected localized names.
The producer trace is in [Race Results identity](race-results-identity.md).

The native Debug->Dump call after Results still crashed on this original
un-hardened candidate, consistent with the known retail NULL `StringList`
formatter defect. H.0.1 later passed the hardened Results Dump path, recorded
below; the historical failure remains preserved as a separate observation.

## H.0.1 Results identity and native Dump — runtime closeout

All three Observatory 0.2.2-beta captures identify the same tested executable
SHA256 `9255c9d7cb27336d0a5324bd193719c768f09f5bb7d37e30bab384031b0de0e7`,
image path under
`.research-output/vehicles/ai/forced-id26-proof-hardened/runtime-package/`,
and profile `local-hardened-9255c9d7cb27`. `exact_profile_id` is `null`,
`profile_origin` is `locally_audited`, and the compatibility family is
`retail-broker-v1`. Each raw header independently reports the same runtime
Root. All raw sidecar SHA256 values match their JSON metadata:

| Capture | JSON SHA256 | Raw SHA256 | Result evidence |
|---|---|---|---|
| `20261007-135125_h0-1-forced-results` | `06597e7c77aadd00619c271fdb8ef028f17e615882d25ac385fa0cc4cf327eff` | `2249ad8ac02afaa41b7f610329f64ad02237154adbf5c4cd05106bd31c192179` | Completed first race, Results NameList |
| `20261007-135213_h0-1-forced-dump` | `d75a8b339f9bc75d0b4184e91f7292483659e61a723b0c094a935cb9e48a97fa` | `3229e33483acf1b54e54c766091d5665ccfb73fd15f8840dd6671e7145defff5` | Post-Results native Dump |
| `20261007-135330_h0-1-forced-results_secondrace` | `d99dfc2f98e2fb111ebf68a67af76b4365abf9b171bd5ec1e4cc46970cb58d69` | `7347e02abe0856c554f681eb08b4456e59d165a9b588799ed0bf2adb3056376f` | Second completed race, Results NameList |

The first Results capture records Car1 `CarID=26`, `CarClass=0`,
`DriverID=6`, `PlayerType=2`, `CarType=Mercedes`, `WheelType=Mercedes`, and
`Rank=4`. The fourth Results name is `BRUNO SELLIER`, matching retail group
`0x39`, selector 6. In the second race Car1 remains ID26/T1/AI, but native
selection gives `DriverID=2`; its fourth Results name is `TESSA BAMFORD`,
matching group `0x39`, selector 2. This confirms that physical vehicle
identity and AI driver identity are separate, and the ID26 Results selector
follows the actual native DriverID. The Results-name fix is
**CONFIRMED_BY_RUNTIME**. The human observed the same visible Results rows.

The post-Results capture reports `native_dump_post_results_safe=true`, emits
`Frontend/RaceResults/PointsList` as an empty StringList, and contains 21
subsequent Broker entries, beginning with `Frontend/RaceResults/Car0`. The
human invoked native Debug->Dump on Results and the game remained alive.
Therefore NULL StringList Dump hardening and post-Results Dump continuation
are **CONFIRMED_BY_RUNTIME**. Textual `{}` / empty-list rendering still does
not distinguish a NULL payload from an allocated empty list. Although the
XmlData guard is part of the candidate, this run does not isolate that guard;
keep its individual runtime behavior **UNKNOWN**.

All three captures show `Race/Type=2`, `Race/AttractMode=False`,
`Race/NumPlayers=1`, and `Race/NumCars=4`. No unintended Attract state was
observed in these races. The exact historical loading-failure trigger was not
retested, so do not claim that trigger's runtime correction from these
captures alone. A second normal race was observed, but it is not evidence of a
specific Restart/loading trigger unless that path is separately recorded.

Observatory's retail-derived compatibility audit and hardened-Dump
classification are **CONFIRMED_BY_RUNTIME** for this tested candidate. No
exact-profile allowlist entry was added: its profile remains locally audited
under `retail-broker-v1`.

## H.0.1 candidate build record

The two candidates derive from exact pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, then
compose G.1, G.2 audio profile 0, and the bounded H.0.1 changes. Each is
3,121,214 bytes. Candidate manifests are generated next to each executable in
ignored `.research-output`.

| Profile | Candidate SHA256 | H proof hook | Randomizer | Current purpose |
|---|---|---:|---:|---|
| `ordinary-hardened` | `391d5d864699b6e945eed43fd8e7bc28b28639b24b222428ab79231e7cc3a819` | no | no | Separate ordinary hardened EXE for stock/player tests without forced AI or randomizer |
| `forced-id26-ai-hardened` | `9255c9d7cb27336d0a5324bd193719c768f09f5bb7d37e30bab384031b0de0e7` | yes, bounded Car1 proof only | no | Re-test the forced ID26 actor, corrected Results name, and native post-Results Dump |

At build time, the ordinary candidate's staged runtime package and verifier returned
`PASS`; the forced candidate's separate package and verifier also return
`PASS`. Each package includes the pinned G.1 resources and VehicleSelect scene
SHA256 `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`,
and excludes generated PlayerState files. The ordinary package has neither a
forced-ID26 hook nor a randomizer DLL; its manifest reports both
`forced_ai_proof=false` and `randomizer_present=false`. These are on-disk
package results, not gameplay results.

The ID26 Results display-selector fix and NULL StringList Dump hardening are
**CONFIRMED_BY_RUNTIME**. The Results fix changes only the localization
selector for an AI competitor whose physical CarID is 26. The original CarID
remains 26; stock IDs and human name paths are unchanged. The XmlData guard
remains static-only, and the loading false-trigger was not isolated by the
new captures. No randomizer code is present. See
[hardening details](hardening.md) and the [updated handoff](runtime-plan.md).

## Scope boundary

The H.0 forced actor proof and H.0.1 Results-name / post-Results Dump checks
are closed for the tested Quick Race path. Natural T1 pool inclusion is the
separate active H.1 phase; no natural pool change is part of this H.0.1
evidence.

## H.1 natural T1 candidate — static package ready; runtime pending

The natural-pool candidate is profile `natural-t1-id26`, built from exact
pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` through
the ordinary G.1/G.2 hardened base. Candidate SHA256 is
`e59895776dd53acb3ac4a25e1973c8de341da815b90407ec372b696be06d363a`, size
3,121,214 bytes. Its patch manifest SHA256 is
`77ff35b1e49025e5b1d29f57d12339a117adb79bc427096cdcfc8685c22c412e`.
The staged runtime package verifies 145 files, includes the pinned
VehicleSelect overlay and Mercedes runtime assets, and excludes PlayerState.

The natural T1 source vector is `[0,1,2,3,4,5,6,26]`; no participant slot is
forced, the randomizer is absent, and participant count is unchanged. The
candidate's ID26 Results display is a fixed `JEAN-PIERRE STRUGO` string,
classified `REAL_2001_MASTER_RALLYE_MERCEDES_DRIVER`; exact ML-320 pairing is
unproven. Native DriverID selection and participant DriverID publication are
unchanged. Demo group-`0x39` selector evidence and the historical-driver
classification are recorded in
[historical-driver-selector.md](historical-driver-selector.md).

This is static/candidate/package evidence only. Natural AI selection,
visible Mercedes behavior, race completion, and the new fixed Results name
remain **READY_FOR_HUMAN_RUNTIME**, not runtime-confirmed. Use the exact test
steps in [natural-t1-runtime-plan.md](natural-t1-runtime-plan.md).
