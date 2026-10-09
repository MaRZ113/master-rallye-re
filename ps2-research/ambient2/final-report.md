# PS2-AMBIENT2 final report

| Summary field | Result |
|---|---|
| Phase | PS2-AMBIENT2 — BirdManager, flight and visual presentation |
| Repository | D:/Game/Master Rallye/master-rallye-re-general |
| Branch | master |
| Starting HEAD | 9ace2be4384f2a052482016e5a4873758934b7b5 |
| Ending HEAD | Phase closeout commit; exact hash in post-commit handoff MANIFEST/receipt |
| Preflight | Clean, ahead14; parallel Observatory changes appeared during closeout and were preserved/excluded |
| Canonical ELF | SLES_509.06,3739852 bytes,b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2 |
| PackFS | Four canonical inputs freshly verified; existing extractor reused |
| BirdManager class | gaAnimals_BirdManager, string472b78,vtable473c10 |
| Constructor | 1ae8b8,0xb0; factory call15d2a4; clone1cec68 |
| Initialization | 1af1c0,list resolution/optionalMaxBirds/pool/initial first-free keys0..3 |
| Update | 1af330; both pointers gate and ordered spawn/retire/takeoff/copy |
| Render | en2d world sprite:21ea20→3301c8→3302b8→337a98/3376c0 |
| Destruction | 1aec50 releases manager vectors; pooled entity deletion not in this body |
| Bird source representation | Typed RaceTest AI properties and ordered MarkerLists |
| Course coverage | 36/36 paired canonical courses |
| Total authored points | 542 flight origins +55 milling-origin candidates; not populations |
| Point semantics | Nearest-index/random-offset spawn origins; no connected flight route |
| Manager runtime layout | Five pointer vectors,+a8/ac marker lists,+34 capacity,+74 observer; JSON field table |
| Per-bird state layout | Entity0x7c,en3d0x80,en2d0x90,FlyBird0x30,switcher0x20 |
| Allocation capacity | Constructor16; effective Animals/MaxBirds UNKNOWN |
| Spawn policy | Clock/probability,count0..RndFly-1,strictXZ annulus,shared origin,pending conversion one per call |
| Active count semantics | Ground/flying/pending/free vector sizes; selected live counts UNKNOWN |
| Culling | Fly retirement>MaxFlyXZ; generic sprite checks/VU clipping; no live visible count |
| Random source | Global4262a8; Schrage48271/2147483647,low24/2^24 output |
| Timing source | Fixed /30 per controller invocation; actual cadence/pause UNKNOWN |
| Motion algorithm | Rise+speed accumulation; P=origin+currentDirection*totalTravel |
| Route/point behavior | Cached local origin search, no path interpolation/loop/target-arrival controller |
| Orientation | Fly writes translation; renderer Y-locked camera billboard,scale0.1 |
| Group/flock behavior | Independent controllers sharing a burst origin; no neighbor steering in traced path |
| Animation | Separate ImageBankSwitcher,keys0..2,advance every five invocations;groundkey3 |
| Visual model/sprite | BurdyBrown/White PSB,one selected quad per flight frame |
| Texture resources | Brown/White_000.GXI64×64,binary stored alpha; hashes in inventory |
| Material | Generic world PSB mode8; no bird-specific PSM/treeblend shader |
| GS state | ABE1,ATE0,source-alpha blend,TCC1/TFX0,ZMSK1,ZTST2; inherited fields explicit |
| VU/packet producer | 3201b0→31d7c8 MSCAL0xf,selector0;317120/31e010→VIF1 |
| Live VU residency | UNKNOWN; embedded upload/input/output contract proved statically |
| Representative cases | FRANCE1,SPAINW,TURKEY3;ITALYS4 sanity |
| Cross-course validation | Counts/references/properties re-extracted across36 courses |
| PC counterparts | No explicit controller/Burdy counterpart in bounded7595-name/122-XML scan; sounds separate |
| Portability readiness | Main motion/assets/animation ready; live population/registry/cadence/render inheritance partial |
| Offline diagnostic | bird_runtime.py,compact JSON,synthetic trace,ignored point/trajectory SVGs |
| Runtime capture | NOT_PERFORMED |
| Unittest | 308/308,0 failure/error/skip; final focused38/38 |
| Pytest | 308 tests,290 subtests PASS; isolated268 PASS/40 external-input skips |
| Compileall | PASS |
| Diff-check | PASS at closeout |
| Reproducibility | Five CLI outputs byte-identical; independent instruction/RNG/source checks |
| Original inputs unchanged | Canonical hashes and bounded PC source/reference checks; no original writers |
| Course SDK unchanged | Clean4244fa0c4d878523c9947f54816bf377cdfb2589; read-only |
| PC renderer unchanged | Empty renderer/proxy diff; no port |
| Commit | Local research: reverse PS2 BirdManager flight and rendering; exact hash in final receipt |
| Push | Not performed |
| Overall status | **PS2-AMBIENT2 STATUS: COMPLETE** at principal static/executable flying-bird level |

## A. Major discoveries

The actual implementation is simpler than a flocking/path system: procedural independent flying sprites, authored spawn origins and a separate three-image animation owner. Its reconstruction reaches actual world-translation stores and a concrete resource/packet draw path. This supplies a reproducible candidate for later Content Pack work without implementing it now.

Two important source/executable discrepancies are preserved. Manager update requires both resolved list pointers, but26 course XMLs contain no local MillList. Config calls the Boolean property writer for Bird Brown, retaining a fresh brown default despite authored False. Neither is replaced with a plausible corrected implementation. No selected live run is claimed to exhibit either consequence.

