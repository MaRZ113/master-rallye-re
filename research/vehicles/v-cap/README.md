# V-CAP: native capacity, configurable core and remaining adapters

Status: **OFFLINE_NATIVE_CORE_ONLY**. Configurable native storage/mapping is
implemented and CPU-tested over the accepted SDK33 parent. An arbitrary-N
playable roster, migration of active championships and multiplayer extension
are **not** qualified or supplied by this experiment. No game, installer or
working DLL was launched or modified.

## Answer: several independent limits

There is no established single global vehicle limit or proven maximum CarID.
The original registry, class selection, UI positions, localization, AI candidate
pools, participant containers, campaign snapshots and network protocol have
different owners. A wider field in one owner does not establish every path's
capacity. In particular, **the original network selectedCar packet is one byte**.
ID256 aliases0 there. This does not limit the offline registry to256 records.
ID255 also needs sentinel-policy review because an inactive -1 narrows to255.

Original inspected EXE: PE32/x86, 3,121,214 bytes,
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Native evidence was rechecked with REA/Ghidra12.1.4 and mapped original bytes;
independent Capstone checks cover persistence/network/ghost owners. Decompiled
text is recovered analysis, not original source or execution evidence.

## Established storage and bounds

| Category | Owner / original address | Observed value / representation | Consequence |
|---|---|---|---|
| Stock Native | Singleton `45A3C0`, global `6F5ED4`, allocation immediate `45A3E0` | Heap allocation `0xC00`; header4 | Not a fixed global buffer. Only three direct singleton-global references were observed; this does not exhaust pointer aliases. |
| Stock Native | Constructor `458CD0`, destructor `458E00`, unwind `686790` | 26 records x52; counts at `458CF4/458E46/686796` | 25 named records0..24; record25 was only default-constructed in pristine retail. The accepted SDK33 explicitly initializes its Trooper. |
| Stock Native | Full initializer `45A0B0`, record destructor `458D60` | CarID and class are dwords; stats4 x dword; owned name and colour | Never memcpy an owned record to add a car. Use the existing full initializer/string ownership ABI. |
| Stock Native | Adjacent RaceTest array | Base `54C`, 39 x44, end `C00` | This is a separate race-preset table, not39 more vehicle slots. |
| Patchable | RaceTest lifetime displacements `458D12/458E2C/6867B3`, 39 initialization LEAs, 11 indexed consumers | Every tail reference must move with registry size | All known50 initializer/consumer references plus lifetime bases are emitted together, with exact preimages. Addresses and bytes are in `native-sites.json`. |
| Stock Native | Vehicle Select constructor `480A20` | Three ordinals at+14/+18/+1C; three counts7/7/11 at+20/+24/+28 | Fourth-class indexing collides with adjacent fields. More classes is a separate state/layout project. |
| Stock Native | Class maps `481E20/481E50` | Dense thresholds7/14; dword class/local/physical ID | Dense stock mapping is replaced by explicit maps; physical IDs are not menu ordinals. |
| Stock Native | Navigation `481F50` | Reads selected class count as signed32 | Not itself a13/128 total-registry guard. Negative sentinels and arithmetic still matter. |
| Stock Native | Position publisher `481950`, comparison `4819A4` | Publishes12 `Button%dXPos` keys; local key buffer64 bytes | Twelve is a publisher/widget policy, not the total vehicle-array size. Core emits a wide bound; scene widgets must separately exist. |
| Stock Native | AI `458090`, `451DD0`, Cup owners | Explicit per-class physical-ID loops, exclusions, shuffle, driver selection | Increasing registry storage does not enlarge AI eligibility pools. Participant and DriverID domains stay separate. |
| Stock Native | Models/physics `44A510/44A710/44ED50`; setup owners `44C780..44E490` |52-byte indexed records; named family drives model/wheel/physics paths | Core keeps stride and record offsets. Collision/mechanical/damage resources still need family qualification. |
| Stock Native | Results `47C6C0/47C840` | Physical CarID dword at result+8; result stride28, dynamically owned pointers | Result index and DriverID are not CarID; names/icons have independent selectors. |
| Stock Native | Localization groups33/34/35, Results39 | Stock physical selectors reach independently owned text tables | Existing addon literal/driver bridges must cover new IDs; more registry memory alone is insufficient. No global maximum is inferred from a text table. |
| Stock Native | Network writer `434453`, reader `433FA5/434161` | selected physical ID -> packet+5 byte -> unsigned dword | Representable wire values0..255, not a qualified global maximum. Upgrade both peers or prohibit the unsupported path. |
| Stock Native | Network mirror `4333D0` | Eight participant flags | Independent of registered vehicle count; do not enlarge with the registry. |
| Stock Native | Championship snapshot `452640` and restore region | Six explicit Car0..5 records, Int CarID and CarClass | Separate campaign schema. Do not migrate active championships implicitly. |
| Stock Native | Replay allocator `4CADF0` | N*16+4 cookie allocation; dynamic per-participant frame vectors | N is participant count. This does not prove high-ID binary replay compatibility. |
| Stock Native | Standalone ghost writer/parser `4BCBD0/4BCEB0` |u32 length + family string; Alpha resource paths | This is distinct from race replay. Numeric physical-ID byte limits do not follow from the ghost family field. |
| Current SDK | Accepted SDK33 |33 records, classes8/12/13, stable IDs0..32 | Preserved as the parent and as the relative prefix of every class map. |
| Current SDK | `sdk_capacity_native.extend_image`, roster layout/builder |13 widgets/class; experimental count whitelist31/32/33; old signed-imm8 emission | Tool qualification/encoding policies, not proven EXE limits. Legacy API remains unchanged. |
| Current SDK | Private helper arena |512 KiB for accepted SDK33; actual parent payload288720 bytes | Not registry heap capacity: the33-record registry itself is3436 bytes. |
| Current SDK | UI bank parser / old initializer |128-frame parser guard; signed-imm8 initializer values | Separate SDK restrictions. A32-bit DXB count does not by itself prove the native loader is unlimited. |
| Current SDK | Native feature contributors |Damage/audio/physics profile guards16; wheel profile guard8; launcher operation guard512 | Per-emitter budgets/qualification. They must become data-sized before broad deployment; they are not native roster maxima. |
| Current SDK / optional mod | Extra Options source |2 players x256 per-car paint/tire entries;8 participant entries; family buffer32 | Mod-specific, not the EXE's global limit. IDs256+ and long family names need its own compatible adapter. |
| Unconfirmed | Full indirect pointer coverage, all binary race-replay paths, new banks and complete high-ID lifecycle | No exhaustive proof | No statement that63/127/255/4095 is a safe global maximum. |

