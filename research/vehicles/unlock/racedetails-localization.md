# G.1 Mercedes Race Details localization

## Status

The native producer and selector source are statically traced. The bounded
ID26-only candidate is built and installed in the verified runtime package.
Human verification of both Race Details modes and a short race regression is
still required; do not call this localization fix runtime-confirmed yet.

## Producer and identity source

Both Master Rallye and Rallye Cup use the shared writer `FUN_0047C080` for
`Frontend/RaceDetails/CurrentVehicleString`. The function reads participant
identity through the existing `RaceData/CompetitorN` accessors initialized by
`FUN_004B0AF0`; `FUN_004B0630` reads the `CarID` field and returns the absolute
vehicle ID in EAX. The value is passed to localization group `0x35`. This is
not a direct read of `Race/Car0/CarID`, nor a class-local selector.

The writer has three equivalent lookup sites:

| Branch | Participant | Hook begins | Group push | gaLocal call | Resume |
|---|---:|---:|---:|---:|---:|
| Split-screen first participant | Competitor0 | `0x0047C0F5` | `0x0047C0F6` | `0x0047C0FA` | `0x0047C0FD` |
| Split-screen second participant | Competitor1 | `0x0047C181` | `0x0047C182` | `0x0047C186` | `0x0047C189` |
| Single-player | Competitor0 | `0x0047C200` | `0x0047C201` | `0x0047C205` | `0x0047C208` |

The ordinary single-player Master Rallye/Rallye Cup path uses the third site.
The other two branches are covered by the same ID26-only presentation rule.

## Observed failure and correction

The pre-fix Master Rallye and Rallye Cup captures both had
`Race/Car0/CarID=26`, `RaceData/Competitor0/CarID=26`, and
`Frontend/RaceDetails/CurrentVehicleString="GALOCAL UNKNOWN"`. Their mode and
event-description fields were otherwise populated normally. This is an
independent group-`0x35` lookup, not an ID alias or race-mode error.

The G.1 final candidate compares the absolute selector with 26. For ID26 it
returns the existing shared presentation string `MERCEDES ML-320`. For every
other ID it replays the original eight-byte group-`0x35` lookup sequence and
resumes at the original continuation. The same implementation covers both
modes through their shared writer; it does not change challenge rules, event
text, class, physical registry state, or save identity.

The change is added only to the G.1 profile. The earlier F.2f candidate and
other vehicle profiles do not receive these hooks. All three original byte
sequences are checked before patching and by deterministic candidate
verification.

## Candidate and deployment

* Source: pristine retail `MRallye.exe`, SHA256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
* Candidate: `MRallye_g1_final_racedetails.exe`, 3,121,214 bytes, SHA256
  `722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`.
* Three added hooks: `0x0047C0F5`, `0x0047C181`, and `0x0047C200`; 78 total
  patch operations in the final G.1 manifest.
* Existing Vehicle Select scene overlay SHA256 remains
  `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`.
* The candidate is staged at the effective executable and resource Root in
  `.research-output/vehicles/unlock/runtime-package/`. The package verifier
  allows existing runtime state only when explicitly requested and does not
  include save contents in its manifest.

## Runtime gate

The human test must visibly check `MERCEDES ML-320` on Race Details in both
Master Rallye and Rallye Cup, and confirm each mode's current race text still
looks correct. Include one stock ID0 display control. A Broker capture should
show the relevant mode, `RaceData/Competitor0/CarID=26`,
`Race/Car0/CarID=26`, and the new Race Details string. Broker values establish
state only; the visible screen establishes rendered presentation. One short
ID26 race smoke checks that `CarID=26`, T1 class, Mercedes `CarType` and
`WheelType`, and the known colour canary remain intact. A complete
stage/results/return lifecycle is not required or claimed here.
