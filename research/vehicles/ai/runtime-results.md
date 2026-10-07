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

The human also reports that the Race Results participant name was
`GALOCAL UNKNOWN`. The supplied capture and raw sidecar were captured during
the active race, not on the Results screen; they contain no
`Frontend/RaceResults/NameList` value. Therefore the visible name is
**HUMAN_RUNTIME_OBSERVATION**, while its native producer and correction are
**CONFIRMED_BY_EXE / READY_FOR_HUMAN_RETEST** respectively. The Ghidra trace is
in [Race Results identity](race-results-identity.md).

The native Debug->Dump call after Results still crashes on this un-hardened
candidate. The failure is consistent with the known retail NULL `StringList`
formatter defect and has a clean-stock reproduction; it is not evidence of an
AI or Mercedes runtime failure. Post-Results Dump safety is not yet runtime
confirmed for the newly built hardened candidates.

## H.0.1 candidates — rebuilt, not yet human retested

Both current candidates derive from exact pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, then
compose G.1, G.2 audio profile 0, and the bounded H.0.1 changes. Each is
3,121,214 bytes. Candidate manifests are generated next to each executable in
ignored `.research-output`.

| Profile | Candidate SHA256 | H proof hook | Randomizer | Current purpose |
|---|---|---:|---:|---|
| `ordinary-hardened` | `391d5d864699b6e945eed43fd8e7bc28b28639b24b222428ab79231e7cc3a819` | no | no | Separate ordinary hardened EXE for stock/player tests without forced AI or randomizer |
| `forced-id26-ai-hardened` | `9255c9d7cb27336d0a5324bd193719c768f09f5bb7d37e30bab384031b0de0e7` | yes, bounded Car1 proof only | no | Re-test the forced ID26 actor, corrected Results name, and native post-Results Dump |

The ordinary candidate's staged runtime package and verifier both return
`PASS`; the forced candidate's separate package and verifier also return
`PASS`. Each package includes the pinned G.1 resources and VehicleSelect scene
SHA256 `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`,
and excludes generated PlayerState files. The ordinary package has neither a
forced-ID26 hook nor a randomizer DLL; its manifest reports both
`forced_ai_proof=false` and `randomizer_present=false`. These are on-disk
package results, not gameplay results.

The neutral Loading->Attract and native Dump patches plus the ID26 Results
display-selector fix are **STATICALLY VERIFIED / READY_FOR_HUMAN_RUNTIME**.
The Results fix changes only the localization selector for an AI competitor
whose physical CarID is 26. The original CarID remains 26; stock IDs and human
name paths are unchanged. No randomizer code is present. See
[hardening details](hardening.md) and the [updated handoff](runtime-plan.md).

## Scope boundary

The forced H.0 actor proof is complete. Natural T1 pool membership remains
**NOT STARTED**. The H.0.1 Results-name correction and hardened Dump require a
human pass before they can be marked runtime-confirmed. Do not proceed to
natural pool inclusion, ID27, T2 expansion, ordering, audio changes, or SDK
work as part of this closeout.
