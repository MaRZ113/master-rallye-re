# R5V-F.1 — ID26 cleanup, then Mercedes

## Status

| Gate | Status |
|---|---|
| R5V-F core physical ID26 | **OWNER-REPORTED RUNTIME PASS** |
| ID26 frontend and offline race path | **OWNER-REPORTED RUNTIME-CONFIRMED** |
| Cleanup patch static validation | **PASS** |
| Cleanup P0 | **OWNER-REPORTED FULL PASS** |
| ID26 red canary | **OWNER-REPORTED RUNTIME-CONFIRMED** |
| ID0 stock-colour comparison | **NOT REPORTED; not a blocker for Mercedes source audit** |
| Mercedes source/profile work | **CLEARED TO BEGIN; no candidate yet** |

The earlier R5V-F result reports T1 local7 as physical ID26, with preview,
Quick Race, normal driving, full-stage completion, Race Complete and return to
frontend. For the cleanup candidate, the owner supplied a follow-up report in
the R5V-F.2 master prompt. It identifies the tested EXE as
`120fb40bbe012914b82847f2d78f126dca0a8d6a5459855a7e29386ee63419c9`.

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

The cleanup P0 observations are owner-reported FULL PASS: T1 has eight entries
with ID26 at local7, T2 is back to seven with no false Bowler, T3 remains
intact, and Quick Race shows a valid name. The owner also reports the ID26 red
progress-marker canary in a race. The prompt does not report an A/B runtime
check of ID0's stock colour; the deterministic patch leaves its record
initialization untouched. The F.2 prompt explicitly says this separate ID0
recheck is useful but does not block starting the Mercedes source audit.

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
Candidate construction and archive checks are **AUTOMATED_STATIC**. Cleanup P0,
the corrected group-0x35 name, and the ID26 red marker are **OWNER-REPORTED
RUNTIME-CONFIRMED**. Do not claim the ID0 marker A/B comparison was tested.

See [capacity-fix.md](capacity-fix.md),
[quickrace-localization.md](quickrace-localization.md),
[id26-canary.md](id26-canary.md) and [validation.md](validation.md).

## Two-stage run plan

1. Cleanup P0 is closed by the owner's report in the F.2 master prompt.
2. The ID26 red marker was observed. ID0's stock-colour A/B recheck remains a
   useful open observation but is not a gate for the F.2 source audit.
3. Begin Mercedes evidence and asset research on the same physical ID26/T1
   local7. Do not generate a Mercedes runtime candidate until model, physics,
   collision and dependency gates are satisfied. No ID27 or renumbering is in
   scope.

Detailed steps are in [cleanup/TEST_INSTRUCTIONS.txt](../../research-output/r5v_f_1/cleanup/TEST_INSTRUCTIONS.txt)
and [mercedes-runtime-plan.md](mercedes-runtime-plan.md).
