# COURSE-CAP1 — native capacity and authoring readiness

## Outcome and qualification

There is no demonstrated single global Course limit. The stock executable has **39 race registrations**, backed by **36 unique course folders**. Those are a particular catalog and allocation, not established engine maxima. Native record addressing, menu mapping, progress keys, competition stages and resource memory are independent owners.

This phase adds a manifest-driven **offline** Course/Race catalog and executes the original x86 record initializer against computed storage. It does not install a new game registry or claim new menu/save/network capacity. Original registrations and vehicle IDs/classes/order are preserved. COURSE-CAP2 is required for composed runtime integration.

Reference executable: x86 PE32, image base `0x400000`, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. SHA identifies the evidence; the new audit validates PE layout and native instruction/record shapes, not an asset allowlist. Ghidra/REA pseudocode is derived evidence, not original source. Exact assembly and evidence IDs are retained in the single ignored scratch root `.research-output/course-cap1/`.

## Part A — HeritageNewRav AI follow-up

The V-CAP3 owner log contains 44 Quick Race admission events: player ID34 on 11, ID33 on 5, ID29 on 9, ID12 on 19. All use policy **Stock**, with seven requested opponents and `AutoRegistered`. ID34 must be excluded while it is the player, but that alone cannot explain its absence with other players.

The actual cause is a composition defect, not an ID34/DriverID/ClassSlot/resource limitation:

Both provider rows are T2, mode mask7 (Quick Race/Cup/Master eligible), and resolve through the same live MRVC class map. Native DriverID uses a separate ten-entry vector (`0045833D..0045835E`), not the physical CarID. Changing driver capacity is unrelated to this defect.

1. The native T2 builder includes both 33 and 34; its append order ends with 34. Existing V-CAP3 native-loop evidence already establishes this.
2. `00450580` implements a **Sattolo cycle**: the element at ordinal `i` swaps with `rand % i`, rather than choosing among `i+1` positions. Consequently the last original element can never remain last. Native selection copies the shuffled list and pops its last element at `004583EB..00458428`.
3. The unmodified native chooser normally consumes subsequent entries from that same shuffled list. Randomizer and Stock's extended-AI path instead rebuild the physical pool for each slot. That repeatedly asks for the one position the last source element cannot occupy. Thus the last newly appended eligible ID starves; ID33 can still be selected.
4. `MRFilterAiPoolV1` now applies a full Fisher–Yates permutation to **rebuilt** pools before the unchanged native cycle. A uniform permutation remains uniform under the following native permutation. Stock with the normal three AI keeps the original native order and chooser. This is a general last-element fix, with no ID34 exception.

This also explains the V-CAP3 observation: appending34 moved33 out of the starving last position. Enlarging the list had exposed the general algorithm defect rather than proving that a particular numeric ID was unsupported.

`Stock` means native selection within retail count, and the player's native class in the existing extended-count implementation. `AutoRegistered` is the display name of `Addons/Include=1`; it admits registered, materializable and mode-qualified entries, not mandatory appearances. `WhenNeeded` permits repeats after eligible unique IDs are exhausted; it does not admit the player's vehicle or add participants. Mode/class filtering and Invitation/Challenge rules remain unchanged.

The new `AI_ROSTER_FINAL` is emitted once after the existing native Quick Race setup returns, using its published `Race/CarN` values. It reports policy, player, final opponent slots, observed native/policy pools and per-addon reasons. A duplicate phase-return callback does not emit a second report. Pools are deduplicated; displayed long lists are capped at 64 with their total count. This is the final **grid-publication** boundary, not a claim that every actor has finished loading or driving. Unavailable observations are identified explicitly, rather than invented.

Private follow-up: sibling Vehicle worktree `.research-output/vehicles/v-cap3/ai-followup`. It retains the accepted 35-record resources/launcher and adds the corrected Extra Options pair. No Course experiment is installed in that candidate. Renderer binary/bridge are unchanged. Use its `Launch-input.cmd` or `Launch-both.cmd`; choose a player other than 34 and inspect the final report. Test Stock extended count and, optionally, V2 `QuickRace=2` (T2), keeping `Include=1`. ID34 is eligible, not guaranteed in one random grid. Then select ID34 as player and verify `human-excluded`. Confirm ID33 remains selectable as AI. No broad vehicle regression is requested.

