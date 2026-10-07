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

## H.1 natural T1 candidate — original handoff state (superseded)

The pending status in the following pre-runtime candidate notes is superseded
by the H.1 runtime closeout at the end of this file; its build details and
original human procedure remain historical.

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

This was static/candidate/package evidence only at the time; its pending state
is superseded by the current H.1 closeout below. Use the exact test steps in
[natural-t1-runtime-plan.md](natural-t1-runtime-plan.md) only as historical
provenance.

## H.1 natural Quick Race runtime closeout — 2026-10-07

The four Observatory 0.2.2-beta JSON/raw pairs below identify the same exact
H.1 candidate SHA256
`e59895776dd53acb3ac4a25e1973c8de341da815b90407ec372b696be06d363a`. Every
raw sidecar SHA256 matches its JSON metadata.

| Capture | Raw sidecar SHA256 | Runtime evidence |
|---|---|---|
| `20261007-155141_natural-t1-race-elf01` | `90fbf13b76621e4191394bbdace8d6451bb288d8ca08d01282f9d7cb170d80ce` | Quick Race active roster |
| `20261007-155913_natural-t1-id26-results` | `6042ae73b49a86f0945c6985c3185e613cf2c269149ca43981a7370ba83eb9da` | Completed race Results identity |
| `20261007-160617_master-rallye-mode` | `c6dfe021abf4aad282669a11575dcaf9589e9a85b2bd71584441bb20d2fa6994` | Master Rallye mode control; not an H.2 inclusion test |
| `20261007-160804_rallye-cup-mode` | `10ca6906519bc68ac2f60b83a7b90792960f4afaf2aaa99eda06a9fff17faa95` | Rallye Cup mode control; not an H.2 inclusion test |

The natural Quick Race capture has `Race/Type=2`, four total cars, one human,
and `Progress/UnlockedCars/T1CupCar1=False`. The player remains Car0 ID1/T1;
the AI roster is Car1 ID2, Car2 ID26, and Car3 ID6, all T1. Car2 reports
`CarType=Mercedes` and `WheelType=Mercedes`. This confirms natural ID26
eligibility in the H.1 Quick Race pool while the player remains locked. The
human reports that newly generated Quick Race rosters sometimes omit Mercedes,
supporting that no participant slot is forced; no statistical distribution is
claimed.

The Results capture records the physical ID26 AI at Rank 2 and the Results
`NameList` contains `JEAN-PIERRE STRUGO`. This is a display-only policy;
native DriverID selection is unchanged. Natural Quick Race ID26 selection and
this fixed Results identity are `CONFIRMED_BY_RUNTIME`.

The Master Rallye control reports RaceType 5 and AI IDs 5, 0, 1. The Rallye
Cup control reports RaceType 6 and AI IDs 1, 3, 5. These samples establish
their mode identity and illustrate that H.1's Quick-Race-only hook does not
change their rosters; they are not evidence against H.2 and are not inclusion
tests.

## H.2 mode-aware candidate — original pre-runtime handoff (superseded)

H.2's current-branch trace found distinct native generation owners for Cup /
Invitation and new Master Rallye competitions. The candidate extends only
their T1 source-pool exits. It leaves existing Cup/Invitation roster
publication, MasterRallye/CarN storage, save/load, resume, and next-stage
reuse paths untouched. See [mode-aware-t1-eligibility.md](mode-aware-t1-eligibility.md)
and [mode-aware-runtime-plan.md](mode-aware-runtime-plan.md). The H.2 package
passes deterministic build and on-disk staging verification, but ID26
inclusion and persistence with that candidate have not been observed in a
human runtime session.

## H.2 mode-aware runtime closeout — 2026-10-07

The nine supplied Observatory 0.2.2-beta captures identify the same exact
candidate executable SHA256
`de5e81c0b126619574834f25ac941cd491139235fd2f89086d8e125f063dcac9`
(3,121,214 bytes; profile `mode-aware-natural-t1-id26`). Each JSON's
`source.raw_sha256` was recomputed from the corresponding `.dump.bin` bytes and
matched. No raw captures are committed.

| Capture label | Raw sidecar SHA256 | Verified runtime result |
|---|---|---|
| `h2-rallyecup-id26-stage1` | `46f5884dbb4d92a3d528df8d49ff16ea6d20112cd52352a790e7773fbbd12393` | RaceType 6; four-car T1 roster; ID26 Mercedes AI at Car2 |
| `h2-rallyecup-id26-stageresults` | `431639f9427479ded72a5df1ab42231809ba141460bdde63b6a39c51fba18a04` | Same physical IDs/classes/DriverIDs; Results NameList includes Strugo |
| `h2-rallyecup-id26-stage3` | `0c7379ce473be32c8b22ef1201a275f90db9bde2f9a291b0898097290543873a` | Same physical IDs/classes/DriverIDs; ID26 remains Mercedes at Car2 |
| `h2-rallyecup-id26-cupresults` | `81d5be7ba3250b204bba5619dc585f1dec9258c370c434ca2f074f7a737525e0` | Same roster through Cup Results; NameList includes Strugo |
| `h2-master-id26-new` | `498125c742b69f228d3255ddd12d7a4c4e2ddfe47c6047a932f9d38b92d1f2dd` | PID 46152; RaceType 5; native MasterRallye and active Race roster contain ID26 at Car2 |
| `h2-master-id26-results` | `0033d66e1070e49d616a483455d5b8c2b923cb2d006d149a0dd8327332ef8fbf` | Same MasterRallye roster; ID26 Results display is Strugo |
| `h2-master-id26-finalresults` | `6233e115d112c438e29bb545d92be8dd7c71caef3a350d245375fcebec0749fe` | Same native roster through final Results; ID26 Results display is Strugo |
| `h2-master-id26-resume` | `45dcdb71cb5d037c6e614944e9aea7387bfbb4dbc8ac8af9a69d1c089705de09` | PID 19008; fresh-process resume restores exact MasterRallye roster and active Race CarIDs/DriverIDs |
| `invitation` | `5e91daa8ef9337aa4b49ea6b68efb92fdc638325e34cf4de050e415e220cf7d8` | PID 19008; RaceType 8; player and all AI are T3, IDs 17/14/15/20 |

