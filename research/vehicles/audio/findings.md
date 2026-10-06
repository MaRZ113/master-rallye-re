# R5V-G.2 vehicle audio identity

## Current result

**Static reconstruction is complete; the retail-derived ID26 donor candidates
are READY FOR HUMAN AUDIO A/B.** Audible behavior remains untested in this
phase. The G.1 physical and unlock profile is retained as the candidate base.

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

Two controlled candidates are prepared:

| Candidate | Audio selector for physical ID26 | Sample family | Evidence-based role |
|---|---:|---|---|
| A | ID0 Landcruiser | `vehicles/rev9` | Ordinary retail profile and closest match to historical demo Mercedes mapping |
| B | ID19 Mattserati | `vehicles/engine9` | Human-reported bass-heavy buggy oracle |

Both candidates change only the CarID value consumed by the audio constructor
when it is 26. The native getter still runs for every participant. No vehicle
record, CarClass, model, wheel, physics, unlock, frontend, or race-result field
is changed by the G.2 layer. The existing untuned warning remains intact; a
donor test passes only if the real tuned switch branch executes and the
warning disappears naturally.

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
G.1 patch set and differ from each other only in the donor immediate.

## Evidence boundary

`CONFIRMED_BY_EXE`: the selector, warning branch, fallback, sample-family
switches, scalar immediates, curve-table selection, and common per-slot owner.

`CONFIRMED_BY_CORPUS`: stock vehicle names/classes, WAV availability and
hashes, and the G.1 pristine-to-candidate reproduction.

`READY FOR HUMAN AUDIO A/B`: two deterministic retail candidates and a short
test procedure exist.

`NOT TESTED`: whether either donor is audible, stable, or preferable on
Mercedes ID26. No runtime audio result is claimed.

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
* [ID26 donor policy](id26-policy.md)
* [Fallback behavior](fallback.md)
* [Runtime handoff](runtime-plan.md)
* [Validation](validation.md)

Next step: human audio A/B only. R5V-H AI pools, ordering, ID27+, T2 expansion,
and the generic SDK remain deferred.
