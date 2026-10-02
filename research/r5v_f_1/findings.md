# R5V-F.1 — ID26 cleanup, then Mercedes

## Status

| Gate | Status |
|---|---|
| R5V-F core physical ID26 | **OWNER-REPORTED RUNTIME PASS** |
| ID26 frontend and offline race path | **OWNER-REPORTED RUNTIME-CONFIRMED** |
| Cleanup patch static validation | **PASS** |
| Cleanup P0 human check | **READY / WAITING** |
| Cleanup P1 independent-record canary | **WAITING FOR P0 FULL PASS** |
| Mercedes asset/profile work | **GATED ON CLEANUP FULL PASS; NOT STARTED** |

The owner reports that T1 local7 is physical ID26, its preview loads, Quick
Race starts, the vehicle drives normally, a full stage completes, Race Complete
is reached, and returning to the frontend works. This establishes the core
registry expansion and race path. The tested EXE hash and captures were not
provided, so this remains owner-reported evidence.

Two defects were reported in that proof candidate:

1. the shared class-capacity immediate accidentally exposes T2 local7, which
   maps through the original dense rules to the canonical T3 Bowler;
2. Quick Race uses localization group `0x35` with selector 26, producing
   `GALOCAL UNKNOWN` and `gaLocal: Can't find id [53]` (`53` decimal is group
   `0x35`).

The cleanup candidate fixes T1/T2 capacity separately, aliases ID26 to donor
selector0 only at the three Quick Race group-`0x35` display lookups, and colors
only `VehicleRecord[26]` red as an independent-record canary. It retains
`Race/Car0/CarID = 26`, the Landcruiser runtime family, the T1/T2/T3 mappings,
the ID25 Trooper profile and the existing VehicleSelect archive.

**No cleanup runtime result is claimed yet. Do not generate or test a Mercedes
payload until cleanup P0 and P1 both pass.**

## Static closure

- Retail source SHA-256 is
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Ghidra Bridge raw assembly at `0x480A20` confirms one `EAX=7` feeds both
  capacity stores at `ESI+0x20` and `ESI+0x24`.
- Ghidra Bridge raw assembly at `0x47B040` contains exactly three Quick Race
  group-`0x35` selectors, at `0x47B0AF`, `0x47B13A` and `0x47B1BA`.
- The `0x4ADFB0` getter returns with `RET 4`; the wrapper copies the stack
  argument before calling it and performs the matching `RET 4` for the caller.
- Ghidra Bridge raw assembly at `0x481E20` and `0x481E50` confirms the false
  T2 entry's `local7 -> ID14 -> T3 local0` path.
- Capstone decoded the emitted capacity/helper bytes and all three redirected
  Quick Race calls. Synthetic tests assert those machine-code semantics.
- `Data.sma` is copied without modification from the prior R5V-F package. Its
  member order, CRCs, `T1_Car8` and `T3_Car12` are validated.

Evidence class: the addresses and raw instruction behavior are
**RAW_GHIDRA_SUPPORTED** and match bytes in the SHA-verified retail executable.
Candidate construction and archive checks are **AUTOMATED_STATIC**. Cleanup
P0/P1 remain **NOT RUNTIME-TESTED**.

See [capacity-fix.md](capacity-fix.md),
[quickrace-localization.md](quickrace-localization.md),
[id26-canary.md](id26-canary.md) and [validation.md](validation.md).

## Two-stage run plan

1. Install only the cleanup candidate EXE and unchanged `Data.sma` into an
   isolated duplicate of the existing Trooper test installation. Perform P0
   frontend checks only; do not start a race.
2. Only after P0 FULL PASS, use that same candidate for P1: ID26 marker red,
   then donor ID0 marker still stock. Report cleanup FULL PASS only if both
   observations match.
3. Only after cleanup FULL PASS begin the separate Mercedes evidence and asset
   audit. The physical slot remains ID26/T1 local7; no ID27 or renumbering is in
   scope.

Detailed steps are in [cleanup/TEST_INSTRUCTIONS.txt](../../research-output/r5v_f_1/cleanup/TEST_INSTRUCTIONS.txt)
and [mercedes-runtime-plan.md](mercedes-runtime-plan.md).
