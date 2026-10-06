# R5V-G.2 runtime closeout

Status: **FULL PASS / CLOSED**. The donor0 and donor19 captures were parsed;
each raw sidecar SHA256 matches its JSON metadata, and each capture's
`exe_sha256` and `image_sha256` match the expected tested candidate. The
machine-readable summary is [runtime-results.json](runtime-results.json).
Raw dumps and executable files remain outside Git.

| Test | Executable SHA256 | Raw sidecar SHA256 | Human sound result |
|---|---|---|---|
| ID26 / profile 0 Landcruiser | `636422d0a21b5f75abd3d6233ab0fcbae26cb0dce79c1a8d40d60ad2e8ca488f` | `47f66586022926ee41360fcbae28a2f7e6a79531c26d7726304ae972460d9ac6` | Ordinary / normal stock-style sound |
| ID26 / profile 19 Mattserati | `fb11754c0c6d56b02c175a261e36d0768a72bba6d5a0fd74cbd7c7ad9d34be7b` | `1a779f8c6482a4dd028ff203a67db9c8708a0458e12c2fc45e979acd13a36ad0` | Clear change; bass-heavy buggy sound |

Both captures show `Race/Car0/CarID=26`, `CarClass=0`, `CarType=Mercedes`,
`WheelType=Mercedes`, `Frontend/VehicleSelect/CarModel=26`, and the same
`MERCEDES ML-320` Quick Race identity. Each contains the same 157
`Vehicles/Car0/*` paths. The 114 stable dimension, engine, suspension and
chassis values match; the nine `Physics/Car0/*` paths include wheel transforms
that differ with pose between separate driving moments. No donor identity is
visible in those physical channels.

The two 3,121,214-byte candidate executables differ at exactly one file byte,
`0x28E688`, the low byte of the wrapper's `MOV EAX, stock_audio_profile_id`
immediate. Profile 0 encodes `B8 00 00 00 00`; profile 19 encodes
`B8 13 00 00 00`. This isolates the audible A/B to the selected complete
stock audio profile. **Physical identity / audio identity decoupling is
CONFIRMED_BY_RUNTIME.**

Retail has explicit tuned cases for IDs 0..24, each with a distinct recovered
composite profile. Only IDs 0 and 19 were individually heard on ID26 in this
phase. Profile ID0 is the final Mercedes default because demo 8.4.1 and 9.3.1
both use the ordinary `rev9` / curve-A path for Mercedes ID2. This is a
historical-compatible stock profile, not a claim of a unique authentic
Mercedes recording. ID19 remains the diagnostic/style oracle.

The audio constructor's normal tuned path is runtime-confirmed through exact
candidate identity and causal A/B. The literal
`Warning - untuned car engine sound used (CarID 26)` message is **NOT DIRECTLY
RECAPTURED**: Observatory captures are Broker dumps, not warning logs. No full
stage/results lifecycle or AI use is claimed by this short audio test.

ID25/Trooper remains outside this result and currently follows the retail
fallback unless separately assigned a proven stock profile. AI-pool inclusion
is the next distinct vehicle phase.
