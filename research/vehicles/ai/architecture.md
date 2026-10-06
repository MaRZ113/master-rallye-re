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

The forced candidate hooks the five retail bytes at `0x00458428`:

```text
8B 44 24 14 50    mov eax,[esp+14h]; push eax
```

The replacement jump enters a small code stub at `0x0068E690`. The stub checks
the return address for the one-human Quick Race call (`0x0047B973`), ESI for
Car1, EBP for end slot 4, class argument 0, player CarID 0, and second excluded
CarID -1. On a match, it changes only the selected-ID local `[ESP+0x14]` to 26.
All paths replay the original five bytes and jump to `0x0045842D`.

The native publication and class derivation then consume physical ID26. H does
not separately write CarClass, DriverID, participant count, model, wheel,
physics, or audio state. Exact candidate identity and byte ranges are in the
ignored research-output manifest; a non-proprietary summary is in
[validation.md](validation.md).

This is a causal AI-materialization experiment only. It does not add ID26 to
the natural AI pool.
