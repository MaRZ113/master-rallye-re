# AI vehicle identity architecture

## Quick Race setup path

1. `FUN_0047B780` publishes the player's selected absolute ID from
   `Frontend/QuickRace/Car0` to the race participant state and derives that
   player's class from its VehicleRecord.
2. The one-human path calls `FUN_00458090` at `0x0047B96E` with starting slot
   1, the active AI count, the player's class, the player's physical CarID as
   an exclusion, and `-1` as the second-human exclusion. The split-screen path
   calls it at `0x0047B93D` with its two human exclusions.
3. `FUN_00458090` builds a vector of absolute CarIDs for the supplied class,
   removes the excluded humans, then selects and removes entries from a
   shuffled working list. It does not call the class/local mapper.
4. For each AI slot, the selected CarID is retained in a local value. The
   driver chooser `FUN_00458980` is invoked before publication.
5. At `0x00458428`, retail loads the selected value from `[ESP+0x14]` and pushes
   it to the participant writer. `FUN_004ACAF0` publishes CarID. The following
   code uses the same ID to find `VehicleRecord[CarID]`, reads its class field
   at `+0x0C` (record stride `0x34`), then writes CarClass through
   `FUN_004ACC10`; DriverID is written through `FUN_004ACCD0`.
6. The G.2 engine-audio constructor later reads the participant's physical
   `Race/CarN/CarID`; physical ID26 is mapped to stock audio profile 0 without
   changing CarID.

## Static facts

| Identity | Representation | Evidence |
|---|---|---|
| Player selected vehicle | absolute CarID in Quick Race state | `FUN_0047B780` reads Car0/Car1 and publishes physical ID |
| AI candidate vehicle | explicit absolute ID vector | `FUN_00458090` loops/appends physical IDs per class |
| T1 local7 | physical ID26 in the G.1 frontend mapper | G.1 registry manifest and runtime closure |
| AI T1 before H | IDs 0–6, no sparse mapping call | current retail Ghidra export + raw bytes |
| Race CarClass | registry-derived field from selected CarID | code after `0x00458428` reads record `+0x0C` |
| AI DriverID | selected by separate helper before CarID publication | `FUN_00458980(&local_68)` at `0x00458423` |
| ID26 audio family | stock profile 0, physical ID unchanged | G.2 static and runtime closeout |

## Diagnostic proof hook

The H.0 forced candidate hooks the five retail bytes at `0x00458428`:

```text
8B 44 24 14 50    mov eax,[esp+14h]; push eax
```

The replacement jump enters a small code stub at `0x0068E690`. Reanalysis with
Ghidra 12.1.4 headless found exactly two references to `FUN_00458090`, both in
`FUN_0047B780`: the single-human branch at `0x0047B96E` passes start slot 1,
and the split-screen branch at `0x0047B93D` passes start slot 2. Thus an
iteration with ESI==1 is single-human-only for the mapped Quick Race owner.
The setup computes EBP as `start + active AI count`; EBP==4 selects exactly
three AI slots beginning at Car1. The retained class argument is at
`[ESP+0x8C]` at publication and is read for pool construction; no write to that
argument slot appears in the function listing. The other exclusion inputs are
not stable at publication: the function copies them into registers and later
reuses those registers for shuffle/loop state. The caller return address is
redundant once the live slot, end slot, and class guards are combined.

The corrected stub therefore has only three guards: ESI==1, EBP==4, and class
0/T1. On a match, it changes only the selected-ID local `[ESP+0x14]` to 26.
All paths replay the original five bytes and jump to `0x0045842D`. It does not
require Car0 ID0, although ID0 remains the human runtime-test control. This is
static call-graph/frame evidence. The corrected H.0 candidate later passed the
human materialization test: the active capture records Car1 ID26/T1 and
Mercedes runtime identity, and the human observed AI movement, progress, and a
finish. This closes only the bounded forced proof.

The native publication and class derivation then consume physical ID26. H does
not separately write CarClass, DriverID, participant count, model, wheel,
physics, or audio state. Exact candidate identity and byte ranges are in the
ignored research-output manifest; a non-proprietary summary is in
[validation.md](validation.md).

The H.0.1 Results-name correction is a separate display consumer: the stock
Race Results builder uses physical CarID as its group-`0x39` AI name selector,
which has no ID26 row. The bounded candidate substitutes the participant's
DriverID only for an ID26 AI name lookup; it does not change physical CarID or
the driver chooser. That fix remains **READY_FOR_HUMAN_RUNTIME**; see
[race-results-identity.md](race-results-identity.md).

This is a causal AI-materialization experiment only. It does not add ID26 to
the natural AI pool. The ordinary hardened test candidate contains neither
this forced selection hook nor an opponent randomizer.
