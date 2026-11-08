# Native owner and hook map

All addresses below are VAs in the pinned 32-bit retail image with image base
`0x00400000`; RVA is `VA - 0x00400000`. Evidence comes from the exact-build
Ghidra 12.1.4 exports in ignored `scratch_rmod1/ghidra/`, plus canonical
research plans. The exports identify stripped functions as `FUN_...`; semantic
names below are project labels, not symbols recovered from the executable.
The checked exports report an unknown formal calling convention, so this map
records only visible register, stack and return-cleanup facts. It does not
invent C++ prototypes.

## Verified generation and selection owners

| Owner | VA / RVA | Caller and inputs | Output / lifetime | ABI evidence and R-MOD overlap |
|---|---|---|---|---|
| Quick Race setup `FUN_0047B780` | `0x0047B780` / `0x7B780` | Quick Race Start path. Reads selected player physical ID via `FUN_004ADFB0` with active player context in ECX; obtains registry class; calls native chooser in the single/split path. | Publishes `Race/CarN` fields at a fresh Quick Race setup boundary. Restart/loading reuses the current Race roster. | Begins `PUSH ESI`, ends `POP ESI; RET`; observed accessor calls are member-like ECX calls. Two xrefs from this owner call `0x00458090`. Existing F3 changes selection seams inside its chooser, and opponent extender owns the Quick Race count/Start UI. A player override must share the prepared UI ID and Car0 publication. |
| Physical chooser `FUN_00458090` | `0x00458090` / `0x18090` | Exactly two call references from `0x0047B780`. ECX is a native vector/context. Stack slots carry count, class and excluded physical ID inputs established by prior analysis; the function consumes `0x14` bytes on return. | Builds eligible physical IDs, shuffles/refills a temporary vector, selects a physical ID, derives class from registry, selects DriverID separately, writes the target `CarN`. | Epilogue is `RET 0x14`; this is a critical ABI constraint. F3's selector hooks are inside this function at `0x45810B`, `0x458379`, `0x4582D5` per plan. Do not install a competing selector/allocator hook. |
| Vector length `FUN_004116A0` | `0x004116A0` / `0x116A0` | ECX points at a vector-like structure; reads `[ECX+4]` and `[ECX+8]`. | Returns element count in EAX, zero if begin pointer is null. Called before the chooser decides to refill. | Leaf sequence ends `RET`, no stack cleanup. Exact assembly is short and exported. |
| Pool shuffle `FUN_00450580` | `0x00450580` / `0x10580` | Two stack pointers are loaded from entry stack into EAX/EBP and used as a range. | In-place random shuffle of physical-ID values; chooser copies the shuffled saved candidates into its temporary pool. | Saves EBX/EBP/EDI and conditionally ESI; returns with plain `RET`, so caller owns stack arguments. Uses CRT random call `0x005C37B8`. |
| Driver chooser `FUN_00458980` | `0x00458980` / `0x18980` | ECX is a separate driver-list object; one stack output pointer is written. | Returns success in AL and emits a DriverID independently of CarID selection. | Epilogue restores EDI/ESI/EBX/ECX and `RET 4`. Do not force a driver's value to avoid a repeated vehicle. |
| Car field setters | `0x004ACAF0`, `0x004ACC10`, `0x004ACCD0` | Native Broker/object access in ECX and stack values visible in caller. | Publish per-participant CarID, CarClass and DriverID respectively. | Called for each slot by Quick Race and other native builders. Preserve ordering and per-slot ownership; don't treat a physical ID as an object pointer or participant index. |

The chooser export spans `0x00458090..0x004584D6`; its byte SHA256 is
`2daec5f26455c98bfa399308ce8a3030ebe5871dfe4fd13a675526bb97842a71`. The
empty-temporary-pool branch calls `0x00450580`, copies the saved eligible
list, chooses an element, and erases it from the temporary list. Thus the
native implementation deliberately has a refill path. This does not by
itself prove that a particular seventh selection repeats a CarID safely.

## Mode-owned roster builders

| Mode | Frontend owner and builder | Caller/callee contract visible in retail | Storage and active R-MOD seams |
|---|---|---|---|
| Rallye Cup Type 6 | Entry owner `0x0045BE10` -> `0x0045ABC0` | `0x0045BE10` selects counts/class path, then calls builder. The builder consumes three stack bytes/words (epilogue `RET 0xC`); observed caller establishes native parameters before the call. The exact formal types are not recovered. | Fresh Cup writes `RaceData/CompetitorN`; `0x0045B170` stage advance/restart reuses it. F3 hooks at `0x45AC79`, `0x45AF0F`, `0x45AE66` are class-selection seams in the shared builder. |
| Invitation Type 8 | Frontend path `0x00462678` / shared `0x0045BE10` -> `0x0045ABC0` | Uses the shared Cup owner with special cup/class selection; ordinary Invitation pool is T3 core IDs 14..20. | One generated roster persists through its three stages. Same F3 shared Cup hooks; any new count must respect Invitation's special pool and should not be inferred from Cup. |
| Master Rallye Type 5 | Entry owner `0x00452590` -> `0x00451DD0` | `0x00452590` passes context in ECX; selector consumes three stack words (`RET 0xC`). New competition path chooses roster size and class. | `RaceData/CompetitorN` is copied to `MasterRallye/CarN`; save/load owners `0x00452640`/the audited load path preserve roster; stage advance `0x00452370`, resume reuses saved entries. F3 hooks at `0x451E90`, `0x4520D2`, `0x45202D` are class-selection seams. |
| Challenge Type 7 | Screen owner `0x0045EA60` -> builder `0x0044FEC0`; fixed authored choice consumed around `0x0045010E` | Event index is passed on stack; builder ends `RET 4`. Reads event-indexed authored vehicle IDs from the Challenge table and publishes the native participant. Exact formal object type is not recovered. | Preview has separate prepared identity/cache and must match the race consumer. F3's Challenge Preview cache intercepts preview/race identity sites. Do not treat Challenge as an ordinary random pool or count owner. |

