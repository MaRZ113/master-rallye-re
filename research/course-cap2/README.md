# COURSE-CAP2 private native candidate

Status: **implemented offline QuickRace candidate, NOT GAMEPLAY QUALIFIED**.
The owner must still verify selection, driving/AI, finish/Results, return and
save/restart. Suspended-process checks do not establish those observations.

## Architecture and delivered scope

`tools/build_course_registry.py` consumes the accepted Vehicle runtime **and its
source build manifest**, a Course manifest, original retail executable, and
optional newly owned resources. Vehicle capacity comes from the actual MRVC
profile. The composer reconstructs the accepted transaction, appends Course
code/data to its existing arena, and regenerates one RVP transaction against
original retail preimages. It never installs files or emits a patched game EXE.

The current fixture retains Vehicle IDs0–34 and every original Race ID0–38.
Its shared object is `4 + 35*52 + 41*44 = 3628` bytes, race base `0x720`.
The native extension remains in the accepted 512 KiB arena; its Vehicle prefix
and both original RW/NX pages are preserved. The final operation count is in
`validation.json`, including the accepted canary. The launcher's 512-operation safety
budget is a tooling budget, not a native Course capacity claim.

| Changed component | Responsibility |
|---|---|
| `course_runtime.py` | Shared layout, lifecycle hooks, actual string construction, new native records, menu maps/captions, scoped progress dispatch, explicit stage lookup/advance, admission diagnostics |
| `course_registry.py` | Identity excludes the proven caption field; image mappings and textures remain outside identity |
| `build_course_registry.py` | Input verification, complete resource composition, private save seeding, gameplay contracts, single transaction/launcher build |
| `prepare_course_registry_candidate.py` | Reproducible France route fixtures and full manifest generation |
| `package_course_registry_candidate.py` | Calls the existing private host packager; no second runtime loader |
| `check_course_registry_progress.py` | Read-only semantic save comparison, including original Master and Won keys |
| Vehicle `build_runtime_launcher.py`, `runtime_launcher/src/main.cpp` | Separate MRCR descriptor verification/child environment; MRVC v1 unchanged |
| Vehicle `package_vehicle_registry_candidate.py` | Explicit private research-root support, retaining existing default confinement |

No Renderer or Extra Options gameplay source was changed. Extra Options is
rebuilt against the complete composite manifest; its accepted AI runtime core
is byte-identical. The accepted Renderer is copied into private hosts only.

### Native ownership

- Allocation: `45A3E0`; race stride44, Vehicle stride52.
- Vector constructor: `458D0E`; destructor: `458E28`; unwind: `6867AB`.
  Counts use PUSH imm32. The destructor retains EAX, constructor retains ECX.
- The original last initializer call `459FD7` first initializes record38 once,
  then constructs temporary scene strings with `4D11D0` and calls the original
  `45A330` for every addition. The original vector constructs all records once.
- `47F2B0` and `47F320` share one forward/reverse map. Added group-0 widgets and
  the `47ECB0` position publisher use final manifest positions/counts. Original
  groups and unlock-conditioned counts outside the changed group are retained.
- New records have their own captions and explicit flag/image bindings. Original
  scene/resource files are not overwritten. New resources can be supplied as a
  full Course set; the fixture generator is optional.
- Admission at the Course Select confirm action admits new records only when
  QuickRace is enabled, split-screen is disabled and network browse is false.
  Other contexts receive a diagnostic dialog and no
  RaceID write. Invalid table indexes stop with a diagnostic before access.

### Progress and competitions

New records use `Progress/BestTimes/CourseRegistryV1/<stable-progress-key>`.
Race-context getter/setter copies use their own key table. All known race
owners, **including shared Results**, are redirected; the original Master
aggregate owners `453BD0/453D10`, default reset `4B0090`, functions `4B0000` /
`4AFF80` and original table ownership remain intact. Original table index39
still means `BestTime_Master`, never new Race ID39 in an aggregate context.

Gameplay contracts combine accepted Vehicle identity/dependencies, Course keys,
scene/AI bindings, semantic start/finish/grid/splits/route/limits, AI bytes and
native DX trailing collision/surface data. Texture pixels, image frames,
captions and decorative scene lists are excluded. New save keys carry native
`SavePlayerState=True`. The real game's serialization/reload remains an owner
gate; it is not inferred solely from XML flags or emulated calls.

For an existing private save, supply `player_state_source` and
`previous_course_contract`. Active competitions or existing Course progress
require the exact compatible gameplay contract. On mismatch, building stops
before copying/writing the save. Changed dependencies require an inactive fresh
profile; no implicit progress migration or reset is performed. The accepted
launcher's exact-save/normal-owned-exit baseline guard is retained.