Record offsets above are **record-relative**: vtable+0, CarID+4, class+8,
stats+C..18, SmallCarSheet+1C, owned name+20, RGBA+24..30. The registry header
adds4, so a global indexed name read uses registry+24+52*ID. This distinction
prevents interpreting the name pointer as colour or treating record0 as the header.

## Evidence map and coverage

- `native-sites.json`:69 checked original instruction/operand sites, complete
  known RaceTest relocation list, PE file offsets and source identity.
- `registry-consumers.json`:34 current Ghidra direct getter callers with body
  ranges. Model/tuning/AI/frontend/Results and common lifecycle callers are
  separated; roles are analyst classifications, not recovered symbol names.
- `persistence-consumers.md`: save keys, exact producer/reader bytes, stock XML
  hashes, network packet chain and distinction between race replay and ghost.
- `wire-identity-evidence.json`:21 paired-field/ghost instruction checks and
  three existing local ghost header samples. Samples are not shipped originals.
- `mod-source-provenance.json`: hashes of read-only current Extra Options and
  Renderer bridge sources. This does not identify the installed DLL binaries.

REA allocator evidence:
`ev_2711dabefe1784a932e1bc605776157700563386b0441366643c9140655ed702`;
core batch:
`ev_99248ee32e7ff10f729f91e8b4b1c69463e09b1b38982a9f40420c7ae18834e1`;
singleton references:
`ev_0320848d57af5ee422f3ab00cec3db56cdf096c07a446978dba8e380daa86736`.
Raw Ghidra exports share the ignored `scratch` directory. A direct-call map
cannot prove the absence of indirect consumers or cached pointers.

## Implemented configurable architecture

Choose the complete roster once, before process startup; do not successively
patch ID33, then34, then35. `capacity_profile.py` validates an explicit physical
ID map and per-class selection order, calculates layout with checked arithmetic,
and preserves every existing SDK33 ID/class/order. Additional class metadata can
be described, but the original native adapter explicitly rejects more than3.