The exact mode map and runtime boundaries are in
`research/r-ai1-2/mode-map.json`. Cup/Invitation and Master Rallye persistence
are prior `CONFIRMED_BY_RUNTIME` evidence. F3 class hooks select policy; they
do not establish arbitrary participant counts for those modes.

## Grid generation

`FUN_0048E2D0` (VA/RVA `0x0048E2D0`/`0x8E2D0`) owns race scene preparation and
calls `FUN_0048EB40` (VA/RVA `0x0048EB40`/`0x8EB40`). The caller places an
argument on stack and supplies a context in ECX. The callee returns with
`RET 4`, reads course `StartArea` data, observes participant-count state,
calculates count-based positions, and publishes transforms for `Race/CarN`.
The native typed meaning of the stack argument is not established by the
stripped function signature; preserve the caller's actual value and ABI. The
existing R-MOD patch plan has no grid operation. Any future grid feature must
be owned by the unified patch planner and installed before transforms and AI
paths initialize.

The 36-course structural audit reports 39 registrations and `Car0..Car7`
templates, but no live terrain-clearance proof. The planned reorder should
permute native ordinals only and remain disabled by default until a per-course
runtime qualification exists.

## Existing F3 operations and composition

The current research plan file `research/r-mod1/native-patch-plan-f3.json`
has 17 operations and pins the retail image SHA. It records Quick Race,
Master Rallye, Cup/Invitation class-selector seams, Quick Race opponent-list
and count navigation/Start, and Challenge preview-cache ownership. It declares
the shared runtime remote allocations and exact preimages. That JSON is a
static plan template (`runtime_qualified=false`); it is not a byte-for-byte
export of the public DLL package. The published release is separately pinned
in `published-baseline.json`.

Required composition rule: one patch owner validates all operations and
conflicts against the pristine preimage before activation. New work should
reuse existing selection callbacks where possible, never patch the same
instruction through a second injector. When a feature is disabled, replay the
original instruction/call and continue at its exact boundary. No hook may read
Race/NumCars before native setup has published it.

### F3 template hook ranges and original bytes

The ranges below come directly from the F3 JSON template. They are a
composition/overlap audit, not a claim that the public DLL has identical
relocation addresses. The JSON records replacement bytes, feature masks,
remote allocations and exact source-image identity separately.

| VA / RVA | Exact original bytes | Static owner |
|---|---|---|
| `0x005C4602` / `0x1C4602` | `55 8B EC 6A FF` | Shared OEP bootstrap before retail constructors. |
| `0x0045810B` / `0x5810B` | `8B 84 24 8C 00 00 00` | Quick Race selector initialization. |
| `0x00458379` / `0x58379` | `8D 4C 24 30 E8 1E 93 FB FF` | Quick Race selector loop. |
| `0x004582D5` / `0x582D5` | `8A 94 24 94 00 00 00` | Quick Race selector end. |
| `0x00451E90` / `0x51E90` | `8B 84 24 90 00 00 00` | New Master Rallye class selection. |
| `0x004520D2` / `0x520D2` | `8B 44 24 38 85 C0` | Master Rallye selector loop. |
| `0x0045202D` / `0x5202D` | `8A 8C 24 90 00 00 00` | Master Rallye selector end. |
| `0x0045AC79` / `0x5AC79` | `E8 82 3A 05 00` | New Cup/Invitation class selection call. |
| `0x0045AF0F` / `0x5AF0F` | `8B 44 24 34 85 C0` | Cup/Invitation selector loop. |
| `0x0045AE66` / `0x5AE66` | `8A 8C 24 8C 00 00 00` | Cup/Invitation selector end. |
| `0x00479DCB` / `0x79DCB` | `8B 54 24 14 89 74 24 28` | Quick Race opponent-list append. |
| `0x0047A32C` / `0x7A32C` | `83 FD 02` | Quick Race opponent-count arrow bound. |
| `0x0047AD0C` / `0x7AD0C` | `E8 6F 0A 00 00` | Quick Race Start call to native setup. |
| `0x0045EC35` / `0x5EC35` | `8B BC 38 74 05 00 00` | Challenge prepared preview identity. |
| `0x0045E511` / `0x5E511` | `E8 BA 58 08 00` | Challenge preview cache reset on entry. |
| `0x0045EA9A` / `0x5EA9A` | `E8 71 EE FF FF` | Challenge preview cache reset on Back. |
| `0x0045010E` / `0x5010E` | `8B BC 38 74 05 00 00` | Challenge race consumes prepared authored identity. |

The checked F3 plan has 17 operations, zero overlapping ranges, and all
expected preimages match the exact retail file offsets. New operations must
join this single patch owner, pass the same conflict checks, and preserve the
original ABI and disabled-path behavior.