Tests: exact original x86 shuffle executed for 256 seeded draws (all 13 other candidates reachable, last source ID34 never first-popped); 2048 C++ control cycles reproduce starvation and show all 14 candidates reachable after correction; production pool/provider harness passes; production final-report phase code passes with native snapshot/sink fixtures; existing option/menu/tyre/model/Renderer bridge and mutable-page harnesses pass. Input/both suspended preflights pass, **game thread not resumed**. New corrected gameplay remains owner confirmation.

## Identifier map

| Identity | Actual owner / meaning | Sharing and independence |
|---|---|---|
| Native race registration ID | Nonnegative integer index of a 44-byte record | Stock 0–38. Frequently called Course/Track by UI/Broker; not a separate folder index |
| SDK course key | New stable string key in `mr-course-registry/1` | Catalog identity for geometry; no claim of an existing native numeric Course Registry |
| Course folder/model | String such as `course/france_s1/frances1` | File namespace/model cache key, no proven global numeric folder ID |
| Race scene | `RaceTest/<name>` string, loaded as DataScene XML/HNT | Supplies landscape binding, markers, objects, conditions, AI dataset; can share a geometry folder |
| AI dataset | `ICont/<name>.sfl` from the scene | Can differ between route configurations on the same geometry |
| Menu index | Mode/group and local ordinal | `0047F2B0` maps it to a race ID; `0047F320` does the reverse. These are not general ID identity maps |
| Competition stage | Position in a particular authored event | Cups/Invitation currently assume contiguous race-ID ranges; not a reusable global Course ID |
| Progress/artwork key | Separate language/image/progress resource index | Must be registered explicitly; extending the race array does not extend these tables |

Invitation records 36/37/38 share scene names with 24/9/29. The extracted catalog preserves this. New fixture registrations 39/40 deliberately reuse existing scenes to exercise address/storage construction; they are **not independent imported courses**. Different routes on shared geometry require distinct RaceTest/AI bindings, not simply another display label.

## Native limits and owners

Full exact sites/preimages and evidence references: `native-limits.json` and the private `delivery-proof/capacity-report.json`.

| Classification | Owner and address | Observed value / consequence |
|---|---|---|
| Stock Native | Singleton `0045A3C0`, pointer `006F5ED4`, constructor `00458CD0` | One object contains vehicle records and a trailing race array |
| Stock Native | Allocation operand `0045A3E0` | `0xC00 = 4 + 26*52 + 39*44`; a layout, not a global maximum |
| Current SDK | Accepted V-CAP3 layout | `4 + 35*52 = 0x720` race base; 39 race rows; allocation `0xDD4` |
| Stock Native / Patchable | Race ctor count operand `00458D0F`, dtor `00458E29`, unwind `006867AC` | `push 0x27`, sign-extended imm8. Blindly changing to 128 is invalid; widen complete instructions in every lifetime route |
| Stock Native / Patchable | Race bases `00458D12`, `00458E2C`, `006867B3` | Original `0x54C`; V-CAP already relocates these. A Course patch must consume the final shared layout |
| Stock Native / Patchable | `004598D0`, `0045A330` | 39 constructors; 44-byte records, nine DWORD values plus owned scene string and vtable. Field ID is full DWORD; no global maximum established |
| Stock Native / Patchable | 39 initializer LEAs, 11 direct consumer displacements | All original sites recorded; direct reads generally lack a new registry-count check. New lookup bounds must be explicit |
| Stock Native / Patchable | `0047F320` / `0047F2B0` | Hardcoded inverse maps for Master 0–9, five Cups 10–24, Challenges 25–35, Invitation 36–38 |
| Stock Native / Patchable | `0047E2D0`, `0047ED10`, `0047ECB0`, RaceSelect.xml | Authored groups/widgets, navigation, image/name/distance/rating and availability. New registration alone creates no new menu item |
| Stock Native / Patchable | `0045B170` | Cup ranges 10–12/13–15/16–18/19–21/22–24, Invitation 36–38; advancement increments race ID |
| Stock Native / Patchable | `004AE7A0`, table `006F65C8`; lookup `004AF430`, mapping `004AF4F0` | Named Won keys and class/event/stage arithmetic. Invitation's `stage+0x6A` is not an unbounded namespace |
| Stock Native / Patchable | `004AF0E0`, table `006F6780`; `004B0000`, `004AFF80`, `0045B3F0` | BestTime index 0–38 are race keys; 39 is aggregate `BestTime_Master`. Indexing by a new Race ID corrupts meaning; 40 is not another usable race key |
| Stock Native | `004ABF20` / `004AC2B0` | Broker integer getter/setter for selected race, full scalar transport. This does not prove every network/save consumer is equally wide |
| Stock Native | `00449A50` / `0047B780` | Scene load and Quick Race publication use registration scene string at original record+`0x1C` |
| Stock Native | `0044FEC0`, `0045EB30` | Challenge reads authored human/opponent fields at record+`0x24/+0x28`; restrictions must remain event-owned |
| Stock Native | `004C0B20`, `004BC590` | Replay producer passes race-name and vehicle-family strings. Existing replay investigation does not establish all playback/network high-ID admission |
| Stock Native / resource issue | `0053BA80`, budget operand `0053BA99`, eviction `0053BE70`, land query `006068A0` | 32 MiB stock model cache is independent of Course count. Existing multi-landscape research found live-scene eviction; larger cache was an experiment, not infinite content capacity |
| Unconfirmed | Network packet field widths; every replay playback and saved competition path for new registrations | Do not infer a byte or DWORD global limit from the selected Broker/initializer paths. No high-ID runtime support is claimed |

