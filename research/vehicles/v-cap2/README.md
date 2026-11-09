# V-CAP2: configurable native registry integration

Status: **implemented private runtime candidate; gameplay qualification pending**.
This extends the accepted SDK33 instead of replacing it. No installed EXE, DLL,
save, Pristine asset or Course SDK file was changed.

## Delivered architecture

`tools/build_vehicle_registry.py` consumes one `mr-vehicle-registry-build/1`
manifest. `capacity_profile` contains the existing `mr-capacity-profile/1`
record count, explicit T1/T2/T3 selection maps and memory budget. Each addition
supplies an existing SDK `project`, validated author `build` and `physical_id`.
There is no per-ID native patch implementation. Both `vehicle_sdk.py
registry-build` and the existing `build_sdk_roster.py` entry point accept it.

The builder verifies the accepted SDK33 compiled parent, retains its allocation
prefix, appends the configurable core and native consumers, and generates one
atomic RVP transaction against original executable preimages. It derives:

- registry allocation, 52-byte records and moved 39-by-44-byte RaceTest tail;
- widened constructor/destructor/unwind operands;
- O(1), bounds-checked class/slot/physical mappings and native publisher bounds;
- display, unlock, Results and audio routes preserving parent fallback;
- per-mode AI pools retaining both human exclusions and original special rules;
- native frontend widgets and independently appended CarSheet/SIDE frames;
- new model damage coverage, optional ride datum and existing wheel selectors;
- immutable MRVC descriptor and disjoint mutable pages.

Existing IDs0–32, families, class membership and accepted relative menu order
remain unchanged. New entries can be ordered within their class by the profile.
New classes are rejected. Allocation is calculated and rounded before the first
registry construction. Live resizing of owned native strings is intentionally
unsupported; changing a manifest means rebuilding and restarting, not opening
another slot manually. The 8MiB default is a configurable tool budget, not an
engine-wide maximum.

The frontend uses existing native Egg widgets, navigation and Broker positions.
Artwork banks retain all prior frame bytes. Their parser bounds count by input
length instead of an SDK-only128 limit, and counted texture names now handle
four-digit indices correctly. This format test alone does not qualify the native
bank loader for thousands of frames. V-TEX2's artwork/project_frame pipeline is
reused; Texture Studio, UVs, model variants and livery authoring were not changed.
`artwork-bindings.json` separates physical IDs, family, model variant and bank
roles/frames. `authored-project-preserved` provenance does not assert that an
image is a historical original.

## Runtime boundaries and ABI

| Contract | Integration |
|---|---|
| Native registry | getter `0045A3C0`, singleton `006F5ED4`; 52-byte records |
| MRVC v1 |44-byte immutable descriptor from `vehicle_registry_abi.hpp` |
| Child discovery | `MR_VEHICLE_REGISTRY_DESCRIPTOR=0x...`, child environment only |
| Extra Options marker | optional `MRExtraVehicleRegistryAbi=0x4D525601` |
| Existing Renderer API | unchanged optional `MRExtraOptionsAbi=0x45583201` |
| Existing G1 provider | `MRRegisterSdkRosterV1`, dynamically checked/copied rows |
| Persistence identity | `mr-roster-identity/1`; model/texture SHA is not identity |

The launcher verifies that the singleton is still null, installs the complete
payload, checks the descriptor and preserves RX versus RW/NX pages before
resuming. It rejects old SDK33 input binding when a capacity package is present.
The matching Extra Options build verifies the installed composite; it does not
reinstall SDK33 over it. Challenge replay displacements derive from the actual
RaceTest layout. MODEL/GENERAL menus, five difficulties, Ghost and tire paths
retain their accepted source implementation.

Extra Options work is isolated at `../master-rallye-re-v-cap2-extra-options`,
branch `integration/v-cap2-extra-options`, source commits `c22231a`, `ba6ba87`,
documentation commit `934a034`. Its baseline manifest records the accepted dirty
source adoption. Per-car MODEL/tires/family state is allocated from verified
capacity; the former256 array and64-provider-row bounds are removed. Standalone
retail/SDK operation derives the native count from the allocation operand.
Neither DLL requires the other. The accepted Atmosphere/Extra Options Renderer
binary is reused unchanged with its existing assets and configuration.

## Saves, reservations and network

Retired IDs cannot silently reactivate. Explicit `mr-roster-reactivation/1`
migration requires an exact previous catalog digest, exact IDs and a reason.
It cannot rebind an ID to another family or class. This digest covers identity,
not repaintable resources. The current builder still requires complete authored
records: it does not automatically hide/remove retired widgets or synthesize a
replacement vehicle for a missing record.

Every integrated capacity launch checks the private
`resource-root/DataGame/PlayerState.xml`. Unknown/retired IDs, invalid class pairs,
malformed/duplicate fields and unsupported identity keys stop launch with a
diagnostic; the save is never rewritten. Normal campaigns with the same valid
catalog can restart. Importing an active competition while changing the catalog
remains blocked by the Python build preflight. This is not a claim that every
championship lifecycle has been gameplay-tested. The native parser deliberately
accepts the stock bounded UTF-8 Game/Broker/Value subset, not arbitrary XML
extensions. `--verify-roster-state` provides a read-only check.

