# Track port handoff (2026-10-19)

State of the PS2 to PC course port after the Turkey3 first-course work. Everything below is in `master-rallye-re-general`, branch `master`, 34 local commits ahead of `origin/master` (nothing pushed). Evidence grades: RUNTIME = the project owner saw it in the running game, STATIC = derived from files or code only, SYNTHETIC = checked by tests on built data.

## 1. Goal and rules
Port PS2 course content (geometry, textures, materials, physics objects, collision, triggers, logic) to the PC game as a delta port: the PC course stays the base, PS2 differences are carried over. Channels: A render overlay (D3D8 proxy), B loose data files, C native hooks. Policy and registry schema: `../track-port0/policy.md`, `registry-schema.json`. First course: Turkey3 (PCSX2 verification mandatory, done by hand for the wall probes).
Test install used for all runs: `D:\Game\Master Rallye Pristine`. PS2 sources: `D:\Game\Master Rallye PS2`. Retail PC corpus: `D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked`.

## 2. What the owner confirmed in the running game
| Item | Result |
|---|---|
| Probe teleport (Ctrl+Alt+1..9, `[ProbeTeleport]`) | works after writing the pose inside the controller hook (the reset manager clears the flag almost every tick) |
| Loose files next to the exe (`DataScene`, `DataGx`) | read by the game, no repack of `Data.sma` needed |
| PS2 wall at probe 1 (PS2 stops the car, PC resets with OFF COURSE) | confirmed; probes 2 and 3 not conclusive (heading not recorded) |
| Plain Egg + DX model without AI | loads and draws |
| `gaAiHayBale` Egg | crashes on the first physics step (see 4.4) |
| House and caravans as loose models + tag100 brushes | drawn at the right place, solid, PS2 lighting, textures right way up after the V flip, caravans stand correctly after the terrain transfer |
| Terrain transfer, second build | no holes any more; texture quality differs (64x64 vs 128x128, fixed afterwards but not re-run); collision still wrong in some changed places (no coordinates given yet) |
| Limits probe (PS2 outer limit lists on PC) | candidate built; the owner confirmed only that loose XML is read; the OFF COURSE effect was not reported |

## 3. Documents (this folder)
`T2-BSP-FORMAT.md` PS2 `.BSP` grammar and leaf classes; `T2-QUERIES.md`; `T2-SOLID-SHELL.md` solid exterior on 36 courses and the probe results; `T2-BEHAVIOR.md` wall vs OFF COURSE comparison, limit lists; `SCENE-CENSUS.md` triggers and controllers on 36 courses; `PROBE-TELEPORT.md`; `LIMITS-PORT-PROBE.md`; `HAY-PROBE.md` (crash analysis); `T4-HOUSE1.md`, `T4-OBJECTS.md`, `T4-TERRAIN.md` (object and terrain conversion with every run result); `README.md` T1 census; `../TRACK_RESEARCH_INDEX.md`; `turkey3-registry.json` (21 elements, valid).

## 4. Technical findings worth knowing
1. PS2 `.BSP` and PC `tag100` are the same BSP family. Grammar: one record per node, `field_0, field_1, has_plane [nx ny nz d code], has_list, has_child [selector, back subtree], has_sibling [selector, front subtree]`; plane nodes have both links (child = back = `n.p+d < 0`, sibling = front), leaves have none; leaf `field_0` = `0xFFFFFFFF` solid, `1` empty; selector 1 = terminal leaf, 0 = plane node; header words w0 = back leaves, w1 = front leaves, w2 = w3 = plane nodes. The PC tag100 suffix also carries 1.9 MB of data after the tree (carried over unchanged, meaning unknown). `tag100_tree.py` round-trips retail Turkey3 byte-exactly.
2. Contact generation (`0x006363C0`, plane query `0x00636770`/`0x006369b0`) returns no contact when the hit plane code is negative as int32. Retail splitter planes have code `0xFFFFFFFF`; every collidable brush plane needs a valid non-negative code (we copy the ground plane code under the object). Plane normal convention: from the solid side to the empty side.
3. `gaAiHayBale` (dormant retail class): initializer `0x004C9CF0` renames the Egg, selects `Misc/Haybale/haybaletest`, creates the body (`0x0043E2A0`, mass 350). The crash (`MRallye.exe+0x10EC56`, write through a NULL pooled contact record inside contact generation) happens on the first physics step in the stock contact code, with or without a model in the Egg. A physical prop needs the real contact/pool contract (`0x006363C0`, `0x004FFDE0`, pool at `0x006F986C`) understood first.
4. PS2 vertex word at +16 = bytes (A, c1, c2, c3); the PC course DX colour for the same vertex is (c1, c2, c3, 255) (48,406 shared vertices, equal within 1): the PS2 tint is copied as is. GXI rows are top-down, PC DXT bottom-up: V is flipped (`1 - v`). PC course textures are 128x128, PS2 ones 64x64; same-name PC textures are used when they show the same image.
5. Ground delta of Turkey3 (triangle level): PS2 4,020 and PC 3,512 non-exact ground triangles (about 15 percent of the ground); 3,424 PS2 ones share the XZ footprint of a PC triangle, 2,694 of them with identical heights (texture/UV/colour only). 177 clusters. Height-field view: 4.1 percent of cells differ, 141 regions.
6. Limit lists: PS2 `LeftOuterLimit2` / `RightOuterLimit2` sit farther from the RaceLine than the PC outer lists (median 88 vs 61 left, 59 vs 48 right); PC `gaLimitsAI` tests the inner then the outer polygon and needs 8 samples outside for state 2.
7. PS2-only controllers on 36 courses: 36 bird managers, 24 spline objects, 81 emitters, rigid bodies on 9 courses; PC has none. PS2 has 3 splits everywhere; PC has a 4th `Copy of` split on Turkey3 and TurkeyS2Flip.

