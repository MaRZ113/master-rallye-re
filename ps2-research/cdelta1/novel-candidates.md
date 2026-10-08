# Novel discoveries ranked by meaningful evidence

The exploratory pass covered every available PS2 DataScene XML, all 36 actual
landscape payloads, the complete PackFS name inventory, every retail PC
DataScene XML, 36 PC material/hierarchy reports and four decoded PC course
models. It searched owners, model references, unmatched resource families,
material interfaces and unusually large authored populations. No filename
count is treated as a visible population.

Five substantive new candidates survived. A top-ten list would pad it with
overlapping fleet members or unsupported names. Boats and barges are kept
together under their shared runtime ownership, with individual rows in the
delta matrix.

| Rank | New candidate | Concrete evidence | Significance / remaining boundary |
|---|---|---|---|
| 1 | Shared spline-controlled fleet | 24 gaEntitySpline Eggs on 17 courses: 18 dinghies, 2 barges, 4 airships; named nonempty path lists and controls | A reusable moving scenery layer, larger structurally than one airship. Runtime movement is UNKNOWN; PC has some embedded dinghy meshes. |
| 2 | Authored rigid-body haybale layer | 58 separately placed haybales on five courses, with gaAiRigidBody, mass/MOI/trigger settings | A gameplay-relevant dressing candidate beyond static scenery. PC already contains hay visuals/collision and a dormant test asset. Contacts/activation are UNKNOWN. |
| 3 | Distributed smoke-emitter ownership | 81 model-less aiSpawnParticle Eggs on 25 courses, smoke-family names and transforms | Broad authored effect layer absent from the compared PC scene ownership. Actual particle binding/rate/effect and any PC alternate path are UNKNOWN. |
| 4 | Turkey3 course-local water/puddle discrepancy | PS2 water/puddle string at decoded offset 3429472; PC sidecar and all 939 validated draws lack named water/puddle bindings | Potential extra surface or changed material classification. PS2 draw/geometry binding and unlabeled PC equivalents are UNKNOWN. |
| 5 | Treeblend foliage interface | 14 PS2 landscape payloads; France1 bush/bush01 corresponds to PC tree material but PS2 treeblend | Potential widely visible renderer difference; neither more bushes nor blend/wind behavior is proved. |

Tumbleweed was a requested lead, so its 25 rigid-owner placements are valuable
but not counted as a newly discovered family. Birds, airship, checkpoint barrels,
grass, water and reflections likewise remain in the required-leads matrix.
The fleet discovery goes beyond the known airship by proving common authored
ownership for boats and barges.

Lower-confidence shader spelling differences (`wire`, `wires`, `signtest`,
`shade(treeblend)`, singular `detail(shrub)`) are recorded for completeness.
PC wire textures/geometry already exist. No major new feature is assigned
solely from these labels. No new weather subsystem was established.

**Rejected large creature lead:** SPAINWFLIP references Nessie with Visible=True,
but NESSIE.PSM and HAWK.PSM are identical 44-byte stub candidates. There is no
renderable monster/hawk proof. One checkpoint-model slot therefore resolves
to that reference rather than a checkpoint model. This rejection is preserved
as a false-positive control, not erased from the inventory.

Screenshots did not reveal another major novel object. Their build/course/frame
identity is unresolved; they are correlation evidence only. The six members of
PS2.zip are byte-identical to the previously supplied userscreens.

The survey supports a larger **authored ownership layer** than the initially
noticed isolated props. It does not yet prove a larger PS2 runtime visual
population or successful dynamic physics. Best next reverse: PS2-AMBIENT1,
as narrowly defined in next.md.