The network protocol remains unchanged. Full-width checks at packet writer
`00434450` and sender `00433DC0` prevent ID255+ or other invalid negatives from
being narrowed or transmitted. The inactive−1 sentinel and IDs0–254 retain their
original encoding. Zero-length packets are not sent. A native diagnostic is
logged once per changed rejected selection. This is a transmission guard;
host-start UI and complete network lifecycle remain owner-unqualified. Wider
protocol/catalog negotiation is deferred without constraining offline registry
arithmetic.

## Actual capacity and evidence

| Evidence | Result |
|---|---|
| Prepared owner candidate |34 physical records, classes8/13/13 |
| Addition |ID33 `Evo2FourRunner`, existing independent SDK project |
| Identity |IDs0–32 and accepted class ordering retained |
| Additional model |own car/complete/wheel resources, physics, CarSheet/SIDE; different model bytes from all parent car.dx files |
| Native arena |524288 allocated bytes;389120 emitted bytes |
| Native transaction |266 operations; no disk-patched game EXE |
| Final core CPU replay |68 forward/reverse queries,3 lifecycle routes, one additional initializer, one parent call, invalid bounds rejected |
| Focused Python/native tests |98 tests run,97 passed, one existing optional fixture skip |
| Four suspended hosts |SDK/input/Renderer/both PASS,3.98–4.69 seconds each; game thread never resumed |
| Source-declared hook audit |25 Renderer/customization spans, original bytes verified; one accepted shared attract redirect; zero unexpected overlaps |

Separate emitted-code tests cover ID127/128,254/255,256 and512; native Extra
Options callbacks cover counts through513 and a487-row provider. Scene generation
tests exercise43 native widgets in one class; bank tests cross128/256 and1000.
These are subsystem tests, **not proof of127/256/512 independently playable cars**.
The earlier4096-record research experiment remains offline evidence only.

A full initial build measured81.66s:12.17s composition,8.16s copying8027 resources,
52.47s legacy verification, plus compilation. The new directory traversal checks
the same8027 files and content hashes in5.07s, retaining reparse-point rejection
and mutable-state rules. Unchanged input digests are reused only after source
verification; the copied output is independently hashed. Repeated verification
before compiling the same fresh package was removed. These timings describe
local packaging/verification, not gameplay frame rate or load time.

## Reproduce and use

Local private output is `.research-output/vehicles/v-cap2/candidate34-final`.
Its `registry-build.json` records the exact prepared project inputs. The author
project's source remains in its existing worktree; the builder does not modify it.

```powershell
python tools/vehicle_sdk.py registry-build --manifest path/to/registry-build.json --output .research-output/vehicles/v-cap2/new-candidate
# From the isolated Extra Options source worktree:
python tools/build_extra_capacity_candidate.py --output .research-output/extra-set1/new-pair --sdk-runtime path/to/new-candidate/runtime --sdk-root path/to/master-rallye-re-v-cap
# Back in this Vehicle SDK worktree:
python tools/package_vehicle_registry_candidate.py --candidate .research-output/vehicles/v-cap2/new-candidate --extra path/to/new-pair --renderer-host path/to/accepted-private-renderer-host
```

`Launch-sdk.cmd`, `Launch-input.cmd`, `Launch-renderer.cmd` and `Launch-both.cmd`
use private copied executables and one private resource/save root. They do not
install or update either real installation. They share the private save; use
fresh competitions for cross-mode comparison. Do not combine an old binding DLL
with a regenerated capacity package. Rebuild its matching pair.

Owner checks, limited to the new integration:

1. Start SDK alone. Navigate every class to its last slot and back; selectID33,
   confirm its name and icons, then select an accepted old car and return.
2. Quick Race:ID33 player, thenID33 AI with an accepted player. Check actual
   4Runner model/physics/wheels/collision, damage/glass/lights, finish and Results.
3. Start disposable new Rallye Cup and Master Rallye competitions. Save/restart
   and confirm selected/AI identities. Invitation keeps its T3 rules; do not
   force this T2 car into authored Challenge/Invitation-only slots.
4. Input-only: short menu check of five difficulties, Ghost, MODEL PS2/PC on a
   supported stock car, GENERAL tires; check per-car selection after restart.
5. Renderer-only and both: repeat theID33 selection/race once; check accepted
   lighting/night/headlights and old car appearance. No broad retest of all33
   previously accepted vehicles is requested unless a regression appears.

Current limitations: no user-confirmed gameplay of this exact composite yet;
no new classes; no live registry resize; only existing mirror-stock-ID10 unlock
policy for additions; new projects needing additional engine-audio/shadow/
mechanical native contributors are rejected until explicit parent composition is
implemented. Accepted parent contributors remain intact. This phase does not
claim a final global CarID maximum, wide-ID multiplayer, or full V-CAP2 gameplay
completion. See the private source/build manifest, SHA256, conflict report and
validation logs for exact evidence.
