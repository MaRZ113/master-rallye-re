# Course cases and bounded PC comparison

All cases use canonical named RaceTest resources through PackFS. Their full decoded hashes, source offsets, parameter duplicates and compact ordered-point identities are in `bird-course-inventory.json`. Spatial source bounds describe authored points, not observed flying regions or populations.

| Case | Why selected | Flight / milling source points | Fly min/max | Milling min/max |
|---|---|---|---|---|
| FRANCE1 | Ordinary positive local-pointer case | 10 /6 | 200 /800 | 200 /850 |
| SPAINW | Fewest FlightList entries, both lists present | 3 /3 | 100 /900 | 200 /800 |
| TURKEY3 | Missing-local-MillList control | 12 /missing | 100 /900 | 200 /800 |
| ITALYS4 | Cross-course sanity, largest milling list | 6 /12 | 100 /900 | 100 /1000 |

FRANCE1's ordinary configuration has RndFly/RndMil10 and BrownTrue/True. Its FlightList is selected by name and consists of origins: no polyline is constructed by the original FlyBird. A burst can enqueue multiple entities at one chosen origin while per-entity six-draw initialization creates differing directions and speeds. Local ignored point map: `data/ambient2/FRANCE1-flight-origins.svg`.

SPAINW makes bounded selection especially clear: random positive0..2 index offset is clamped at the end of the three-record list. This changes which origin can be selected; it does not loop a path. The same generic owner/flight/sprite contract applies. Its point map is likewise unconnected.

TURKEY3 proves the source distinction between absent and empty MillList. Update's both-pointer gate is a concrete executable condition, while this XML supplies only FlightList. `1fdba8` returns the stored registry pointer or NULL, without creating a fallback list. Whether live course loading registers/retains another MillList must be sampled. **No claim of twelve live birds or universally disabled Turkey3 birds is made.**

ITALYS4 checks a different country/list proportion and distance settings under the same typed parser. All36 courses are re-extracted, including duplicate properties and exact list spellings. Runtime population and visibility for every case remain UNKNOWN; shared code ownership is not a captured race.

## PC corpus scope

Read-only root: `D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked`. Bounded inventory searched7595 filenames and122 XML files for bird/animal/controller/resource leads. No `gaAnimals_BirdManager`, FlyBird or Miller owner was found in that XML scan. Thirty-five XMLs contain bird **sound** references. A filename hit `DataGx/Vehicles/LandCruiser/citybird128-tga.dxt` is a vehicle texture path; no ownership connection to this sprite system is established. Its exact source hash is recorded in `pc-evidence.json`.

Classification: **NOT_FOUND_IN_SCANNED_PC_CORPUS** for a corresponding explicit BirdManager/bank candidate, not universal PC bird absence. This phase does not reverse the PC executable's animal code or classify every compiled DX polygon as bird-shaped. PC sound names, missing standalone Eggs and ambiguous filename fragments are not counts of visual birds.

The separate Course SDK remains unchanged at4244fa0c4d878523c9947f54816bf377cdfb2589. Existing route/visual geometry work is read-only context; this sprite mechanism does not require a new general PSM decoder or a course-geometry port during AMBIENT2.

## Future portability readiness

| Interface | Readiness | Needed later |
|---|---|---|
| AUTHORED_DATA_READY | READY | Exact points/properties available through PackFS; retained-registry issue separate |
| SPAWN_CONTRACT_READY | PARTIAL | Main flight algorithm ready; effective pool/global registry and ground population need capture |
| MOTION_CONTRACT_READY | READY | Original equations/order and explicit RNG state; scheduler/global call history required for a faithful race |
| ANIMATION_READY | READY | Separate key0..2 switcher; live frequency unknown |
| VISUAL_ASSET_READY | READY | Proven PSB quads/two atlases, future conversion needed |
| RENDER_CONTRACT_READY | PARTIAL | Concrete sprite/GS/VIF chain; live inherited GS and VU/frame unknown |
| PC_ASSET_CORRESPONDENCE_READY | UNKNOWN | No positive counterpart in bounded PC scan |
| RUNTIME_VALIDATION_READY | NOT_READY | No identified PS2 bird/texture/packet frame captured |

Future work categories: **TEXTURE_CONVERSION, NEW_VISUAL_MODEL, ANIMATION_SUPPORT, SCENE_OBJECT_CONTROLLER, PATH_OR_FLIGHT_RUNTIME, SPAWN_MANAGER, COURSE_METADATA_EXTENSION, CAMERA_CULLING_SUPPORT**. Here NEW_VISUAL_MODEL means a sprite quad/bank representation; PATH_OR_FLIGHT_RUNTIME means the recovered procedural flight, not an invented spline. **D3D8_RENDER_FEATURE** may supply ordinary billboard/blend submission, but draw wrapping alone cannot own spawning, RNG or course metadata. **REQUIRES_DEEPER_PS2_RE** applies to the exact live registry/cadence and Miller producer. Collision research is not a proved prerequisite for the main visual FlyBird path. No PC controller, asset conversion, renderer feature or course edit is implemented.
