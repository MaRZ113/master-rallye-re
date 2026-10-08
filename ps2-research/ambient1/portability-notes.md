# Future PC portability, without implementation

Read-only SDK reference: `D:\Game\Master Rallye\master-rallye-re-course`,
HEAD `4244fa0c4d878523c9947f54816bf377cdfb2589`.
`docs/course-sdk.md` already exposes a loss-preserving `CourseXmlDocument` and
typed `CourseProject`; `docs/course-race-logic-authoring.md` bounds the existing
writer to race logic/allowlisted marker positions. Neither presently promises
a dynamic-scenery importer, world-matrix runtime controller or general entity
writer. No reference code, asset, Blender UI or renderer was changed.

The smallest future read representation could preserve: exact source course
and hash; Egg/AI identity and model reference; original authored matrix; ordered
marker attributes/Type/Pos/Dir and raw lexical numbers; ordered typed properties
including duplicates; proved config semantics; observer binding; nominal
controller tick policy; evaluator/orientation version and fidelity label.
Unknown values stay raw. Route geometry/config are authored; time/trigger/
rest/banking and overwrite behavior depend on this executable reverse.

A future SDK semantic projection could provide read-only spline descriptors
and model/route provenance without broadening its writer. A separate PC runtime
integration would need stable object ownership, a proven model-instance/world
matrix hook, pause/destruction behavior, logical tick scheduling and an explicit
observer policy. Reusing native PC scene infrastructure is preferable to
presuming a new renderer, but no PC hook address or compatibility has been
proved in this phase. Retaining PS2 timing quirks vs deliberate improvements
would be an explicit later product decision.

| Selected case | Planning classification | Proof boundary |
|---|---|---|
| ITALY3 barge | NEW_DYNAMIC_OBJECT | Hypothesis: no matched standalone PC barge family; unnamed baked equivalent/placement UNKNOWN |
| TURKEYW barge | NEW_DYNAMIC_OBJECT | Same corpus-limited hypothesis; no one-to-one placement match |
| FRANCE1 boat1 | REPLACE_OR_HIDE_BAKED_STATIC_OBJECT | Hypothesis requiring per-placement proof: PC course has embedded dinghy meshes/materials; no matched boat1 instance yet |
| FRANCEM airship | NEW_DYNAMIC_OBJECT | No matched PC airship family in surveyed corpus; exact resource/runtime route not ported |
| SPAINS2 boat1 | NEW_DYNAMIC_OBJECT | No mapped baked counterpart in this comparison; placement equivalence UNKNOWN |
| SPAINS2 boat5 | NEW_DYNAMIC_OBJECT | Independent second object; no matched PC scene object to reuse |

These are `STATIC_INFERENCE` planning choices; exact equivalence is `UNKNOWN`.
No case qualifies as proved REUSE_EXISTING_SCENE_OBJECT. CDELTA1's PC France1,
FranceS2, FranceW and FranceWFlip each have 11 hull +11 mast **mesh-name records**,
not 22 visible boats. Simply spawning PS2 boats risks duplicating scenery;
matching grouped draws, coordinates, visibility and collision must precede
any hide/replace strategy. No static object was hidden or removed here.

Shared owner code supports boats, barges and airships without family branches.
It does not prove other ambient controllers share its movement. BirdManager,
rigid bodies and vegetation remain existing bounded leads, not new reverse
work or an automatic AMBIENT2 recommendation.
