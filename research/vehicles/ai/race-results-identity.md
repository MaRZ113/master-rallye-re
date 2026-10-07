# ID26 Race Results name identity

## Original runtime symptom and H.0.1 result

The H.0.1 forced-ID26 human run reached Race Results and displayed
`GALOCAL UNKNOWN` for the Mercedes participant. The available Observatory
capture `20261007-111017_h0-forced-id26-ai` was taken during the active race;
it confirms `Race/Car1/CarID=26`, `CarClass=0`, and `DriverID=8`, but it does
not contain a post-Results `Frontend/RaceResults/NameList` snapshot. The visible
label is recorded as a human observation, not a parsed NameList value.

## Native producer

`FUN_0047C840` constructs the Race Results lists. It iterates the native
competitor records, publishes each result image from the participant's
physical CarID, and separately builds the `Frontend/RaceResults/NameList`.
The ordinary AI-name branch passes localization group `0x39` and the
competitor record field at `+8` to the native localization lookup. The same
field is the physical CarID used by this routine's result-image lookup. The
record field at `+4` is the DriverID; its meaning is corroborated by the
participant-record construction path and the observed H.0 pair
`CarID=26` / `DriverID=8`.

Human names (`DriverID` 30 and 31) take separate player-name branches before
the patched AI lookup. Network-style name formatting also has its own branch.
Neither is changed here.

The inspected language tables contain group-`0x39` selectors `0..24` and
reserved selectors `40..47`, but no selector 26. Passing physical ID26 to this
group therefore reaches the stock `GALOCAL UNKNOWN` fallback. This is a
presentation identity gap; the runtime model, physics, wheel family, CarID,
and class are already correct.

## H.0.1 runtime-driver correction

The H.0.1 candidate replaces the 11-byte sequence at VA `0x0047CC71` / file
offset `0x07CC71`:

```text
stock:  8B 0C AE 8B 10 8B 49 08 51 6A 39
patch:  E9 AA 1A 21 00 90 90 90 90 90 90
```

The stub at VA `0x0068E720` reloads the native competitor record and its
physical CarID. For ID26 only, it substitutes the record's DriverID as the
group-`0x39` name selector; every other AI keeps the original CarID selector.
Both paths push group `0x39` and resume at `0x0047CC7C`, where retail performs
the original localization call. The emitted stub does not write a participant
field or alter CarID, CarClass, driver selection, the result icon, or race
progression.

That tested profile followed the **actual AI driver identity** selected by the
native path. It did not hardcode DriverID 8, a Mercedes display string, or an
authored driver. The two H.0.1 Results captures showed CarID26/DriverID6 ->
`BRUNO SELLIER` and CarID26/DriverID2 -> `TESSA BAMFORD`; the human confirmed
the visible Results names. The H.0.1 runtime-driver display policy is
**CONFIRMED_BY_RUNTIME** for those tested Quick Race rows. It did not globally
change `gaLocal` or any stock localization row.

## Demo group 0x39 audit and current H.1 policy

Exact-hash inspection of demo-8.4.1 and demo-9.3.1 shows physical Mercedes ID2
reaches group-0x39 selector 2, which maps to `JOSE MARIA SERCIA` in both
builds. Historical 2001 result tables put Servia/Lurquin in a Schlesser T3
entry and separately list the Mercedes T1 crews Strugo/Larroque,
Lansac/Jacquema, and Menguy/Menguy. The demo mapping is therefore classified
`DEVELOPER-PLACEHOLDER` as a Mercedes T1 name association; this does not assert
that the referenced Servià is fictitious. Full row offsets, hashes, and
historical links are in [historical-driver-selector.md](historical-driver-selector.md)
and [demo-group-39.json](demo-group-39.json).

The H.1 `natural-t1-id26` candidate uses a distinct display-only ID26 branch:
it returns the literal `JEAN-PIERRE STRUGO` to the same stock string consumer,
classified `REAL_2001_MASTER_RALLYE_MERCEDES_DRIVER`. The exact ML-320 pairing
is unproven. The H.1 result display hook is at `0x0047CC71`; its 60-byte helper
and NUL-terminated string occupy `0x0068E720..0x0068E75C`. Other AI rows still
use the original CarID -> group-0x39 path. Native DriverID selection,
participant DriverID, CarID26, CarClass, and vehicle family are not changed.
At initial handoff this fixed H.1 policy was marked **STATICALLY VERIFIED /
READY_FOR_HUMAN_RUNTIME**. That historical status is superseded by the H.1
natural Quick Race runtime closeout in [runtime-results.md](runtime-results.md);
the completed Results capture shows the physical ID26 AI at Rank 2 with the
fixed display name.

## Verification status

Synthetic x86-path tests verify the H.0.1 ID26 -> DriverID selector and the
H.1 fixed-ID26 literal path, non-ID26 -> original CarID selector, localization
group `0x39`, preserved native DriverID/physical identity, and both hook
continuations. The H.1 candidate builder verifies the retail and neutral-base
hashes, exact loop/hook bytes, zero-filled non-overlapping caves, PE bounds,
deterministic output, and inverse patch reproduction.

Status: H.0.1 runtime-driver policy **CONFIRMED_BY_RUNTIME** for its two
captured names. H.1 fixed `JEAN-PIERRE STRUGO` Results identity is also
**CONFIRMED_BY_RUNTIME** for the completed natural Quick Race capture. This
confirms the tested Results row; it does not alter native DriverID selection
or claim an exact ML-320 pairing.
