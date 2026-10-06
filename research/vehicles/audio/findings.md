# R5V-G.2 vehicle audio identity

## Current result

**R5V-G.2 is FULL PASS / CLOSED.** Human A/B testing confirmed that changing
ID26's audio profile changes its engine sound while the participant remains
physical Mercedes ID26. The final Mercedes policy uses retail
`stock_audio_profile_id = 0`; ID19 remains the confirmed diagnostic oracle.
The G.1 physical and unlock profile is retained as the base.

The retail executable creates a `gaAiVehicleSound` component for every active
`Race/CarN` slot. The component reads the participant's absolute
`Race/CarN/CarID`, then uses that value in separate native switches to select
an engine sample object, scalar settings, and a pair of 60-entry curve tables.
Physical ID26 has no tuned switch entry. It takes the warning/default path,
which uses `vehicles/rev9`, default tuning values, and curve table A.

The best historical mapping is available: demo 8.4.1 and 9.3.1 each register a
Mercedes as ID2, and their audio constructor puts IDs 0 and 2 through the same
`vehicles/rev9` branch and curve-table-A path. In those builds Mercedes shares
the ordinary Landcruiser profile; there is no Mercedes-only sample. The retail
donor A therefore uses the current retail ID0 profile. Demo data was not copied
into the retail candidate.

The runtime-tested candidates were:

| Candidate | `stock_audio_profile_id` | Sample family | Human result |
|---|---:|---|---|
| A | ID0 Landcruiser | `vehicles/rev9` | Ordinary / normal stock-style engine sound |
| B | ID19 Mattserati | `vehicles/engine9` | Clearly changed; bass-heavy buggy sound |

Both candidates change only the CarID value consumed by the audio constructor
when it is 26. The native getter still runs for every participant. No vehicle
record, CarClass, model, wheel, physics, unlock, frontend, or race-result field
is changed by the G.2 layer. The original warning code remains unchanged; the
static switch path and runtime A/B show the configured tuned profile is used.
The warning text itself was not directly recaptured in these tests.

The deterministic outputs are 3,121,214-byte retail-derived executables:

| Candidate | Output SHA256 | Research output |
|---|---|---|
| A / donor ID0 | `636422d0a21b5f75abd3d6233ab0fcbae26cb0dce79c1a8d40d60ad2e8ca488f` | `.research-output/vehicles/audio/MRallye_r5v-g2_audio-id26-donor0.exe` |
| B / donor ID19 | `fb11754c0c6d56b02c175a261e36d0768a72bba6d5a0fd74cbd7c7ad9d34be7b` | `.research-output/vehicles/audio/MRallye_r5v-g2_audio-id26-donor19.exe` |

Both rebuild from pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, reproduce
the exact G.1 base SHA256
`722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`, and pass
the candidate verifier. The G.2 hook replaces the five-byte call at VA
`0x00408FB4`; its wrapper starts at `0x0068E679`. Both outputs retain the same
G.1 patch set and differ at exactly one byte: the low byte of the wrapper's
`MOV EAX, stock_audio_profile_id` immediate (`0x00` versus `0x13`). The
corresponding captures report the exact output hashes. See
[runtime results](runtime-results.md).

The builder now accepts any matrix-verified explicit tuned retail profile
0..24. Only ID0 and ID19 are individually human-tested here; the other tuned
profiles are statically supported, not runtime-qualified. Profiles 25, 26 and
27+ are rejected as configuration values.

The hash-keyed ID0 executable above is the canonical Mercedes G.2 candidate;
its already-qualified bytes were preserved through the builder generalization.

## Evidence boundary

`CONFIRMED_BY_EXE`: the selector, warning branch, fallback, sample-family
switches, scalar immediates, curve-table selection, and common per-slot owner.

`CONFIRMED_BY_CORPUS`: stock vehicle names/classes, WAV availability and
hashes, and the G.1 pristine-to-candidate reproduction.

`CONFIRMED_BY_RUNTIME`: exact ID0 and ID19 candidate hashes, Broker identity
captures, and human audible A/B observations agree.

`HUMAN_RUNTIME_OBSERVATION`: ID0 is ordinary stock-style; ID19 is audibly
distinct and bass-heavy. This is a subjective sound description, not proof of
which scalar or sample component causes it.

`NOT DIRECTLY RECAPTURED`: the literal untuned-warning log line. Static switch
flow and exact candidate-driven A/B support the normal tuned path, but the
Broker dump is not a log capture.

Internal float fields and curve-table values are recorded as raw bits. Their
precise meanings (for example RPM, load, or pitch axes) remain unknown.

## Files

* [Audio architecture](architecture.md)
* [Warning path](warning-path.md)
* [Component ownership](engine-sound-owner.md)
* [Stock ID/profile matrix](stock-audio-matrix.md) and
  [JSON](stock-audio-matrix.json)
* [Buggy audio oracles](buggy-oracles.md)
* [Cross-build comparison](cross-build.md)
* [Historical Mercedes mapping](historical-mercedes-audio.md)
* [ID26 stock audio profile policy](id26-policy.md)
* [Fallback behavior](fallback.md)
* [Runtime closeout](runtime-results.md)
* [Historical runtime handoff](runtime-plan.md)
* [Validation](validation.md)

R5V-G.2 is closed. R5V-H AI Opponent Vehicle Pools is the next vehicle phase
but was not started here. Ordering, ID27+, T2 expansion, and the generic SDK
remain deferred.
