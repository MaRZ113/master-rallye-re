# R5V-H — AI opponent vehicle pools

## Current status

**Static Quick Race pool analysis: CONFIRMED_BY_EXE.**
**Forced Car1=ID26 materialization: CONFIRMED_BY_RUNTIME** for the tested
single-player T1 Quick Race with three AI opponents.
**H.0.1 forced-ID26 Results-name policy: CONFIRMED_BY_RUNTIME.**
**H.0.1 NULL StringList Dump survival: CONFIRMED_BY_RUNTIME.**
**H.0.1 XmlData NULL guard: STATICALLY VERIFIED; isolated runtime status UNKNOWN.**
**H.1 natural T1 ID26 pool and fixed Results label: READY_FOR_HUMAN_RUNTIME.**

R5V-H first proved that an existing AI participant can materialize physical
ID26 without changing the player's vehicle or race count. H.0.1 then closed its
tested Results display and NULL StringList Dump paths. The current H.1 phase
adds ID26 to the natural T1 pool while preserving native driver selection and
the existing participant count.

## Stock Quick Race pool

`FUN_0047B780` calls `FUN_00458090`, which builds a class-specific vector of
absolute physical CarIDs. T1 enumerates IDs 0–6, T2 enumerates 7–13, and T3
enumerates 14–20 plus the four individually progress-gated IDs 21–24. ID25 is
not in the current T3 pool. T1 local7 -> physical ID26 is a separate frontend
mapping and is not called by the AI chooser. The chooser excludes human
vehicles, shuffles the pool, and removes selected IDs as it builds the active
roster.

The native driver chooser runs after the vehicle choice and before participant
publication. At `0x00458428`, stock publishes the selected absolute CarID, then
derives CarClass from `VehicleRecord[CarID]`. The G.1/G.2 runtime identity and
audio path therefore continue to consume ID26 as Mercedes.

## Forced materialization result

The exact H.0 forced proof used the candidate SHA256
`dc821c096dea1db00c91ddf41e85cfac1f5369eaf56bd821ed0b904cbe246e13` and the
capture/raw pair documented in [runtime-results.md](runtime-results.md).
The active capture contains four cars, one human, and Car1 ID26/T1/DriverID8
with Mercedes `CarType` and `WheelType`; its red color matches the ID26 canary.
The human observed the Mercedes actor drive, progress, finish, and appear in
Results. This confirms the bounded Car1 forced proof, not natural T1 pool
eligibility or arbitrary mode/slot behavior.

The exact R5V-H0 hook changes only the selected CarID local for the guarded
Car1/T1/three-AI Quick Race iteration. It does not modify DriverID, CarClass,
Car0, Car2/Car3, `Race/NumCars`, or AI pool membership.

H.1 removes that force and extends only the native T1 candidate vector to
`[0,1,2,3,4,5,6,26]`, retaining native exclusions, shuffle, selection,
DriverID chooser, participant publication, and registry-derived class. It
does not alter participant count or other class pools. The exact candidate
and pending human procedure are in [natural-t1-pool.md](natural-t1-pool.md)
and [natural-t1-runtime-plan.md](natural-t1-runtime-plan.md).

## Race Results name defect

The human reports `GALOCAL UNKNOWN` in the ID26 Results row. Static tracing of
`FUN_0047C840` shows the ordinary AI result-name branch asks localization
group `0x39` for selector `Competitor.CarID`; group `0x39` has no selector 26.
The routine separately builds the result image from the physical CarID. The
H.0.1's forced-test profile used that participant's actual DriverID as the
group-`0x39` selector for AI CarID26 only; this behavior is runtime-confirmed
for its tested rows. H.1 uses a distinct fixed display-only name for physical
ID26. The demo 8.4.1 and 9.3.1 group-`0x39` tables map Mercedes physical ID2
to selector 2, `JOSE MARIA SERCIA`; historical event tables place Servia /
Lurquin in Schlesser T3, while the listed Mercedes T1 crews include Strugo /
Larroque, Lansac / Jacquema, and Menguy / Menguy. The mapping is therefore a
`DEVELOPER-PLACEHOLDER` Mercedes-T1 association, not evidence of an authentic
Mercedes driver assignment. H.1 presents ID26 as `JEAN-PIERRE STRUGO`
(`REAL_2001_MASTER_RALLYE_MERCEDES_DRIVER`); exact ML-320 pairing is unproven.
Neither H.0.1 nor H.1 changes native DriverID selection. See
[the selector audit](historical-driver-selector.md) and
[Results identity trace](race-results-identity.md).

## Neutral hardened research base

The corrected candidate builder composes G.1/G.2 with:

* the legacy loading media-check false-trigger skip;
* NULL guards for native StringList and XmlData Dump paths;
* the profile-specific display-only ID26 Results name selector (H.0.1 follows
  the actual selected DriverID; H.1 returns the fixed historical Mercedes
  display name).

The separate `ordinary-hardened` profile has no forced AI hook and no opponent
randomizer. The `forced-id26-ai-hardened` profile includes only the fixed H.0
proof hook, not the R-AI1.2 randomizer. Both candidates and staged runtime
packages passed deterministic build and on-disk verification. The tested
forced profile confirmed its Results name and post-Results Dump survival. The
natural H.1 candidate and package also pass static/on-disk verification;
natural ID26 selection and its fixed Results label remain pending human
runtime validation.

## Unlock and audio axes

The AI chooser does not call the general player availability predicate.
Player unlock policy and AI pool membership are distinct except where retail
explicitly couples particular progress flags to pool entries. G.1 keeps the
ID26 player unlock behavior independent. G.2's sound constructor reads
physical `Race/CarN/CarID` and maps ID26 to stock audio profile 0 without
changing physical identity.

## Evidence boundary

* `CONFIRMED_BY_EXE`: stock Quick Race pool construction, absolute-ID
  representation, caller frame/guard, post-choice registry-derived class,
  group-`0x39` Results-name producer, and exact H.0.1 patch layout.
* `CONFIRMED_BY_RUNTIME`: the tested forced Car1=ID26 actor/materialization,
  AI movement, progress, finish, Results-row presence, H.0.1 Results identity,
  and post-Results native Dump survival.
* `HUMAN_RUNTIME_OBSERVATION`: the current row's `GALOCAL UNKNOWN` text; the
  supplied capture is active-race state and has no Results NameList payload.
* `READY_FOR_HUMAN_RUNTIME`: H.1 natural T1 pool inclusion and fixed ID26
  Results display policy.
* `UNKNOWN`: isolated XmlData NULL-guard runtime behavior and the exact legacy
  Loading->Attract trigger correction.
* `NOT STARTED`: ID27, T2 expansion, ordering, audio architecture changes,
  and SDK work.
