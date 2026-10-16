# Fleet conditional rear OFF lamp source inventory

## Decision

**21 exact source profiles**, including the accepted Kia, X-Trail and Terrano
identities, are eligible for the existing bounded native Mode4 OFF transaction.
This adds18 source profiles. It does not certify21 live vehicles, damaged
variants or arbitrary lamp surfaces. Original native ON selection and the
separate25-profile additive glow path remain unchanged.

The registry is `fleet_off_lamp_registry_draft.hpp`. Integration must retain
current owner, resource generation/revision, complete mirrored range, native
WORLD, state/dependency and single-draw restoration checks. The source registry
does not replace these runtime gates. Existing Terrano/X-Trail damage-specific
contracts must remain separately enforced; this static fleet registry does not
authorize damaged geometry or a weaker identity.

## Source proof

`audit.py` verifies canonical PS2 archive inputs and the original PS2/PC CAR SHA
for every25 selected playable families. It selects explicit conditional
carshiny mode3/mixed roots only inside the same authored PS2 root family as a
known brake-glow branch. It then joins to the original PC **blight** owner and
its authored children, comparing each complete triangle's positions and UVs.
The established source-comparison limits remain .001 position / .000001 UV.
Runtime guards are exact SHA256 of original PC geometry and position+UV corners:
no runtime tolerance, texture-only alias or draw ordinal is admitted.

This explicitly excludes Navara's four damaged-window carshiny alternatives,
which otherwise also look like conditional mode3. Likewise, unknown UFO
carbrakelight generic perspex is not silently renamed carshiny.

Every other compiled CAR record is a negative against the exact profile pair,
including ON, glow, interior, windows and body records. Some OFF/ON pairs share
position geometry; UV remains mandatory. No selected OFF geometry+UV pair
collides with any other record in its family or any other admitted family.

## Coverage

All rows below are source eligibility, not new user-runtime PASS.

| PC family | original OFF record | result |
|---|---:|---|
| Astero |31|exact profile|
| Bruno |20|blocked: original geometry corresponds, UV residual0.00018972158432006836 exceeds1e-6|
| ChevyBlazer |33|exact profile|
| Frontera |33|exact profile|
| IceCream |26|exact profile|
| Jump |29|blocked: original XYZ revision differs by0.0024013519287109375|
| Kamaz |24|exact profile|
| Kangoo |28|exact profile|
| KiaSportage |30|exact profile; user confirmed existing corrected OFF behavior|
| LandCruiser |32|exact profile|
| Mattserati |25|blocked: original XYZ revision differs by0.008023202419281006|
| megane |26|exact profile|
| Navara |28|exact profile; window alternatives excluded|
| NewRav |34|exact profile|
| Pajero |24|exact profile|
| Patrol |29|exact profile|
| RMonster |22|exact profile|
| SeatBuggy |24|exact profile|
| Simmbugghini |25|exact profile|
| Tata |30|exact profile|
| Terrano |32|existing exact profile retained|
| Ufo |—|no independently verified carshiny/mixed conditional OFF source|
| WildCat |28|exact profile|
| PC Forester / PS2 WOOLDAND |26|exact profile; PS2 FORESTER remains distinct|
| Xtrail |23|existing exact profile retained|

Record numbers are positions in the immutable original resource parser output,
never live draw sequence identities. Forklift is deliberately omitted.

## Tests and local fixture

Five focused tests pass: exact original guard bounds; all ON/glow/body negative
identity pairs; existing Kia/X-Trail/Terrano constants; precise exclusions and
WOOLDAND pairing;21-positive fixture inventory.

`prepare_fixtures.py` creates ignored local
`.assets/vehicles/fleet-off-lamp-native.bin`:774 original PC records encoded
FVF0x152/stride36,21 OFF positives and753 negatives. SHA256
`bf03e11485f7b09d043b8819d3cc8c181ac1612aaee302b8c7350d5837b33875`.
FormatPS2LMP01, kind0 positiveOFF, kind3 negative, IDX32. These are original
source fixtures, not captured uploads. Do not ship or commit their bytes.
Native regression should additionally mutate XYZ/UV/index data and resource
generation and verify rejection, preserving exact setter rollback/restoration.

## Runtime boundary and smallest next steps

No renderer/build changes were made here. Main-agent integration can add the
21-row exact lookup while keeping existing special damage guards and optional
logging bounded per profile. If a live candidate has no normals or a different
native layout, report that exact gate; do not manufacture reflection normals.

For each source-eligible car: same rear-camera OFF -> held-brake -> released
captures, confirm reflective OFF patch, independent bright ON and soft additive
glow, then windowReset/MSAA4x. A changed damaged source must stay Stock unless
the existing independently proven damage contract explicitly covers it.

Bruno requires a specific original UV revision/material comparison or a private
PS2 conditional replacement. Jump/Mattserati require a separate documented
source-revision contract or private conditional PS2 mesh, not relaxed hashes.
UFO requires its generic authored material behavior, not assumed mixed Mode4.
These bounded exclusions do not block the18 additional exact families.
