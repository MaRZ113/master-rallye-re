# R5V-F patch design

## Scope

The candidate supports exactly the clean retail executable hash and one
additional slot: physical ID26, class0/T1 local7, duplicate retail Landcruiser
ID0. It keeps the R5V-E Trooper ID25 profile. It does not implement arbitrary
registry capacity, ID27+, new demo payloads, online support, or campaign
persistence.

## Patcher

`tools/patch_vehicle_registry_id26.py` is deterministic and fail-closed. It
requires the exact retail SHA-256, checks every original byte range, converts
VA values through the verified PE sections, rejects overlapping operations,
requires a zero-filled `.text` cave, refuses source overwrite, and writes only
under `research-output`. It supports dry-run and `--verify-existing`.

The 328-byte code-cave payload starts at `0x68E2A0`; `.text` VirtualSize grows
from `0x28D294` to `0x28D3E8`, still ending below `.rdata` at `0x68F000`. It
contains:

1. a combined record initializer for Trooper ID25 and Landcruiser ID26;
2. a forward sparse class-map wrapper;
3. a reverse sparse class-map wrapper;
4. a display-selector wrapper;
5. an ID26-only unlock wrapper;
6. independent NUL-terminated name literals.

The initialization stub calls the original string constructor and full record
initializer twice, then calls the existing 39-row secondary initializer once.
Capstone decoding of the emitted machine bytes confirms the branch/call targets
and the two initializer sequences. The candidate never raw-copies a
VehicleRecord.

## Operations

There are 69 non-overlapping byte operations:

| Category | Count | Purpose |
|---|---:|---|
| PE bookkeeping | 1 | Map the code cave inside `.text`. |
| Registry allocation | 1 | `0xC00 → 0xC34`. |
| Construction | 2 | Record count 27 and RaceTest base `+0x580`. |
| Destruction | 2 | Matching RaceTest base and record count. |
| Exception unwind | 2 | Matching partial-construction cleanup. |
| Secondary construction | 39 | Move each RaceTest row LEA by `+0x34`. |
| Secondary consumers | 11 | Move each direct row displacement by `+0x34`. |
| Frontend capacity | 2 | T1=8; retain T3=12. |
| Class mapping | 2 | Sparse forward and reverse hooks. |
| Unlock policy | 2 | Preserve ID25 test access and add ID26 selection-only test access. |
| Display localization | 3 | Localize ID26 as ID0 without changing its record ID. |
| Record initialization | 1 | Install the code-cave payload and its literals. |
| Record initialization hook | 1 | Replace only the original `0x4598D0` call at `0x458D3F`. |

The exact operation bytes and semantic owners are in the ignored runtime
`patch-manifest.json` and `binary-diff.txt`; no raw binary or analysis database
is committed.

## Sparse mapping behavior

```text
T1 local0..6 -> IDs0..6 (original)
T1 local7    -> ID26 (new)
T2 local0..6 -> IDs7..13 (original)
T3 local0..11 -> IDs14..25 (original)
ID26 -> T1 local7
```

Display localization alone maps ID26 to donor selector0. Preview, stats, race,
physics and resource lookups retain ID26 and its own record.