The native core reuses `_CodeImage`, PE mapping, operation format and the full
record initializer. Its optional `wide_immediates=True` emits32-bit arguments;
the default legacy byte stream is retained. Three lifecycle trampolines widen
the actual PUSH instructions and replay their complete displaced operands.
Allocation, RaceTest tail and all50 known tail references move together.
CarID/class/local maps are immutable arrays with bounds-checked O(1) helpers;
their size is derived from configuration. Existing SDK33 helper bytes and its
initializer chain are preserved. Every new record requires an explicit record
declaration. Diagnostic donor declarations are visibly marked as experiments.

The registry uses one appropriately sized native heap allocation. **No live
reallocation** is attempted: records own strings, and consumers may cache
addresses. This is a configurable startup layout, not a new fixed64/128/256
profile or an unsafe hot-resizable vector. The private code/data arena preserves
the SDK33 prefix and writable range and grows in64-KiB allocation units.
Its historic base0x10000000 remains inherited from SDK33; arbitrary-address
relocation of all older helpers would be a separate ABI change. A future loader
must reserve it before resume and fail on conflicts.
Installation must also prove that singleton `6F5ED4` is still zero. Applying
new counts to an already constructed smaller registry would corrupt its tail
and destructor; hot application is not supported.

`mr-capacity-profile/1` contains `record_count`, explicit `classes`, and an
explicit tool `memory_budget_bytes` (default8 MiB). The budget and signed32
offset checks are conservative engineering ABI checks, **not engine maxima**.
Examples33/64/128/256/512 are checked-in configurations, not admission ceilings.
For other counts use `scenario(count, distribution)` or author an explicit map.

`MRVC` descriptor v1 is44 bytes; its C++ declaration is
`src/master_rallye/addon_sdk/vehicle_registry_abi.hpp`. It contains version,
size, record count/stride, class count, native registry getter address, class
count/table pointers, and reverse class/local pointers. The builder emits it;
no working DLL is changed to publish or consume it. A future runtime query must
validate version/size/ownership before exposing it to optional consumers.

`mr-roster-identity/1` catalogs physical ID, family, class and retired status in
a stable namespace. Names are resource identities; livery/model hashes are not
identity gates. Reservations cannot be deleted/rebound: keep tombstones.
Read-only save preflight checks saved physical IDs, per-class selections and
CarClass consistency. Active championships remain explicitly blocked from
unqualified migration. It never changes save bytes.

## Actual offline experiments

| Record count | Class counts | Registry heap bytes | Shared arena bytes | Core build time |
|---:|---|---:|---:|---:|
|33|8/12/13|3436|524288|0.034s|
|64|16/24/24|5048|524288|0.028s|
|128|32/48/48|8376|524288|0.032s|
|256|64/96/96|15032|524288|0.033s|
|512|128/192/192|28344|524288|0.037s|
|1024|256/384/384|54968|524288|0.050s|
|4096|1024/1536/1536|214712|786432|0.110s|

All were emitted over the real accepted SDK33 parent and exercised with
Unicorn. Every physical ID was checked in both mapping directions; constructor,
destructor/unwind PUSH values, publisher boundary, invalid indices, new-record
destinations/IDs, preserved old-record region, exactly-once parent initialization
and volatile-register/stack cleanup were checked. Allocator, native strings,
record initialization and parent initialization are mocked; no vehicle rendering,
physics, save or network session was executed. Lookup emulation timings are
host/emulator timings, not measurements of game performance.

Automated regression:118 tests,117 passed and1 skipped because the optional old
retail/H.2 asset fixture is not packaged. This includes original SDK/roster/slot
builders, audio reference reproduction, new capacity boundaries and save checks.
The separate seven real-parent CPU scenarios passed. A historical audio-evidence
loader LF/CRLF normalization fix is a separate cherry-picked commit, preserving
actual data verification and existing binary reproduction.

## Use and artifacts

From this worktree, with the established SDK Python environment:

```powershell
$env:PYTHONPATH='src;tools'
python tools/audit_vehicle_capacity.py --source ../MRallye.exe --output scratch/native-sites.json
python tools/build_sdk_capacity_profile.py --source ../MRallye.exe --parent ../master-rallye-re-vehicles/.research-output/vehicles/extra-set2/extra-set2-03/runtime --profile research/vehicles/v-cap/profile-64.json --output .research-output/vehicles/v-cap/example-64 --diagnostic-donors
python tools/validate_capacity_profile.py --source ../MRallye.exe --parent ../master-rallye-re-vehicles/.research-output/vehicles/extra-set2/extra-set2-03/runtime --experiment .research-output/vehicles/v-cap/example-64
```

The validator additionally requires Unicorn; the existing local research Python
tools directory supplies it where necessary. Use a fresh output directory.
For actual authored record metadata, replace `--diagnostic-donors` with
`--records resolved-addon-rows.json`; this does not qualify its assets or runtime
feature routes. Optional `--player-state` and `--saved-roster` run read-only
identity preflight. All portable maps use IDs/families; no absolute resource paths.
Diagnostic catalogs use the separate `master-rallye-vcap-diagnostic` namespace;
their donor IDs do not reserve or rebind IDs in an actual authored roster.

The curated generated output has one `candidate-4096` (private binary, process
operation report, identity sidecar and CPU validation) and `validation` with
scenario/test/provenance summaries. There is no patched EXE, runtime installer
or admitted `runtime-profile.json`. The schema deliberately cannot be installed
by the existing launcher as if all dependent features were qualified.

## Remaining integration by owner, not by next slot

| Source / ABI | Required implementation before arbitrary-N gameplay |
|---|---|
| `build_sdk_roster.py`, `roster_layout.py` | Consume one validated capacity profile instead of experimental count whitelist and13-position qualification; size total allocation from all native contributors; preserve old SDK33 entry point. |
| `roster_scene_layout.py`, scene composition | Emit complete class widgets and physical-owned frames for the configured map, then validate scroll/re-entry and max-position publication. |
| `ui_assets.py`, collection/bank code | Verify the original bank-loader allocation/index width, then replace128 tooling admission with checked count/size policy. Keep native rectangles and per-car frame ownership. |
| `sdk_capacity_configurable.py`, existing display/audio/unlock bridges | Cover every added physical ID with explicit strings, icon selector, unlock oracle and stock audio tuning alias; no accidental stock localization indexing. |
| `sdk_addon_ai.py` | Emit eligibility from complete per-mode class maps with both player exclusions and existing special-vehicle rules; do not increase race grid size. |
| `vehicle_*_native.py` | Replace16/8 profile guards and fixed allocator choices with declared data budgets after each source/ABI check; retain model-specific geometry/UV identities for damage and light/material ownership. |
| launcher builder/native launcher | Add a distinct versioned capacity-core manifest, allocation sizing, descriptor publication, overlap ownership and save preflight. Do not merely bypass33/512 admission or relax patch preimages. |
| Extra Options (`MRExtraOptionsAbi` currently45583201) | Query validated native record count; allocate per-player appearance/tire/family state dynamically; preserve existing INI IDs. Its256 entries are its own limitation. Renderer family/participant ABI can stay independent; absence of input proxy remains supported. |
| Native network writer/reader | Version/handshake a wider physical-ID field and shared catalog, or explicitly prohibit affected IDs in network mode. Both peers and the255 sentinel policy need qualification. |
| Save/race replay/campaign | Preserve identity sidecar and unchanged bytes; finish native high-ID parser/save/reload, recorded race replay, campaign continuation and all indirect consumers. Standalone ghost needs correct family Alpha resources. |
| More than3 classes | Relocate frontend arrays and their users; add class navigation, localization, AI policies and class-specific campaign/player keys. Do not project a real T4 silently into T3 or conflate this with vehicle count. |

Thus storage/configuration and an executable proof are implemented; the remaining
feature adapters are explicitly open, rather than relabeling a storage-only
experiment as a complete game-compatible capacity release.

## Manual qualification checklist

After those adapters are built in an isolated candidate: check all old IDs0..32,
both human players and natural AI, complete/car/wheel resources, physics/collision,
damage, lighting, CarSheet/SIDE, unlocks, tuning, Results and return-to-menu.
Use representative IDs127/128/255/256 without renumbering earlier IDs. Verify
unchanged old saves and a fresh campaign save/re-entry with its exact catalog,
race replay start/seek/end, ghost Alpha resources, and absent/present compatible
Extra Options/Renderer. Test native multiplayer only with a qualified protocol
and matching peers. No item in this checklist is claimed performed here.