The inspection covers all **34 Ghidra-resolved direct callers** of the shared registry getter, the constructor/register/destroy/unwind family, all 39 known race initializer addresses and the 11 direct race consumer displacements used by V-CAP relocation. Additional targeted UI, progress, replay and cache owners were inspected. This is a bounded, reproducible consumer map, not a proof that no indirect/computed or protocol consumer exists. Every unresolved owner is a COURSE-CAP2 qualification gate.

Per-course SFL grid dimensions, marker lists, BSP nodes and land-database cells are separate resource-size domains. SFL uses DWORD dimensions and a byte heading per cell, not a byte Course ID. The Course SDK's parser budgets (for example tag100 node/nesting and tag1400 cell limits) are defensive tool limits, not established EXE limits. Compiled visual draw-local indices, coordinate precision, split counts and physical-object budgets need their own qualification for large external scenes; none establishes a global registration-count bound.

Stock mode ranges and frontend counts are separate from record capacity. The one demonstrated numerical boundary here is the existing **signed imm8 instruction encoding** at 127/128; it is patchable, not a proven engine limit. Native 44-byte initialization/field addressing was exercised at counts 127,128,254,255,256,257,513 with deliberate scene aliases. Constructor lifecycle, save tables, menus, networking and real independent resources were not qualified by that test.

## Existing experiments: use the latest evidence

`docs/course-new-entries.md` and `patch_invitation_entries.py` retain stale headline/status strings. Their later E1.4 section records the owner result that all **five** Invitation races load and finish after the cache/progress guard changes. E2.4/E2.5 additionally record the own BSP builder and remaining collision defects. Those newer observations take precedence over the earlier “not tested” headings. They do not establish arbitrary stage counts or independent Won/BestTime persistence for stages 4/5.

The old patch is a fixed five-stage experiment: it skips unsupported progress writes and guards BestTime reads. It does not implement a scalable catalog. Its raw EXE/cave and shared-object writes must not be layered over V-CAP3. The generated conflict audit compares this exact experimental plan with accepted V-CAP3 operations; no such combined binary was installed or declared compatible.

## Configurable architecture

`course_registry.py` separates geometry identity, scene/race configuration, mode menu placement and competition stage lists. Original IDs are fixed. The offline validator rejects overwritten original fields/scenes, missing keys, duplicate IDs, uninitialized holes, unsafe paths, arithmetic overflow and attempts to mark unimplemented competition routes runtime-enabled. Native parameters whose full semantics remain unresolved retain neutral DWORD field names rather than fabricated meanings.

