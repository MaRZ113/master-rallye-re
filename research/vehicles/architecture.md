# Vehicle identity channels

Vehicle identity is not one shared name lookup. The retail path has separate
physical, class-local, frontend, and runtime identities:

| Channel | Owner / representation | ID26 result |
|---|---|---|
| Physical registry record | `VehicleRecord[26]`, native absolute ID | Mercedes record, physical ID 26 |
| Class-local selection | T1 local index 7 through sparse mapping | resolves to physical ID 26 |
| Vehicle Select identity | `FUN_004819B0`, groups `0x33` and `0x34` | `MERCEDES` / `ML-320`; unavailable state is separate |
| Quick Race summary | `FUN_0047B040`, group `0x35` | combined `MERCEDES ML-320` |
| Race Options identity | `FUN_0047A540`, groups `0x33` / `0x34` | manufacturer and model remain separate |
| Vehicle Setup identity | `FUN_0044F8E0`, group `0x35` at `0x0044FA29` | ID26-only combined string; stock lookup for other IDs |
| Race Details identity | `Frontend/RaceDetails/CurrentVehicleString`; shared `FUN_0047C080`, group `0x35`, three bounded sites | Final candidate runtime-confirmed in single-player Master Rallye and Rallye Cup: `MERCEDES ML-320`; absolute `RaceData/CompetitorN/CarID` remains 26 |
| Runtime race identity | participant `CarID`, `CarClass`, `CarType`, `WheelType` | ID 26, T1, Mercedes / Mercedes |

## Vehicle audio identity

The engine-audio constructor selects an implicit stock profile from the
participant's absolute `Race/CarN/CarID`. The addon-facing semantic field is
therefore `stock_audio_profile_id`, separate from `physical_vehicle_id`.
R5V-G.2 runtime evidence proves that physical ID26 can use a different tuned
profile while Broker state, Mercedes model/physics configuration, class,
`CarType`, and `WheelType` remain Mercedes. The canonical Mercedes setting is
`stock_audio_profile_id = 0` (Landcruiser, historical-compatible `rev9`/A
profile); ID19 was the intentionally diagnostic bass-heavy A/B oracle.

Retail tuned profile IDs are 0..24. ID25 and ID26 have no ordinary tuned case
in pristine retail. The tool validates the stock profile row against the
hash-pinned [audio matrix](audio/stock-audio-matrix.json). Profile selection
does not rename or remap the physical vehicle. The sample family, scalar
fields, and curve-table pair remain one indivisible stock profile; they are
not independently configurable addon fields in this phase. Runtime evidence
and its limits are in [G.2 results](audio/runtime-results.md).

The renderer-facing localization selector is not the physical identity. The
R5V-F display hooks preserve ID26 and specialize only confirmed presentation
consumers. G.1 mirrors ID3 only as temporary input to the native availability
predicate and locked-reason selector. It does not alias the registry record,
class mapping, model, wheel, physics family, or runtime CarID. Race Details
reads absolute `RaceData/CompetitorN/CarID` through the traced accessor chain;
the final Broker captures and human visual checks confirm the bounded string
path in both qualified single-player modes. Stock ID0 regression and full
stage/results are owner-reported PASS; frontend return is not reported.

The group-6 locked message and group-0x35 vehicle-name paths are also separate.
The generic locked line remains retail text, while ID26's second locked line
reuses ID3's existing selector. Vehicle Setup uses the already-established
combined string rather than changing `gaLocal` globally.

## AI opponent vehicle identity

R5V-H confirms statically that the Quick Race AI chooser builds class pools
from absolute Vehicle IDs. Its stock T1 list is IDs 0–6; the player-facing
T1-local7 mapping to ID26 is not used there. A gated proof candidate changes
only the selected Car1 absolute ID after driver selection, allowing native
registry code to derive T1 `CarClass` from physical ID26. See
[R5V-H architecture](ai/architecture.md) and [pool map](ai/stock-ai-pools.md).

R5V-H is now **FULL PASS / CLOSED** for physical ID26: natural Quick Race,
new Rallye Cup, and new Master Rallye T1 eligibility are runtime-confirmed;
Cup stage reuse and Master Rallye native fresh-process save/load persistence
are also confirmed. Invitation's normal route is T3-only and uses ordinary
base IDs 14..20, so T1 ID26 is not applicable there. This establishes a future
addon-design requirement: ordinary/non-bonus T3 vehicles need explicit
Invitation pool qualification, while bonus/special T3 vehicles must not be
inserted automatically. This note is carried forward for R5V-I/J.

## R5V-I — multi-slot registry and independent-family qualification

R5V-I.0 is **FULL PASS / CLOSED** for the second sparse physical slot: 28
records, T2/local7 -> ID27, with the 39-row RaceTest table relocated from
base `0x580` to `0x5B4` (39 initializer and 11 indexed-consumer relocations).
Verified I.0 captures show physical ID27/T2 materializing as a player actor and
coexisting with physical ID26/T1 in SplitScreen. The I.0 Navara identity was
only a donor slot proof.

I.1 changes the same physical ID27 to an intentionally authored qualification
identity, `R5VQualifier`, without increasing the record count or changing the
T2 local mapping. The human-tested candidate materializes the player vehicle
through the separately named `R5VQualifier` family; a natural AI capture also
shows physical ID27/T2/AI with `CarType` and `WheelType` `R5VQualifier`. The AI
capture does not prove a completed AI lifecycle. Resources remain
Navara-derived, with a controlled magenta body texture, cloned physics and
player-modification rows, donor frontend art/stats, donor-derived collision,
and audio profile7. This is an authored qualification vehicle, not historical
content. Capture hashes and evidence limits are in
[I.1 runtime evidence](multislot/i1-runtime-evidence.json).

The architecture demonstrates formula-based registry layout through IDs26
and 27 and sparse placement in T1 and T2. The identity/presentation layer is
runtime-qualified only for those two additions; it does not prove arbitrary-N
runtime support. Vehicle Select re-entry still has an unresolved
scene-selection restoration divergence, and the captured ID27 race-marker
color remains white; the J0 example requests magenta independently of body
art. Both gates are documented before public runtime-release qualification.

## Generic addon SDK J0

The new manifest-driven SDK planning architecture is separate from the
existing donor-authoring SDK v1. It provides strict JSON validation, explicit
capability-profile ID allocation, sparse forward/reverse class maps,
formula-derived registry layout, AI/audio/unlock/Results and color planning,
optional external DX/DXT payload validation, deterministic multi-addon output,
and hash verification. It emits semantic frontend plans rather than native
XML or executable patches. The public unchanged-EXE runtime loader is not yet
implemented. See [SDK architecture](sdk/architecture.md).
