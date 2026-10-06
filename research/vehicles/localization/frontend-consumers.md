# Frontend vehicle identity writers

The same vehicle can pass through several independent presentation writers.
The string already present in a Broker path is not guaranteed to refresh when
Vehicle Select changes; each consumer has its own owner and timing.

## Confirmed vehicle-name consumers using group `0x35`

| Owner | Lookup VA(s) | Consumer | ID26 handling in this correction |
|---|---|---|---|
| `FUN_0044F8E0` | `0x0044FA29` | Vehicle Setup `CarName`; EDI is physical ID | new ID26-only combined string wrapper |
| `FUN_0045EB30` | `0x0045EC5A`, `0x0045ECBF` | Challenge preview `Car1Text` / `Car2Text` | unchanged; Challenge opponent pool is out of scope |
| `FUN_0047B040` | `0x0047B0B4`, `0x0047B13F`, `0x0047B1BF` | Quick Race summary strings | existing ID26-only direct string wrappers |
| `FUN_0047C080` | `0x0047C0F6`, `0x0047C182`, `0x0047C201` | Race Details vehicle-name fields | unchanged in this phase |
| `FUN_004803A0` | `0x004805E6` | Trophy `VehicleUnlockedText2` | unchanged; reward presentation is separate |

These ten sites are the vehicle-name group-0x35 consumers found in the bounded
retail xref inventory. The Vehicle Setup bug was the uncovered consumer in the
current ID26 frontend flow. No global `gaLocal` behavior is changed.

## Other retail pushes of group `0x35`

The other ten static pushes in the bounded xref inventory are not vehicle-name
lookups: `0x00460E50` routes through progress helpers; `0x00465F53`,
`0x00481612`, `0x004817D9`, `0x00482D5E`, `0x004837FE`, `0x0048423E`, and
`0x0048505E` route through menu/action-index handling; `0x004AF87A` routes
through an indexed helper; and `0x005CFB68` is a generic storage/helper path.
They are not patched.

## Other vehicle identity channels

* Vehicle Select `FUN_004819B0`: manufacturer group `0x33`, model group
  `0x34`; the existing ID26 wrappers return `MERCEDES` / `ML-320`.
* Quick Race summary: group `0x35`; existing hooks return `MERCEDES ML-320`.
* Race Options `FUN_0047A540`: manufacturer group `0x33` at `0x0047A65F`,
  model group `0x34` at `0x0047A6C4`; existing hooks keep the split semantics.
* Vehicle Setup `FUN_0044F8E0`: combined group `0x35` name; the new wrapper
  returns the exact existing `MERCEDES ML-320` spelling.
* Runtime `CarType` and `WheelType` remain registry/runtime identity and are
  not localization selectors.

## Writer chronology relevant to ID26

Vehicle Select writes its own manufacturer/model state. The Quick Race summary
path has three group-0x35 lookups and may leave its prior Broker value until
that screen refreshes. Race Options independently writes the manufacturer and
model fields. Vehicle Setup then independently computes `CarName` from the
selected physical ID and was the path that emitted `GALOCAL UNKNOWN` for ID26.
The correction addresses this last writer without changing the earlier
consumers or physical identity.

## Failure classification from the captures

* **Stale value — confirmed:** after Vehicle Select reports ID26, the Quick
  Race key can still contain prior donor text until its own screen refresh runs.
* **Independent lookup — confirmed:** the Race Options refresh
  `FUN_0047A540` sends physical ID26 into groups `0x33` and `0x34`. The earlier
  F.2e candidate therefore produced `GALOCAL UNKNOWN`; F.2f added bounded
  ID26-only manufacturer/model wrappers.
* **Post-override overwrite — not supported:** the capture/reference sequence
  did not show a correct Race Options string being written and then replaced by
  `GALOCAL UNKNOWN`.
* **Split identity path — confirmed:** the manufacturer key is written only by
  the group-0x33 path, while the combined group-0x35 Quick Race writer can
  refresh `CurrentVehicleString` later without touching the manufacturer key.
  This explains how a combined Mercedes value could coexist with a stale
  manufacturer value in the earlier capture.

Vehicle Setup is another independent group-0x35 lookup. Its ID26 failure is
not a stale Quick Race field: `FUN_0044F8E0` passes the physical ID into the
group-0x35 table and receives `GALOCAL UNKNOWN` at `0x0044FA29`. The G.1
correction adds an ID26-only return at that consumer and leaves all unrelated
group-0x35 calls unchanged.

The proven screen order is therefore: Vehicle Select writes its own identity;
the Quick Race summary refresh writes the combined string; Quick Mode Select /
Race Options independently writes manufacturer and model; returning to the
Quick Race summary invokes its own refresh again. The active-race capture shows
the combined-name path can refresh while the separate manufacturer key remains
from its prior writer. No distinct race-launch-only writer for these keys was
isolated, and the new G.1 candidate has not yet been captured on frontend
return; those states should not be assigned a separate writer without new
evidence.