`course_capacity_audit.py` extracts the real 39 registrations, links landscape and SFL resources from their scenes, checks mandatory DX/scene/HNT/SFL bindings, computes storage and emits the catalog plus a native initializer proof. Transitive dependencies still use the existing Course SDK/HNT diagnostics; this is not a universal asset-closure validator.

For COURSE-CAP2:

1. **One startup layout composer** owns shared vehicle/race allocation, construction, initialization, destruction and unwind. Inputs are accepted Vehicle Registry and Course Registry manifests. Both counts and bases are computed before the singleton exists. Never grow/realloc live native strings.
2. Keep MRVC v1 compatible for Extra Options. Add a separately versioned proposed `MR_COURSE_REGISTRY_DESCRIPTOR`/MRCR descriptor with count, stride44, registry base, stable identity mapping, bounded lookup and menu/stage maps. This is a proposal, **not a new shipped ABI**. Neither Extra Options nor Renderer becomes mandatory for Course SDK.
3. Replace both directions of menu mapping together with manifest-built group lists and cloned native widgets. Images, localized text and unlock policy have distinct bindings. Do not extend ordinal assumptions by merely increasing a widget count.
4. Replace contiguous competition arithmetic with explicit ordered registration lists. Preserve original routes/rules and progress keys. Additional stages need distinct namespaced persistence, explicit ownership and migration; skip/clamp guards from the five-stage experiment are not the final solution.
5. Preserve every original save key. New progress lives in a versioned sidecar/catalog namespace until native named-key extension is fully qualified. Active competitions bind stable route/stage identities and gameplay dependencies (markers/AI/collision/rules), excluding texture pixels. An absent route or incompatible active schedule must stop with diagnostics, not substitute a random course or overwrite the original save.
6. Qualify input bounds at every consumer. Registry addressability, global race availability, individual championship stage capacity, networking and resource-memory limits remain separate. Select engineering budgets from measured memory/consumer results, never call 64/128/256 the true engine limit.

No hot reload, new class, replacement original course or universal donor importer is introduced in COURSE-CAP1.

Concrete implementation targets for the next phases (new files below are proposals):

| Target | Change | Acceptance gate |
|---|---|---|
| `course_registry.py`, proposed `tools/build_course_registry.py` | Explicit menu/stage/progress bindings, reserved identities, resource catalog compilation | Repeatable manifest edits with all original identities unchanged |
| Proposed `tools/course_capacity_native.py` and shared layout composer | Compose accepted Vehicle layout with race allocation/count/lifetime/unwind and guarded lookup | Original constructor ownership once, correct destroy/unwind, boundary probes; no sequential legacy patch |
| Accepted runtime launcher, in a separate integration worktree | Admit composed descriptors/resources and active route/save contract before startup | SDK alone/Extra/Renderer combinations; original saves unchanged on rejection |
| Menu adapter and progress binding layer | Both mapping directions, native widget resources and namespaced new progress | New entries navigate/load/return, stage advance and persistence without clamping unrelated keys |
| `course_sdk.py`, proposed Blender `course_collision.py` | Typed actual physical diagnostics using existing tag100/BSP/land readers | Stock collision vs visual terrain separation and reproducible transforms |
| Proposed Marker Builder, existing `course_entry.py` / bounded writer | Generated route transaction with marker inventory, ground/heading checks, AI field | No-op preservation, single-edit export, physical-grid/checkpoint/AI owner checks before donor imports |

## Blender and COURSE-VIS1 readiness

