# PS2-CDELTA1 checkpoint survey

**The authored checkpoint visual asset changes, while gameplay triggers remain
separate Eggs.** The 36 PS2 scenes contain 431 explicit checkpoint-model Eggs
using `misc\objects\checkpoints\checkpoint`; the 36 paired PC scenes contain
440 using `misc\checkpoints\checkpoint`. The 41-file PC RaceTest scan also
contains templates/tests; its 452 references are not the paired comparison.
Every counted checkpoint-model Egg authors `Use en2d=False`,
`en3d Visible=True` and `Hitable=True`, with **no non-Null AI owner**.
These counts describe authored scene references, not independent in-game
rendering or successful collisions.

## Q3: trigger, visual, collision, physics and banner are distinct layers

| Layer | PS2 evidence | PC evidence | Conclusion / limit |
|---|---|---|---|
| Gameplay split trigger | 108 `gaRaceSplitTimeAI` owners on 36 courses; Split Time ID, Radius, ExtraTime on separate Eggs | 110 owners on the paired 36, with additional authored duplicates in some files | Shared semantic timing/checkpoint layer; counts need per-course inspection |
| Checkpoint visual placement | 431 explicit model Eggs and matrices, generally four per split | 440 explicit model Eggs and matrices | `SCENE_PLACEMENT`, `DIFFERENTLY_USED`, `CONFIRMED_BY_BYTES` |
| Selected visual resource | `MISC\OBJECTS\CHECKPOINTS\CHECKPOINT.PSM`, 4,924 decoded bytes; drum/top metal names and c-point/aluminium/top references | `DataGx/Misc/Checkpoints/checkpoint.dx` exists | PS2 barrel-like material evidence versus PC legacy checkpoint asset; geometry shape/runtime color not independently verified |
| Legacy PS2 asset | `MISC\CHECKPOINTS\CHECKPOINT.PSM`, 7,465 bytes; planks/stamp/CHECKPOINT references | Shared legacy PC checkpoint family | Asset exists, but no RaceTest Egg selects this PS2 path |
| Collision | Hitable=True on both scene sets | Hitable=True and separate PC baked drum/hay collision nodes elsewhere | Flag is eligibility, not collision registration, response or dynamic physics |
| Dynamic physics | No explicit `gaAiRigidBody` owner on any of the 431 checkpoint model Eggs | No matching standalone checkpoint rigid owner | Runtime registration/implicit body creation and knockability UNKNOWN |
| Banner | `MISC\CHECKPOINTS\BANNER.PSM`, 4,315 bytes; MR Banner/masterlogo printable reference | `DataGx/Misc/Checkpoints/banner.dx` exists | Resource availability; no explicit RaceTest banner model Egg on either platform; automatic creation/rendering UNKNOWN |

### Exact authored example

In `\TNG\DATASCENE\RACETEST\ITALYS1.XML`, `SplitTimes / SplitTime0`
is a model-less Egg (`en3d Model Name=Null`) with `AI No=0 /
gaRaceSplitTimeAI`, Split Time ID=0, Radius=12 and ExtraTime=70.
Its visual sibling `SplitTimes / SplitTime0-0` has
`en3d Model Name=misc\objects\checkpoints\checkpoint`, a real matrix
(translation `-1756.07 35.35 -1020.47`) and no AI owner. Twelve such visual
checkpoint Eggs occur in this scene. The PC counterpart `ItalyS1.xml` also
has twelve checkpoint visual references, with the legacy model path.
This demonstrates **authored visual placement**, rather than assuming the
visible markers are generated from the timing trigger's radius.

SPAINWFLIP has eleven checkpoint references because `SplitTime1-3` instead
selects the 44-byte Nessie stub. Its twelve authored visual slots do not mean
twelve renderable checkpoint meshes. Paired PC SpainWFlip has twelve legacy
checkpoint model references. Additional PC duplicate/helper rows explain why
the global count cannot safely be reduced to `36 * 12`.

### Resource byte evidence

The active PS2 resource's printable material strings include
`drum $shader(metal)` at decoded offset 2109 and `top $shader(metal)` at 2254.
Texture-name evidence includes `commontextures\c-point-tga` at 2038,
`commontextures\aluminium-tga` at 2074/2219 and
`commontextures\top-tga` at 2187. These are bounded byte observations; this
survey does not promote string carving to a complete PSM mesh/collision parser.
The alternative legacy resource uses planks/stamp references instead, so the
two PS2 filenames resolve to materially different payloads.

PC has drum/barrel texture families inside compiled course directories and
haybale render/collision geometry; these are not proof that the same checkpoint
barrel model exists or that checkpoint barrels are dynamically activated.
`Misc/Haybale/haybaletest.txt` contains `$chull(haybaletest)`, which establishes
authored collision geometry for that separate prop, not checkpoint physics.
The corpus inventory and scan bounds are retained in the main survey.

### User runtime observation and unresolved owner

The user reports yellow PS2 checkpoint barrels that can be knocked down,
versus PC noncolliding checkpoint markers. This remains explicitly
**USER_RUNTIME_OBSERVATION**. No independent PS2 or PC gameplay run was made
for this survey, and screenshots do not prove collision or physics response.
Serialized `Hitable=True` on PC as well as PS2 shows why a boolean cannot be
substituted for observed behavior.

`gaAiRigidBody` is independently authored on 58 haybales and 25 tumbleweeds,
but not on the checkpoint visual Eggs. Therefore the causal checkpoint owner
is still UNKNOWN: possible automatic model/scene registration, collision-kind
interpretation or runtime-generated body behavior needs bounded ELF work and
then a runtime check. Banner creation is another separate open question.

Recommended deferred deep phase: **PS2-CHECKPOINT1** should trace the selected
objects/checkpoints model load through collision registration/body creation,
compare the PC legacy visual's corresponding path, and keep timing triggers
and banner drawing independent. That is a research backlog item; no gameplay
patch, physics port or proxy feature is implemented by CDELTA1.