### Rallye Cup

The stage-one active race reports `Race/Type=6`, `Race/NumCars=4`, and
`Race/NumPlayers=1`. Its roster is:

| Slot | CarID | CarClass | DriverID | PlayerType | Runtime family |
|---|---:|---:|---:|---:|---|
| Car0 | 2 | 0 / T1 | 30 | 1 / human | Tata |
| Car1 | 0 | 0 / T1 | 0 | 2 / AI | Landcruiser |
| Car2 | 26 | 0 / T1 | 3 | 2 / AI | Mercedes |
| Car3 | 6 | 0 / T1 | 2 | 2 / AI | Frontera |

The same IDs, classes, and DriverIDs appear in the later stage and Cup-result
captures. Car2 retains `CarType=Mercedes` and `WheelType=Mercedes`. Human
runtime reports normal Cup gameplay without issues. This proves natural
Rallye Cup ID26 T1 eligibility and native roster reuse across the tested Cup
stages: **CONFIRMED_BY_RUNTIME**. The extension is applied only at native new
roster generation; no per-stage reroll was added.

### Master Rallye

The new competition capture reports PID 46152 and this native roster in both
`MasterRallye/CarN` storage and active `Race/CarN` state:

| Slot | CarID | CarClass | DriverID | PlayerType | Runtime family |
|---|---:|---:|---:|---:|---|
| Car0 | 0 | 0 / T1 | 30 | 1 / human | Landcruiser |
| Car1 | 5 | 0 / T1 | 2 | 2 / AI | Xtrail |
| Car2 | 26 | 0 / T1 | 4 | 2 / AI | Mercedes |
| Car3 | 1 | 0 / T1 | 5 | 2 / AI | Pajero |

The two Results captures retain the same native roster. After the original
process ended, fresh process PID 19008 resumed the competition; the capture
again reports `MasterRallye/Car0..3` IDs `0,5,26,1` and DriverIDs `30,2,4,5`,
with active Race Car2 physical ID26 and native DriverID4. Thus natural
Master Rallye eligibility, native roster storage, and
save -> process exit -> fresh process -> load restoration are
**CONFIRMED_BY_RUNTIME**. No sidecar is required. The fixed ID26 Results
display name is `JEAN-PIERRE STRUGO`; native AI DriverID remains 4 and is not
bound to that display label.

### Invitation classification and H closeout

The Invitation capture is a control, not an ID26 failure: `Race/Type=8`,
player Car0 ID17 Kangoo class 2/T3, and AI IDs 14 Wildcat, 15 Simmbugghini,
and 20 Bruno, all class 2/T3. The observed normal mode is T3-only and consumes
the ordinary/base T3 family IDs 14..20. H.2 extends only the shared chooser's
T1 arm, which this route does not reach. Therefore Invitation T1 ID26 is
`NOT_APPLICABLE`, not `NOT_FOUND` or an RNG failure. A future ordinary,
non-bonus T3 addon must explicitly qualify for Invitation; bonus/special T3
addons are not included automatically.

The mode matrix is now:

| Mode | Classification | ID26 result |
|---|---|---|
| Quick Race | Dynamic class pool | Natural T1 inclusion `CONFIRMED_BY_RUNTIME` (H.1) |
| Rallye Cup | Dynamic, generated for a new Cup | Natural T1 inclusion and stage reuse `CONFIRMED_BY_RUNTIME` |
| Master Rallye | Dynamic, generated for a new competition | Natural T1 inclusion and native fresh-process persistence `CONFIRMED_BY_RUNTIME` |
| Invitation | Normal tested path is T3-only; ordinary/base IDs 14..20 | T1 ID26 `NOT_APPLICABLE` |
| Challenge | Authored/event-specific | No automatic addon injection |
| Practice | No distinct stock AI roster owner found in bounded audit | `NOT_APPLICABLE` |

R5V-H is **FULL PASS / CLOSED**. ID26 remains physical CarID 26, T1,
Mercedes `CarType`/`WheelType`; player unlock is independent; native DriverID
selection is unchanged; the display-only Results identity remains Strugo; and
G.2 audio continues to resolve physical ID26 to stock audio profile 0. No
capacity or roster-count behavior is implied by this result.
