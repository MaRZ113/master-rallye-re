# V-SDK1 native composition audit

2026-10-24 · `research/vehicles` · source/build audit plus isolated CPU replay.

## Findings and composition requirements

The established 29/30 configurations are user-qualified through race loading,
AI, Results and re-entry. Their metadata still carries older provisional flags;
this does not itself invalidate that user evidence. The new combined build has
a separate qualification boundary and must be tested again.

1. Completed candidates cannot be concatenated. SCALE30 private capacity code
   and Lancer damage/audio both independently claim `0x10000000`. Build one
   reference image and one sealed allocation, emitting each hook owner once.
2. Existing `prepare_vehicle_damage_runtime.compile_context` is ID27-only: it
   reads `collection-inputs.json.id27_resource_source` and rejects any existing
   `native_extension`. A collection composer must gather all addons' reports.
3. Use the qualified J.2 parent, then generate the capacity extension in a free
   admitted cave or as a relocatable segment in the one shared private payload.
   Generate shared damage dispatch and each optional appender only once, with
   every selected profile supplied in the same call. Preserve exact original
   preimage checks; do not permit an appender to overwrite another unknown hook.
4. The supplemental audio state is naturally owner scoped (64 owner slots,
   three independent SFX allocations each), but its old construct/destructor
   cleared the entire publication map. Multi-owner interleaving needs a repair
   and regression: another owner's create/destroy must not invalidate live
   associations. V-SDK1 now records the publication key in each44-byte owner
   slot and invalidates only that owner's key while others remain alive.
   Last-owner destruction clears all residual publications for race re-entry.
5. Preserve the SCALE1 crash fix: capacity audio lookup calls its qualified
   parent only once, then translates added IDs. Never call native CarID getter
   twice with the volatile `ECX` destroyed by the first call.

## Hook ownership

| Feature | Exact retail site | Owner / condition |
| --- | --- | --- |
| Registry constructor | `00458D3F` | Capacity wrapper chains J.2 parent |
| Class forward / reverse | `00481E20` / `00481E50` | Capacity wrapper chains parent |
| Registry allocation | `0045A3E0` | Existing registry layout calculation |
| Audio profile route | `00408FB4` | Capacity route, single native getter |
| T2 AI append loops | `004581B4`, `0045AD53`, `00451F18` | Quick Race / Cup / Master |
| Damage | `0056BD1D` -> `005892E0` | One shared dispatch, native call once |
| Ride reference | `0044F33E` -> `004938C0` | Family scoped, one appender |
| Engine names | `004090C8`…`00409904` case-specific table | Group by donor call site, physical CarID guard |
| Supplemental construct | `00409CAD` | Owner-scoped voices |
| Actor publication | `00492CCA` | Shared exact publication association |
| Supplemental update | `0040A026` | Physical CarID profile selection |
| Supplemental destroy | `00409E25` | Owner-only cleanup |
| Shadow | `0058848A` -> `004F5BC0` | Resource name + all44 native bounds bytes |
| Mechanics | `0043F22C` -> `0043ED00` | Source wheel resource family, native registration once |

These sites are disjoint across capacity/damage/physics/audio/shadow/mechanics.
Engine-name and supplemental audio are separate hooks. Runtime resource names,
namespace and CarID still must be unique. All appenders reject changed preimages.

## Bounded storage / launcher constraints

The former Lancer extension uses86754bytes in128KiB, with one4KiB RW/NX page
at offset81920. The frozen Subaru+Lancer damage identities alone use176128bytes:
Subaru4777vertices/960coverage; Lancer3587vertices/1168coverage. Therefore a
combined build cannot retain the old128KiB budget. V-SDK1 admits a separately
reviewed256KiB profile, with an exact sealed blob length/hash and one aligned
RW/NX data page; all other bytes remain RX. This is a storage budget increase,
not a new engine vehicle-count claim. Original EXE and graphics DLL stay intact.

Other SDK bounds: damage<=16models/256KiB; physics<=16families;
engine/audio<=16CarID+namespace profiles; shadows<=16models;
mechanics<=8families; map/voices<=64owners; RVP<=512operations.
T1/T2 class appends are currently constrained to12positions, T3 already has12.
The signed immediate record-count guard is<128, not demonstrated engine capacity.

## Saved identity reservations

Existing SCALE29 owns28 as `scale-t2-probe`. SCALE30 owns28/29 as
`capacity-probe-0` / `capacity-probe-1`. Thus importing those reservation files
and assigning Lancer28/third29 must fail. `reserve_roster(previous=...)` preserves
tombstones and rejects reassignment; do not weaken it. A new isolated roster
may explicitly establish Lancer28/third29 from the frozen26/27 baseline, with
new disposable state. Do not reuse probe-candidate saves or silently migrate IDs.
Subaru remains27/T2-local7; Lancer28/T2-local8; a third29/T2-local9 is the
qualified30-record layout. Actual imported resources still need gameplay tests.

## Shared damage implementation and evidence

`vehicle_damage_native.payload_models` / `extend_models` preserve the historic
singleton emitter exactly. Multi-model code invokes native deformation once,
then compares source XYZ and UV arrays and vector sizes for each unique model.
Only the first matching model's coverage alpha is restored. Native RGB damage,
position deformation, opaque reflection fading and return/ABI are preserved.
Unknown XYZ/UV, unsuccessful native calls and invalid lengths pass through.
Duplicate binary models and ambiguous identical XYZ/UV identities are rejected.

`vehicle_damage_multi_validate.py` replays each source, changed XYZ, changed UV
and unsuccessful native result, verifying one deformation call, callee-saved
registers, stack cleanup and alpha ownership. Its synthetic native service does
not prove the original damage arithmetic. A separate run through the existing
original-instruction deformer replay compares Subaru/Lancer against native
controls, including repeated impacts and unknown UV pass-through.

Both original-deformer controls passed36impacts/model: identical native XYZ,
RGB and returns, exact coverage ownership and unknown UV pass-through. The
multi-model dispatcher passed16synthetic service cases including short vector
lengths and native failure. Five asset-free unit tests passed.

## Multi-owner audio regression

`validate_vehicle_audio_multi.py` passed with full profiles onCarID28/29 and
separate namespaces. It executes original SFX constructors, manager intrusive
registration and destructors, with generated engine/layer routing. It checks:
interleaved construct/publication, two accumulated spool states, BOV event
isolation, stockCarID7 pass-through, independent engine resource interning,
one-owner destruction while the other continues, muted reconstruction before
fresh publication, last-owner cleanup and address reuse on race re-entry.
The shared map remains valid when another owner is created or destroyed.
Broker/interner/clock/allocator/free use typed mocks; Windows SEH setup is
excluded. No actual DirectSound device or live audible mix is claimed.

Private evidence remains under `.research-output/vehicles/vsdk1/native-audit/`;
no source DX arrays, GT resources or proprietary samples belong in source handoff.
