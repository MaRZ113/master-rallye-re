# Course dressing and dormant PC content

Q5: the survey proves additional separately authored PS2 prop/controller
records. It does **not** prove a larger total tree population or that every
PS2 prop family is visually absent from PC. Q8: PC contains relevant dormant
standalone and embedded course content; activation, motion and rendering are
separate questions.

## Comparable scene metric

The table counts authored RaceTest Eggs with `Use en2d=False`,
`en3d Visible=True`, and a nonempty, non-`Null` model beginning `misc\`,
excluding `misc\sky\`. One Egg is one reference, including duplicate names or
transforms. This excludes cars, landscape aggregates, HUD, sound/editor
helpers and manager-only Eggs. `Visible=True` is an authored property and
does not establish successful rendering at runtime. A controller-driven
object with an identity Row3 still counts once; its path markers do not count
as additional objects.

All pair identities and route comparisons are recorded separately in
`course-pairs.json`; this table is a compatible XML-level comparison.

| Course pair | PS2 declared prop references | PC declared prop references | What the difference establishes |
|---|---:|---:|---|
| ItalyS1 | 14 haybales + 12 checkpoint companions | 12 checkpoint companions | 14 separate haybale Eggs with `gaAiRigidBody`; one exact duplicate transform is retained as a second authored record |
| France1 | 12 checkpoint companions + 2 dinghies | 12 checkpoint companions | Two separate `gaEntitySpline` boat entities, beyond PC's course aggregate |
| FranceS1 | 12 checkpoint companions | 12 checkpoint companions | No extra prop reference in this metric; other scene owners/materials can still differ |
| Turkey1 | 12 checkpoint companions + 7 tumbleweeds | 12 checkpoint companions | Seven separate rigid-body candidates, not a population count derived from texture names |
| TurkeyW | 12 checkpoint companions + 1 barge | 12 checkpoint companions | One spline-owned barge tied to an authored marker list |
| SpainWFlip | 11 checkpoint companions + 1 Nessie reference + 2 dinghies | 12 checkpoint companions | One checkpoint reference is replaced by an empty-model candidate; two boat entities are additional references |

PS2 uses `misc\objects\checkpoints\checkpoint`; PC uses
`misc\checkpoints\checkpoint`. Those resource paths are not equated merely
because their basenames match. The checkpoint survey separates these visual
companions from triggers and runtime construction. All 431 selected PS2
checkpoint-model references author Visible=True; the Nessie slot has that
flag too, although its tiny payload does not establish a renderable object.

Across all 36 PS2 principal RaceTest scenes, the concrete non-checkpoint
families represented above are 58 haybale references, 25 tumbleweed
references, 18 dinghies, two barges and four airships. The rigid-body owner is
authored on 83 Eggs in nine courses; the spline owner is authored on 24 Eggs
in 17 courses. Counts describe authored entities, not unique positions,
spawned runtime population, collision contacts or successful draws.

## Trees and bulk geometry

There are no separately authored tree model Eggs in the scanned principal
RaceTest XML on either platform. **Total tree/plant instances: UNKNOWN.**
This is a representation limit, not evidence that either platform lacks trees.

PC's Course SDK parses complete revision-135 render draws and TXT hierarchy,
but its Retail corpus has no paired GXM. TXT `moMesh` records retain names,
parentage and triangle spans; they do not supply an independently validated
one-object/one-instance map. A tree can have separate trunk, crown, billboard,
LOD and collision meshes, while a grouped mesh can cover many plants. PS2
PSM geometry, grouping and LOD ownership remain outside this survey's parser
coverage. Comparing TXT mesh-name totals against PSM string occurrences or
archive filenames would therefore be invalid.

For example, PC France1 TXT has 883 `moMesh` names containing `tree` and 114
containing `bush`; ItalyS1 has 290 tree-name matches, 71 pine-name matches and
four `COLLIDE_` tree-name matches. These are **source mesh-name records**, not
883 trees or a physical-tree count. The measured XML prop differences above
remain valid without converting those mesh records into object populations.

## PC counterparts already present in course content

The PC inventory covers 7,595 files, 99 `DataScene` XML files, 41 RaceTest XML
files, 36 principal course TXT sidecars and their associated course DX files.
The protected root is `corpora/retail/Data.sma_unpacked`. Absence statements
apply only to that scanned corpus; other PC builds and compiled executable
construction paths are not implicitly covered.

| Family | Actual PC evidence | Consequence for presence and portability |
|---|---|---|
| Haybales | `DataGx/Misc/Haybale/haybaletest.dx` and TXT exist; no standalone reference appears in the 99 scanned scene XML files. TXT has `HayBale` Size 28 and `$chull(haybaletest)` Size 28. Italian course TXT sidecars also contain numerous haybale mesh/material records. | Dormant standalone asset candidate **and** embedded course family. `gaAiRigidBody` use differs; static collision names alone do not prove movable physics. |
| Dinghies | France1, FranceS2, FranceW and FranceWFlip each have 11 literal hull meshes and 11 mast meshes in course TXT, with associated dinghy material/texture use. No standalone spline-owned dinghy Egg is found in the PC XML inventory. | PC has embedded boat content. PS2's moving-object ownership is the meaningful delta; a blanket PC-absent boat claim would be false. |
| Water/puddles | `$shader(water)`, `$shader(puddle)`, `$shader(waterfall)` and `$surfacetype(water)` occur in PC course materials. Decoded France1 and ItalyS1 DX draws carry matching material candidates and finite geometry bounds. | Existing PC course geometry is a potential carrier for renderer changes. Extra PS2 placement must be proved per course. |
| Checkpoints/banner | PC standalone checkpoint and banner DX assets exist; checkpoint companions are authored on all 36 principal courses. | Present on both, with different paths and usage; the knockable-barrel claim remains user runtime observation until independently tested. |
| Bird ambience | PC `Birds`/`Birds2` Eggs use `enAiSoundSource` and `Environment\birdsb`; no `gaAnimals_BirdManager` occurs in the scanned PC XML. | Sound ambience is already present. It is not equivalent to PS2 visual bird ownership. |
| Airship, barge, tumbleweed | No matching standalone model family or corresponding spline/rigid-body ownership found in the scanned PC file/XML inventory. | `NOT_FOUND_IN_SCANNED_PC_CORPUS`, not a universal PS2-only conclusion. |

ItalyS1 PC TXT contains 158 non-`COLLIDE_` haybale-named mesh records and 16
`COLLIDE_` haybale records, despite zero standalone haybale Eggs. Italy2 and
ItalyS4 each have 206 non-`COLLIDE_` haybale mesh records and 16 collision-named
ones. These are particularly clear counterexamples to equating an XML
instance count of zero with absence of a visual family. The meshes' exact
runtime collision ownership and correspondence to PS2 prop positions remain
unresolved.

## Rejected creature discovery

SpainWFlip's `SplitTime1-3` has the model `misc\nessie\nessie`, a concrete
Row3 `(1438.25, 32.37, 156.03)`, `Visible=True`, and no substantive AI owner.
However, `NESSIE.PSM` is only 44 decoded bytes and is byte-identical to
`ANIMALS\HAWK.PSM`:
`339d5610a6a170f45fafc316d2ca7ae23bd9060ed8180f892efa8ea003d621ac`.
Its empty/NaN header candidate provides no visible creature geometry proof.
Classify it as `SCENE_PLACEMENT` metadata with unresolved payload semantics,
not a discovered monster or an extra physical object.

## Evidence and follow-up boundary

XML properties, resource identity, hashes, TXT records and decoded PC draw
data are `CONFIRMED_BY_BYTES`. A runtime-generated or moving interpretation
of the authored owners is a `STATIC_INFERENCE` until a bounded executable
trace or runtime capture closes it. The survey creates no assets, scene
edits, Course SDK extension, physics hook or Blender change.

The strongest dressing follow-up is to close `gaEntitySpline` ownership and
marker-list consumption for boats, barges and airships. A later
`PS2-DRESSING1` should decode comparable landscape grouping/LOD/instance
ownership before making tree-population claims. `PS2-CHECKPOINT1` and
rigid-body work should retain their separate trigger, visual and physics
boundaries.