The native Cup/Invitation stage ordinal and next stage are now obtained from
explicit lists, rather than subtracting a first RaceID and incrementing IDs.
Stock schedules, trophy/unlock logic and original progress bindings remain
unchanged. The generated lookup also accepts noncontiguous schedules; the
fixture contains the disabled independent schedule `[40,39]`.

**Custom championship UI, result storage and restart are not implemented in
this candidate.** A new competition with `runtime_enabled=true` is rejected.
The executable lookup/table is infrastructure, not qualification of a playable
new Cup. Stock Master/RallyeCup/Invitation/Challenge remain supported through
their existing registrations. New records are not admitted into these modes,
split-screen or network play; no fallback to an old Course is supplied. Closing
this remaining competition integration needs separate namespaced per-stage
results and Cup start/result/save owners, not the old five-stage skip patches.

## Reproduction

Run from the Course worktree with its current authoring dependencies present:

```powershell
$env:PYTHONPATH='src;tools;tests/synthetic'
python -c "import sys,runpy;sys.path.append('C:/Users/MaRZ/scoop/apps/python/current/Lib/site-packages');sys.argv=['prepare_course_registry_candidate.py','--vehicle-source','../master-rallye-re-v-cap','--vehicle-runtime','../master-rallye-re-v-cap/.research-output/vehicles/v-cap3/ai-followup/runtime','--retail-exe','../corpora/retail/MRallye.exe','--output','.research-output/course-cap2/next-build'];runpy.run_path('tools/prepare_course_registry_candidate.py',run_name='__main__')"
```

For a prepared Course, provide the full catalog to `build_course_registry.py
--manifest <compose.json> --output <fresh-private-output>`. New rows carry
`course`, `scene`, `icont`, nine confirmed native DWORDs, `title`, `modes`,
independent `progress_key` and `menu {group,position,flag_frame,screenshot_pair}`. Menu positions
may reorder additions independently of RaceID. Currently they occupy group0
after its three original entries. Holes, overwritten original registrations,
duplicate positions/keys, incomplete resources, unqualified modes and budget
overflows are rejected. `runtime_budget.max_shared_bytes` is an explicitly
chosen qualification budget, not a statement of the engine maximum.

Optional per-race `artwork {screenshots:[relative-png,relative-png],flag_png,
provenance}` plus an explicit compose `artwork_root` appends native screenshot
pairs/flags with the existing SDK sprite-bank and FEED/BGRA32 APIs. Inputs must
match their selected template dimensions. Original sprite records and texture
files remain unchanged; new frame indices are assigned independently of RaceID.
The pipeline validates actual bank bounds. The append-only artwork check added
two screenshot frames and one flag, verified CRCs and all original frame bytes,
and confirmed that changing artwork does not change the gameplay contract.

The accepted Vehicle/Extra sources are imported read-only as separate tooling
inputs. Course Python modules use an isolated namespace to avoid accidentally
importing an older Vehicle SDK from the Course worktree. Existing dirty Course
authoring files are neither staged nor moved into other worktrees; the private
source snapshot records the exact dependencies used for this build.

## Validation and owner handoff

The final candidate is `.research-output/course-cap2/owner/candidate`.
It has `Launch-sdk.cmd`, `Launch-input.cmd`, `Launch-renderer.cmd` and
`Launch-both.cmd`, plus an English source/build report and a local owner checklist.

- 101 focused Course tests and 8 launcher descriptor/compatibility tests pass.
- Real x86 record field writes, temporary ownership call counts/stack balance,
  constructor/destructor/unwind registers, menu bijection, arbitrary additive
  order, namespaced progress return ABI and shared Results routing were checked.
- Explicit native stage lookup was executed with `[40,12,39]`, including its end
  and invalid-input paths. Original Master aggregate byte ranges are preserved.
- Counts128/255/256/257 were checked for generated lifecycle/addressing only.
  They are **not** gameplay-qualified counts or a proven global limit.
- A second full bundle build with the same manifest/compatible private save
  reproduces the sealed native/resource artifacts; no per-slot code edit.
- Four private hosts pass suspended process installation/readback and descriptor
  verification. **The primary game thread was not resumed.** This does not test
  DLL initialization, rendering, native UI or a completed race.
- Build timing: approximately18 s composition,57 s complete bundle verification,
  64 s including the launcher compilation on this machine. Full resource hashes
  are verified at the build boundary; no per-frame work was added.

The fixture registers two independently named/resampled full France1 route
scenes with their own RaceTest/HNT/SFL paths. It retains the original full limit
polylines, source grid/start/finish intent and source AI field bytes. It is not
two imported terrains, and resampling/AI behavior still needs driving evidence.

The original 28 dirty Course files and working/Pristine installations are
preserved. Owner checks must establish the complete menu -> new scene -> grid/
AI -> start/checkpoints/finish -> Results -> menu -> restart/progress loop.
COURSE-VIS1 remains the next direction after this runtime candidate and its
explicitly outstanding competition/save qualification are accepted.