| Layer | Current implementation/evidence | Remaining work |
|---|---|---|
| Visual geometry | Rev135 DX reader and Blender import; atlas OBJ/MTL export; v7 GXM/TXT **writer already exists**; existing Demo cooker route | A unified editable course scene/export transaction; preserve unsupported draws and material semantics, verify normals/UVs rather than flattening everything |
| Physical collision | Tag100 recursive reader, existing `course_bsp.py` encoder/solid-leaf polygon-clipping builder, own-tree runtime findings | Integrate a real collision viewer in Blender/public CourseProject. Display actual BSP half-space boundaries/cells; render mesh or box proxies must be identified as reconstructions |
| Collision extraction | Actual compiled tree planes/leaves are readable | Original source triangles are not necessarily recoverable. Finite collision surfaces require clipping planes by ancestor volumes and a documented domain, not drawing every infinite plane as a triangle |
| Ground/surfaces | Land-database runtime path and structural tag1400 reader, source terrain builder | Complete generic material/surface/physics mapping, preserve code/index references; no claim of a full arbitrary compiled-land writer |
| Coordinates | Existing DX-to-Blender `(X,-Z,Y)` convention; GXM source-to-DX `(x,z,-y)` documented | Centralize transform metadata/unit checks in export; do not apply both conversions twice; verify scale and normals for each imported donor |
| Start/finish/splits | G0 bounded writer/runtime accepted; four start markers, finish four or five; sphere split centers/radii | Marker Builder must handle variable finish topology explicitly, fit to physical ground and validate order/direction. Do not truncate five-marker finishes |
| RaceLine/limits | Existing ordered Marker Pos editing; progress/rank and selected limits have targeted runtime evidence | New topology/Marker Dir semantics and all boundary effects need qualification. Nearest-sample progress and single-valued SFL create crossover/self-overlap constraints |
| Route synthesis | Existing `course_entry.py` route frames, anchoring, checkpoint distribution, transferred limits | Expose as a separate explicit generated-route transaction, validate joins/clearance/start grids/checkpoint sequence. It is not a universal road detector |
| AI field | SFL decoded; heading/pursuit synthesizers and later runtime observations exist | Tune steering/corridor recovery on new routes and preserve route direction. An extractor alone does not supply AI paths |
| Scene dressing | Template-preserving scene generation, terrain merging and experimental physical object proxies | General roundtrip of cameras, pace notes, sounds, water, sky, animated/physical objects, start dressing and unsupported component properties remains incomplete |

COURSE-VIS1 should first load a classic stock course into one Blender project with **separate visual terrain, actual collision diagnostics, route/limits, markers and object inventories**. Export no-op preservation and single-edit validation precede importing donors. Keep original unsupported data opaque and explain what cannot be exported; do not silently replace it with visual geometry.

Source Garage's vehicle extraction/scene adapters do not establish course import. 4x4 Evolution 2 is the first technical donor: validate terrain/road/object/material partitions, axes/units, physical collision and route metadata in an intermediate Blender scene before MR cooking. Rally Trophy Kenya is the first artistic target after that contract is proven. RalliSport Challenge1/2, Dakar2, CMR04/2005, Rally Championship Xtreme and other donors require their own track-semantic adapters. No archive inventory or converted OBJ is labeled a playable course.

## Reproduction and validation

The local audit needs the existing Capstone and Unicorn packages. On this machine Capstone is in the Scoop Python site-packages, Unicorn in Python315. No new dependencies were installed. In PowerShell:

```powershell
$env:PYTHONPATH = 'src;tools;C:/Users/MaRZ/scoop/apps/python/current/Lib/site-packages'
python tools/course_capacity_audit.py --exe ../corpora/retail/MRallye.exe --data-root ../corpora/retail/Data.sma_unpacked --output .research-output/course-cap1/next-proof
```

To rebuild a different catalog, pass `--manifest <registry-manifest.json>` and a fresh output. The native initializer proof runs real `0045A330`; string assignment/release are mocked. It does not run original registry allocation/lifetime, native string ownership, game UI, AI driving, collision or saves. The caller's input files remain unchanged. Catalog paths are relative.

88 focused Course/registry/XML/tag100/tag1400 tests passed. The 41-record storage proof and seven boundary profiles passed; mandatory source bindings were checked. The existing 28 dirty Course files are byte-preserved. No working/Pristine installation changed, no game thread was resumed in automated validation, and no DLL/EXE was installed or published. Full changed-file/source/build/preservation manifests and hashes accompany the private outputs.

Next phase **COURSE-CAP2**: shared layout/lifetime composer, menu bidirectional mapping, progress ownership and safe stage routing; then a private runtime candidate with new scene registrations and exact owner checks. **COURSE-VIS1**: real collision/terrain viewer and loss-preserving authoring contract, followed by the Evo2 technical scene and Rally Trophy Kenya art prototype. The Course global limit, protocol limits and fully generalized stage persistence remain explicitly unconfirmed.