## B. What the542 points mean

They are ordered FlightList candidate origins across36 courses. The manager selects a nearest horizontal base, later limits search to a cached local interval, adds a random0..2 index offset and clamps. A burst copies one selected XYZ into multiple pooled entities. Subsequent movement does not traverse the list. List order affects selection, not connectivity. Another55 MillList points support separate milling-origin selection code with normal population activation unresolved. No point total is a live bird count.

## C. Ownership and spawning

Factory→fresh0xb0 manager→typed list/config→pool of registered entities is proved. Original flight-burst probability, count, free-pool limit, annulus, pending queue and one-at-a-time activation are specified. Fly retirement returns entities to the pool. Capacity16 is a default, not captured maximum. Initial first-free visual commands contain allfour keys; any preload purpose/visible initialization artifact is unobserved. Registered entity cleanup outside the manager destructor, race resets and external/retained list registry remain unknown.

## D. Flight algorithm and actual transform

Global RNG has exact recovered integer state and low24 float output. Initialization draws six values and creates a normalized mostly-away/lateral/up direction. Update conditionally increases D.y, always increases speed, accumulates travel using updated speed, then calculates origin+D*travel. It writes entity+50 carrier translation; manager`1b0508` transfers that XYZ to entity+4c visual. Parameter24 is passed but unused by the position helper. `/30` is literal per invocation, not proof of wall-clock30Hz. Mathematical detail, float32 operation order and independent instruction probes are in [flight-motion.md](flight-motion.md).

## E. Group behavior

Shared spawn origins and independent RNG draws can create grouped flight; no neighbor steering, leader, waypoint spline or collective trajectory is found in the traced controller. This negative scope is executable-backed; observed flock shape/count is not asserted. Ground Miller exists with plane walking/random timers, but its normal population producer is an explicit missing link.

## F. Orientation and animation

Fly supplies translation without yaw/pitch/bank. The renderer uses a Y-locked basis from camera matrix row2 X/Z and preserved0.1 scale; no invented normalization or velocity-facing orientation. ImageBankSwitcher in slot1 cycles0/1/2 every five invocations, independent of slot0 motion. Groundkey3 is separate. Original bank frame representation is two source triangles per image, converted into a four-vertex textured quad.

## G. Bird rendering and causal chains

```text
AUTHORED: exact manager/list properties --1af0b0/1ff7a8--> runtime names/80-byte records
         --1fdba8--> list pointer --1b06d8/1afa20--> selected spawn origin
         UNKNOWN LINK for courses lacking local MillList: actual external/retained registry

MOTION: pooled entity --1affe0/1b0138--> FlyBird
        --1b0a40/1b0e68/1b0f88--> carrier translation --1b0508--> en2d translation

ANIMATION: fly flag --1b0410--> slot1 ImageBankSwitcher
           --1b17e8/1b1838--> bank key0/1/2 --337a98--> selected original Burdy frame

ORIENTATION: camera --3387c8--> renderer+220 --330530--> Y-locked basis
             + carrier-derived en2d translation --337a98--> world sprite transform

RESOURCE: manager bank --2062a8/305038/380a08--> PSB records
          --387478/2fd7d0--> GXI texture handle --3376c0/311c50--> bound primary draw

RENDER: selected quad --337a98/362138/3201b0--> packet cache
        + mode8 GS/texture --3376c0/317120/31e010--> DMA CALL
        --316ce0/316b88/30ea80--> VIF1 submission
        --confirmed upload and matching embedded selector0 contract--> GIF/XGKICK
        UNKNOWN LINK: selected live VU residency/inherited state/visible frame
```

All code arrows are CONFIRMED_BY_EXE; original selected resources/configuration add CONFIRMED_BY_BOTH. The final embedded-program relationship is statically established; no arrow is promoted to CONFIRMED_BY_RUNTIME. Source-alpha blending, disabled alpha test and masked depth writes are decoded independently from texture alpha. Exact inherited bits remain unknown. [draw-pipeline.md](draw-pipeline.md) gives the complete bounded contract.

## H. Course and PC evidence

France1 provides ordinary positive lists; SpainW has the fewest flight points; Turkey3 is the missing-local-list control; ItalyS4 tests another distribution/configuration. All36 source inventories are checked, with duplicates/source order intact. Bounded PC search found bird sound references and an unrelated-by-ownership vehicle texture name, but no explicit BirdManager/bank counterpart. Compiled geometry/executable-wide PC absence is not claimed.

## I. Future portability

Future work would combine converted sprite banks/atlases, authored origin/configuration input, a spawn manager, the recovered motion/RNG/animation and ordinary billboard/blend rendering. Existing final D3D8 draws do not by themselves expose that ownership or state. Main algorithm/assets are usable for later design; faithful course population and visual parity need captured registry/RNG/cadence and final draw state. No PC assets, controllers, renderer, courses or SDK files changed.

## J. Exact unknowns

Effective Animals/MaxBirds; MarkerList registry contents/retention on26 missing-local-list courses; first/last registry entry identity; global RNG state/call history at spawn; scheduler/pause/replay; normal ground/Miller population producer; initial first-free four-key visual effect; global pooled-entity destruction/reset; missing-resource selected bird behavior; final inherited GS/texture descriptor and actual live VU/frame. The manual capture plan targets these fields/functions directly. Synthetic previews are not runtime PASS.

## K. One next phase

Recommend **PS2-RIGID1**, narrowly recovering authored tumbleweed/haybale ownership and rigid update→world-transform behavior. It adds a distinct course-content mechanism while preserving the current breadth-first research priority. No subsequent phase begins here.
