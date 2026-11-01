# V-DEF3 — configurable roster order and 33-record trial

**Subsequent owner review:** custom ordering was tested and accepted in-game without reported bugs. This original offline-delivery snapshot is retained as history. V-DEF4 replaces only the technical probe with TOMCAT and requires a new owner vehicle test; see V_DEF4_TOMCAT_RESULTS.md.

## Result and boundary

The common SDK/Workshop builder now produces an isolated **33-record, 8/12/13**
CMD candidate. Physical IDs0–31 and their resource identities remain unchanged.
The owner has accepted V-DEF1 Forester and V-DEF2.1 RAV4 with the independent
retail Newrav physics. Their accepted builds remain read-only references.

The new candidate is **PASS OFFLINE / OWNER D3D8 PENDING**. No game was launched
by this work. ID32 is explicitly **SDK PROBE T3 SLOT32**, an independent copy of
retail Wildcat geometry/resources/physics, not a restored Demo vehicle. It tests
selection, namespace and record capacity without doing the next restoration.

Private launch:
`.research-output/vehicles/v-def3/delivery/workshop/builds/first/candidate/Launch-SDK-Roster.cmd`

## Actual retail consumers

Original retail executable SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA/Ghidra12.1.4 inspected this immutable PC/x86 original. Private pseudocode,
cross references and evidence envelopes are in `vehicles_scratch/vdef3`.
Decompiler output is supporting static evidence, not original source or gameplay.

| Consumer | Finding and action |
|---|---|
| Forward selection `0x481e20` | Stock dense arithmetic depends on class/local. Existing hooks are extended with a complete explicit map, including stock IDs, when an order is configured. Seven original direct call sites include details/stats and selection acceptance. |
| Reverse selection `0x481e50` | Four direct initialization/re-entry callers restore class/local from a physical ID. Emit the inverse permutation and retain the existing native publication/epilogue at `0x481e89`. |
| Constructor `0x480a20` | Counts are fields+0x20/+0x24/+0x28. The existing G.1 cave independently owns T1/T2; frozen T3 immediate at `0x480a65` is12. Candidate uses8/12/13. |
| Position publisher `0x481950` | Original `83 fe 0c 7c b1` at `0x4819a4` publishes only Button0–11XPos. Signature-checked immediate at+2 changes12→13 in process memory only. The original64-byte formatting buffer accommodates the tested thirteen keys. |
| Navigation `0x481f50` | Native class-count comparison already advances to local12 and stops there for count13; no speculative navigation rewrite. |
| Vehicle details `0x4819b0` | Calls forward mapping for physical model, four stat lookups and presentation. Names/resources/stats remain owned by physical record, not by image position. |
| AI `0x451dd0` / `0x45abc0` | MasterRallye/Cup loops enumerate physical IDs. Original T3 ordinary pool14–20 plus gated special actors is not the entire selectable T3 class. Existing three T2 append hooks are unchanged in meaning; probe32 has every AI flag disabled. |
| Results/audio/unlock | Existing per-physical-ID dispatch is reused; ID32 gets isolated labels and retail profile14. Unlock mirrors the already-qualified ID10 oracle. No new progression bit, shift-by32 or achievement flag is introduced. |
| Championships | `MasterRallye/CarN/CarID` stores physical IDs; getter `0x4b0630` reads participant Broker state. Existing IDs and persisted values are not permuted. This does not prove full championship save/load compatibility. |
| Registry/RaceTest | Reuse the existing52-byte vehicle records, constructor/destructor/unwind counts and relocated44-byte RaceTest layout/displacement patches. No new registry implementation. |

The investigation establishes these paths, not universal compatibility with
every executable or unknown third-party hook. This trial uses the existing
validated retail adapter and byte preimages. An unrecognized layout is rejected.

## Configured ordering

| Class | Physical ID order |
|---|---|
| T1 | 0,1,2,3,4,5,6,26 |
| T2 | 7,8,**30**,9,10,11,12,**31**,13,27,28,29 |
| T3 | 14,**32**,15,16,17,18,19,20,21,22,23,24,25 |

Thus WOOLDAND8 is followed immediately by Demo Forester30; Newrav12 is followed
by Demo RAV4 31. Retail Wildcat14 is followed by the technical capacity probe32.
The original resource key Newrav is used here; this does not rename its retail
localized display identity. Existing T1/T2/T3 member classes are not changed.

`selection_order` must be a complete class-preserving permutation: no duplicate,
missing, Boolean or foreign-class IDs. Reservations and addon `class_local_index`
retain canonical append ownership; `selection_layout` and `class_mapping` record
effective menu positions separately. Previous reservation locks cannot be stolen
by reordering or class reassignment.

Per-project `vehicle_class` provides explicit runtime class assignment. New
non-T2 AI is rejected unless disabled, because those pool insertions are not yet
qualified. The ordinary author compiler still uses its established technical
author slot, then the common runtime builder rebinds it. No T3-only compiler or
false global capability approval was added.

Workshop's **Configure → Configure vehicle order and classes** edits this same
declaration into a fresh project-owned configuration. Accepted input configs are
never overwritten. `null` order restores canonical append behavior for older
profiles. A33-record trial requires an explicit complete order.

## Widget and storage findings

The frozen base's loose `VehicleSelect.xml` lacks `T3_Car12`, although its pinned
parent `Data.sma` contains the historical hidden-ID25 widget. A new configured
layout restores that exact archived widget, including frame5 and existing
visibility state, before applying the permutation. Existing widget artwork,
unlock rules and presentation values remain attached to the original physical
car. No new authentic Trooper artwork or unlock success is claimed.

