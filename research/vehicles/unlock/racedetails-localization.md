# G.1 Mercedes Race Details localization

## Final status

**CONFIRMED_BY_RUNTIME** for single-player Master Rallye and Rallye Cup on the
final candidate (`722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`).
Human observation confirms that `MERCEDES ML-320` is visibly rendered in both
Race Details screens. The two Broker snapshots agree and preserve physical
CarID 26 / T1. The stock ID0 Race Details regression and full stage/Results are
also PASS by the owner's human runtime report. Frontend return was not
specifically reported.

## Producer and identity source

Master Rallye and Rallye Cup share writer `FUN_0047C080` for
`Frontend/RaceDetails/CurrentVehicleString`. It reads an absolute vehicle ID
from `RaceData/CompetitorN/CarID` through `FUN_004B0AF0` and `FUN_004B0630`,
then queries localization group `0x35`. It does not read
`Race/Car0/CarID` directly and does not use a class-local selector.

| Branch | Participant | Hook starts | Group push | `gaLocal` call | Resume |
|---|---:|---:|---:|---:|---:|
| Split-screen first participant | Competitor0 | `0x0047C0F5` | `0x0047C0F6` | `0x0047C0FA` | `0x0047C0FD` |
| Split-screen second participant | Competitor1 | `0x0047C181` | `0x0047C182` | `0x0047C186` | `0x0047C189` |
| Single-player | Competitor0 | `0x0047C200` | `0x0047C201` | `0x0047C205` | `0x0047C208` |

The final implementation checks the display selector. ID26 returns the
existing `MERCEDES ML-320` presentation; every other ID replays the exact
original group-`0x35` lookup. It changes neither the physical CarID nor global
`gaLocal` behavior and does not remap a donor ID.

## Runtime before and after

| Mode | Before | Final candidate |
|---|---|---|
| Master Rallye | `GALOCAL UNKNOWN` | `MERCEDES ML-320` |
| Rallye Cup | `GALOCAL UNKNOWN` | `MERCEDES ML-320` |

The final captures are `20261006-173146_g1-racedetails-masterrallye` and
`20261006-173057_g1-racedetails-rallyecup`. Both report the exact final EXE
hash and active `runtime-package` Root. Raw sidecars match metadata:

* Master Rallye: `6ca9ebf726c1be8f871091a5704fa45fef22a6d8122a3af1a1f2b39b5c0d16a7`.
* Rallye Cup: `ec88c4c88c7517929b71e091fe433a195c97c550e5fa203f17c352d4aeffad02`.

Master Rallye capture values: `LEG 1/10 - FRANCE`, mode `MASTER RALLYE`,
`RaceData/Competitor0/CarID=26`, `Race/Car0/CarID=26`, and
`Race/Car0/CarClass=0`. Rallye Cup values: `RACE 1/3`, mode `RALLYE CUP`, and
the same participant identity/class. Race-description strings are capture-
specific, not fixed invariants. The human saw the correct rendered Mercedes
name in both screens; Broker text alone is not visual proof.

No human split-screen Race Details test is claimed. The two split-screen
branches are **STATICALLY COVERED BY THE SAME BOUNDED ID26 WRAPPER**. Challenge
and Trophy consumers were not modified or qualified for ID26.

See [runtime captures](runtime-captures.json), [validation](validation.md), and
[G.1 closeout](closeout.md).
