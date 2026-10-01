# ID26 bounds and other registry consumers

## ID26 player path

The intended test path is the offline Vehicle Select / Quick Race player path.
On that path:

1. T1 local7 maps to absolute ID26.
2. The narrow Vehicle Select unlock wrapper makes ID26 selectable.
3. The updated heap registry and expanded direct row allocation make
   `VehicleRecord[26]` addressable.
4. The frontend retains EDI=26 for record-based stats and resource lookup.
5. Quick Race carries the absolute `CarID=26` into the race setup record; the
   name field resolves Landcruiser resources and named physics.
6. HUD race colour and SmallCarSheet paths index the same record and fields.

The critical absolute-ID accessors do not maintain a separate 26-element copy
of the vehicle records. Their record pointer comes from the singleton registry
getter, whose allocation is expanded in this candidate.

## Fixed or bounded consumers

| Address / function | Original limit or role | ID26 treatment |
|---|---|---|
| `0x45A150` | 26-case unlock switch; checks `ID > 25` before its jump table | The default path is in-range and returns a byte; a caller-only wrapper forces true for ID26 after the original check. No table is indexed at 26. |
| `0x481E20` | class/local → absolute ID | Hook adds only `class0/local7 → 26`; all other inputs replay the original instructions. |
| `0x481E50` | absolute ID → class/local and common UI update | Hook adds only `26 → class0/local7`; other IDs replay the original prologue and body. |
| `0x481AC7` | model-name selector switch through ID25 | Its initialized default selector is ID0; ID26 safely gets the donor model-label fallback. Localization identity is explicitly aliased to ID0 at the two string-group lookups. |
| `0x4584F0` | campaign/event opponent pool, IDs0–24 | Remains stock-only; ID26 is not added to AI/event generation. |
| `0x4389C0` | network participant clamp through 25 | Remains unchanged. ID26 network support is unproven; online tests are excluded. |
| logo-ID converters near `0x46B560`, `0x46CEB0`, `0x47A540`, `0x47B040` | network/QuickRace logo identity; IDs25–35 use an 11-entry table | ID26 maps to index1 inside that table. These are not registry record arrays. |

The original event pool and online clamp are documented scope limits rather
than silently expanded. They do not participate in the isolated offline player
P0 path; AI/event and network use remain unsupported for this proof.

## Secondary-array references

The RaceTest rows live after the main registry in the same allocation. This
candidate shifts the row base and updates the 39 constructor LEAs and 11 direct
reader operands. See the complete address list in
[construction-destruction.md](construction-destruction.md). The visually
similar anonymous-object fields near `0x40A6B9` and larger physics-object
offsets are distinct structures and are not modified.

## Persistence and identity risks

Quick Race stores an absolute ID in its scene property, but campaign/save
bitset sizing and persistent ID26 round-trip behavior are not proven. Do not
use a permanent profile or campaign save; use a disposable profile for P0 and
P1. Do not test online. The proof only targets a selected player vehicle in an
offline session and does not add ID26 to opponent selection.

No additional `<=24` / `<25` hard check was identified on the traced P0 and
offline P1 path after the mapping and unlock wrappers. The remaining known
limits are the explicitly excluded AI/event, persistence and network systems.
