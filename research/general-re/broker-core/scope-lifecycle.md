# Scope and lifetime

## What is established

`CONFIRMED_BY_EXE`: scope is entry +0x14, independent of SaveFile and save bits.
The Dump labels 0 GLOBAL, 1 SCENE, others USER. `004D5AF0` sets the numeric field
without an inherent revision update. Typed fresh entries default to 1.
DataGame Value conversion `005FE120` explicitly assigns **0 GLOBAL**, even when
its load-mode flag disables saving. XML does not serialize this field.

`004D7A60(scope)` walks the manager and resets matching live entries.
`004D7800` clears all live payloads without itself proving a scene policy.
Whole Game reset `00522910 → 004D7830 → 004D7BD0` clears/re-registers the
database and rebuilds engine owners/factories. GLOBAL is therefore not immortal.
Editor acceptance preserves the source scope or uses its local default.

## What runtime evidence actually shows

The owner's provided frontend/race snapshots contain SCENE rows and zero USER
rows. The four root `Car0..Car3` XmlData entries in race are **GLOBAL** with
`__NO_SAVE`. Runtime vehicle/physics ownership is not inferable from a scope
label alone. `CarN`'s lifetime can be controlled by its owning subsystem and
explicit removal/replacement. These observations are `CONFIRMED_BY_RUNTIME`
for the supplied states, not for all scene transitions.

## Sharply bounded unknowns

`CONFIRMED_BY_RUNTIME` U1: race Broker SCENE state survives RaceRetry, QuickRace
and GameSelect. SCENE is not the current DataScene XML lifetime. This observation
does not identify the normal bulk-clear owner, which remains UNKNOWN.

No direct call or validated raw E8 candidate to `004D7A60` was recovered. Scene
teardown `00522480` resets many subsystem owners, but a call from those owners
to this scope-clear primitive was not established. Inline clearing, virtual
cleanup or explicit per-key removal remain possible. We do **not** claim that
all SCENE entries automatically disappear on every scene load.

USER is currently a **display classification for other numeric scope values**.
No authoritative producer or destruction policy for those values was recovered.
It does not mean SavePlayerState; the fields are independent. This is the main
remaining architecture blocker, targeted by human U1 and a narrow static
owner-cleanup follow-up. No new research branch is started here.
