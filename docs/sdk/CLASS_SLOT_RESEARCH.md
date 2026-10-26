# Further vehicle class-slot capacity — Heritage research

27 October 2026. This is an evidence update, not a capacity increase in the
Heritage candidate. The owner-confirmed SCALE1 maximum remains30 active records
with class counts8/10/12. No universal engine maximum is established.

## Original native evidence, rechecked with REA/Ghidra12.1.4

Retail EXE SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Private REA evidence and snapshot: `vehicles_scratch/heritage/` (ignored).
Exact original instruction bytes were independently read from the loaded image;
no original file was modified.

| Native consumer | Observed behavior | Consequence |
|---|---|---|
|00480A20|Class counts at+20/+24/+28 initialized7/7/11|Defaults, not universal engine maxima|
|00481F50|Navigation reads current class count and per-class selection|No independent12 bound in this navigation helper|
|00481950|Formats position keys using index, selection and100px spacing|A UI-key publisher, not a vehicle-record array|
|004819A4|`83 FE 0C 7C B1`: CMP ESI,12; JL0048195A|Original publisher covers indices0–11|
|00481E20/00481E50|Dense maps use class thresholds7/14|Further slots require explicit mapping, not only changing counts|

Evidence IDs: publisher pseudo `ev_66feb23ff3d0b287f73e2e819d1852b23959406e197ff08beb761196798589bb`,
assembly `ev_853dcfd1faac91169b3bf35701ac44d0ea89f5c69181e180d75bbc2d6532fa24`,
bytes `ev_f9cec91a65cdf5c568e685dd445479133c0224588d4d974d97c06ed0eede4b60`.
Pseudocode is not original source; the CMP/JL statement is independently supported
by instruction bytes and assembly.

## New controlled experiment

`tools/validate_class_slot_research.py` runs original x86 helpers in Unicorn,
with typed formatting/Broker calls isolated. It does not create a runtime patch.

- Original publisher emits keys0–11.
- Emulator-private hypothetical CMP bounds13 and16 emit exactly13 and16 keys,
  without exceeding the original stack string buffer in these tested inputs.
- Original navigation with a configured count13 advances11→12 and refuses to
  advance12 further, independently for T1/T2/T3.

This demonstrates that12 is not intrinsic to those helper calculations. It does
**not** prove UI nodes exist, image-bank frames are assigned, a larger roster
spawns, or saves/AI work. No hypothetical instruction is written into the
Heritage launcher, runtime manifest or original EXE.

## Practical next bounds

| Layer | Current finding |
|---|---|
|Owner gameplay qualification|29 and30 records, including AI/Results/re-entry, preserved|
|Production multi-addon builder|Explicit IDs28/29 in T2 local8/9; unchanged|
|Existing lower native emitter|Append within12 positions; T1 needs AI disabled; T2 audited pools only|
|Arithmetic remaining under that publisher|T1:4 slots; T2:2 slots; T3:0 from8/10/12|
|Theoretical12/12/12 layout|36 total; not a demonstrated safe roster and not newly built here|
|Older32-record experiment|Historical helper emulation only, not owner gameplay proof|
|Signed immediate guard128|Current generated-code encoding restriction, not proven engine/global limit|

Further T2 slots within12 are the smallest next experiment: qualify31, then32
individually using explicit resources, independent UI allocation, actor ownership
and whole race/re-entry tests. T1 additionally requires auditing its AI pool
owners before AI participation. T3 is already at the current publisher boundary;
slot13 would need a separately qualified publisher, new widget/frame allocation,
T3 forward/reverse mapping, unlock/localization/AI registration and persistence
checks. Enlarging only a class count is insufficient.

Global record allocation,52-byte stride, relocated44-byte RaceTest tables,
resource/audio owners, UI banks and save compatibility remain separate limits.
A private code allocation solves code storage, not all these consumers. No
unlimited count, safe36, ready T3 expansion or new engine maximum is claimed.

The original executable and qualified30-entry infrastructure remain untouched.
