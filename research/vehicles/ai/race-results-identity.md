# ID26 Race Results name identity

## Runtime symptom and evidence limit

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

## Bounded correction

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

This intentionally follows the **actual AI driver identity** selected by the
native path. It does not hardcode DriverID 8, a Mercedes display string, or an
authored driver. It also does not globally change `gaLocal` or any stock
localization row.

## Verification status

Synthetic x86-path tests verify ID26 -> DriverID selector, non-ID26 -> original
CarID selector, localization group `0x39`, and unchanged physical identity.
The candidate builder verifies the retail hash, exact hook bytes, zero-filled
non-overlapping cave, PE bounds, deterministic output, and inverse patch
reproduction.

Status: **STATIC FIX VERIFIED / READY_FOR_HUMAN_RUNTIME**. The forced
H.0.1 candidate must be tested through Results to prove the displayed localized
driver identity. Automated candidate verification cannot prove the visible
name.