New addon widgets clone the audited ID10-mirroring T2 template, updating class Y,
local X and assigned art frame. Cloning a bonus/hidden template would give the
new car an unrelated visual unlock gate; the shared code avoids this defect.
All13 T3 widgets and Button0–12XPos bindings are present in the delivered scene.

The five models' exact XYZ/UV damage-ownership tables exceed the earlier256-KiB
combined storage budget. Only the explicit33-record profile admits a bounded
**512-KiB** private allocation at the established address. Actual payload is
296624bytes, with one4096-byte RW/NX data page at offset286720; code is RX.
Existing29–32 profiles retain their256-KiB gate. No identity checks or original
damage tables are removed to save space. Occupied-address rejection and actual
remote allocation self-test pass, with `game_launched=false`.

## Authentic early WildCat identity

Original shipped Demo8.4.1 EXE SHA256:
`2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a`.
The existing bounded registration parser was rerun against original instructions:
record/index15 owns family`Wildcat`. Original localization category52/index15 is
**TOMCAT**, and category53/index15 is **PRIVATEER TOMCAT**.

Both localized values are PROVEN, with exact table offsets/pointers in
`V_DEF3_PROVENANCE.json`. Original registration numeric class1 is retained as
evidence; it is not silently equated with the new retail T3 assignment. The
current user-replaced/rebaked WildCat folder is not used to authenticate8.4.1
geometry. No early model, artwork, driver or physics restoration occurs here.

## Validation

| Check | Result |
|---|---|
| Emitted forward/reverse native mapping | All33 IDs, effective class/local and stack ABI PASS |
| New records | Five exact initializer destinations/RGBA,55 display literal checks, Results/unlock dispatch PASS |
| Audio |99 physical-ID/participant tests, original getter called once with volatile-register clobbering mocks PASS |
| AI | Three existing T2 pools preserve baseline/new eligible physical IDs;32 absent PASS |
| Actual publisher/navigation |13 keys,33 count-driven right-navigation/boundary cases, native8/12/13 bytes PASS |
| Existing widget ownership | All32 physical widgets match their old loose or pinned archived ownership, except intended local/name/XPos changes PASS |
| Previous resources |376 nonshared loose resources exact; prior physics values and UI-bank records unchanged PASS |
| Protected inputs |1085 original/accepted-build pins unchanged PASS |
| Determinism | Two actual Workshop builds:416 resource files,293 DX/DXT and native extension/RVP byte-identical PASS |
| Launcher | Resource verification, environment/proxy handling and native allocation all exit0 |
| Focused |45 tests PASS; seven new synthetic roster cases |
| Full Windows |1336 tests,0 failures/errors,2 existing optional private-fixture skips;99.980s PASS |
| Final narrow API correction | Canonical/null-order restore and input checks covered by final45-test focused run after full-suite checkpoint |
| D3D8 | NOT TESTED for this candidate; no selection/race/Results/save/Randomizer success inferred |

Exact private reports: `.research-output/vehicles/v-def3/{qualified-delivery.json,
determinism.json,full-windows.json,focused-final.json}`. Source-only provenance
summarizes results without copying models, textures, executable or Ghidra payloads.

## Save and compatibility limits

Configured-order trial packaging refuses an active `GameSaved` championship
before writing the candidate; it does not erase or migrate it. Current owner
PlayerState has `MasterRallye/GameSaved=False`; its167309bytes are copied unchanged
to disposable candidate state. Physical participant IDs are stable, but campaign
load/re-entry/progression still need owner tests. Trial saves must not be copied
back to retail or accepted builds, especially saves containing probeID32.

Original EXE, clean retail Data.sma, installed D3D8 Proxy, Randomizer, existing
accepted projects and source geometry remain unchanged. Existing launcher proxy
SHA rejection remains disabled as requested; handle pinning/link checks remain.
No competing DLL, new mod installation or additional J.2/F3 patch is introduced.
Live Randomizer coexistence and unknown hook conflicts remain owner-test gates.

## Owner checklist and rollback

1. Use the private CMD above. Do not copy its resources over the game installation.
2. In T2 confirm both adjacency pairs, their correct icons, large previews and
   identities. Select Forester/RAV4 and verify accepted wheels/glass/lamps/handling.
3. In T3 confirm **SDK PROBE T3 SLOT32** beside retail Wildcat. It intentionally
   looks like retail Wildcat. Navigate the entire row; verify final positions,
   locked special-vehicle behavior and class changes without wrapping/cross-talk.
4. Enter a fresh Quick Race with the probe, steer/brake, finish, inspect Results,
   return to menu and re-enter. Check no ID32 replacement of another car.
5. In separate fresh competitions exercise AI with T2 Forester/RAV4 and T3
   stock cars. Probe32 must not be chosen as AI. Challenge/Invitation are unchanged.
6. On disposable candidate state, save/relaunch/re-enter a new championship and
   verify participant IDs, class/order and progress. Do not import an old active
   championship or promote this state to the accepted build.
7. With the owner's existing Randomizer configuration, check normal initialization
   and a fresh race; report logs/screenshots for any conflict. Offline preflight
   alone is not this test.

Rollback: close the game and launch either accepted Forester/RAV4 CMD. No installed
file or original save needs restoring. Stop here for owner review. Full Demo
TOMCAT restoration and any new AI/capacity extension remain separate milestones.