## 5. Tools (all under this folder unless noted)
- Build everything for Turkey3: `python ps2_course_objects.py --pc-root <retail unpacked> --out <dir> --terrain` (objects: house1, caravan, redcaravan; `--terrain` adds the ground delta). Output tree: `DataGx\Misc\PS2Port\...`, `DataScene\RaceTest\Turkey3.xml`, `DataGx\Course\Turkey3\turkey3.dx`, `report.json`.
- `ps2_obj_to_dx.py` single-mesh converter (T4a); `ps2_terrain.py` ground transfer; `tag100_tree.py` / `tag100_patch.py` BSP editing; `tag100_tree.py` tests: `python -m unittest test_tag100_tree test_tag100_patch`.
- Measurements: `ground_clusters.py`, `ground_delta_probe.py`, `ground_delta_regions.py`, `terrain_verify.py`, `mesh_pc_presence.py`, `limits_compare.py`, `gcoll_*.py`, `bsp_*.py`, `scene_census.py`.
- Probes: `limits_port.py` + `limits_port_spots.py`, `hay_probe.py` (all three bisects), game-side tools in the renderer proxy: Ctrl+Alt+1..9 teleport and `[Diagnostics] CrashLog=1` (files in `renderer-source/` of the archive; commits `a6fe7fe`, `c357e8b`).
Candidate outputs live in `D:\Game\Master Rallye\research-output\` (`t4-terrain` = current full Turkey3 package, `t4-objects`, `t4-house1`, `limits-port`, `hay-probe*`); the archive contains only their reports.

## 6. Known gaps and open decisions
1. Collision of the transferred terrain: slabs between the PC and PS2 surface only where a PC triangle has the same footprint, top layer only, at most 8 units thick. Skipped: 612 triangles without a PC twin, 50 lower-layer, 21 too thick, 195 near-vertical. Offline: at 4,000 PS2 columns blocking 578 to 381 and falling 337 to 248 (retail vs patched). Exact alternative, not built: transplant PS2 BSP solid leaves per changed region (carve region, fill with leaf polyhedra, polyhedron clipping for speed), skipping regions inside the PS2 solid exterior shell.
2. Decision pending: port the PS2 solid exterior shell (policy so far: no) and PS2-style soft reset limits (Limit2 lists).
3. Visual quality: PC noise detail layer missing on added ground; PS2-only textures stay 64x64. A global fix = replace the whole PS2 course render data and tag100 (needs a course-DX render writer; only same-topology position patching, index neutralising and template-based model writing exist).
4. Not converted: CARAVAN_ALPHA (alpha-test material flags in DX unknown), huts, shrubs, boats, fences (PLACEMENT_DIFFERS), puddles (own overlay channel PS2OBJ01, still pending its A/B), tyres (material delta), rigid props (tumbleweeds, hay), birds, splines, emitters, triggers beyond the limit lists.
5. Physics props need the native contact/pool work in 4.3.
6. Only Turkey3 was built; other courses need their own object lists and checks (`mesh_pc_presence.py` finds candidates).
7. Risks not yet seen in the game: load time with the 16.5 MB tree, memory pools sized by the tag100 header counts, three-restart stability of the new files.

## 7. Commit list since the track work began
`13535e8` index and TRACK-PORT0; `8914805`/`de13e76` Turkey3 census and T1b; `d3e1bc8` policy v2; `d3c0d62`..`a23dcf4` PS2 BSP reversal and 36-course censuses; `a6fe7fe` teleport; `6dc2220`/`d6daa62`/`9c9becc` probe results, behaviour comparison, limits; `e44a6ed`/`0cb4141`..`e0427ac` limits and hay probes; `c357e8b` crash log; `3bd5863`..`1daaa12` T4a to T4c (house, caravans, tag100 editing, terrain).
