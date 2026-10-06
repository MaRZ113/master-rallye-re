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
| Race Details identity | `Frontend/RaceDetails/CurrentVehicleString`; retained static consumer map lists `FUN_0047C080`, group `0x35`, three sites | Broker captures show `GALOCAL UNKNOWN` for ID26 in Master Rallye and Rallye Cup; mode/source dataflow and fix are pending staged-scene validation |
| Runtime race identity | participant `CarID`, `CarClass`, `CarType`, `WheelType` | ID 26, T1, Mercedes / Mercedes |

The renderer-facing localization selector is not the physical identity. The
R5V-F display hooks preserve ID26 and specialize only confirmed presentation
consumers. G.1 mirrors ID3 only as temporary input to the native availability
predicate and locked-reason selector. It does not alias the registry record,
class mapping, model, wheel, physics family, or runtime CarID. The new Race
Details captures prove the correct physical ID reaches the screen, but do not
prove that its string writer reads `Race/Car0/CarID` directly.

The group-6 locked message and group-0x35 vehicle-name paths are also separate.
The generic locked line remains retail text, while ID26's second locked line
reuses ID3's existing selector. Vehicle Setup uses the already-established
combined string rather than changing `gaLocal` globally.
