# V-CAP persistence, participant and class consumers

## Evidence scope

Read-only analysis on 9 November 2026. Target: original retail x86 PE32
`corpora/retail/MRallye.exe`, 3,121,214 bytes, SHA-256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
No active REA target was changed; no game was started or installed. Original
instruction bytes were mapped through PE sections and decoded independently with
Capstone 5.0.7. Ignored reproducible raw work is under
`scratch/v-cap-persistence/`: `persistence_probe.py`, `verified-assembly.txt`,
`strings.json`, `stock-schema.json`. String pointer searches are candidate xrefs;
only instruction-aligned disassembly is treated as an instruction observation.

Prior participant analysis was reused from the sibling general checkout's
`research/r-ai2/native-storage.md`, `participant-pipeline.md`, and
`research/r-ai2-1/capacity-8-map.md`. Its gameplay qualifications refer to its
specific old test candidates, not to this V-CAP implementation. Registry count,
participant count and driver-profile count are independent domains.

## Established observations

| Classification | Owner / location | Original representation and evidence | Capacity implication |
| --- | --- | --- | --- |
| Stock Native | `004AC660` Race CarID getter | Stack participant ordinal is a dword (`8B442404`); suffix key is object+68 (`8B4E68` at `004AC66E`); generic integer getter `004D6760` returns EAX | CarID transport here is 32-bit; no byte truncation is present in this getter. Does not prove every consumer or file uses 32 bits. |
| Stock Native | `004B0630` RaceData CarID getter | Same scalar Broker access pattern, separate `RaceData/CompetitorN` owner | A registry physical ID is not the participant ordinal. |
| Stock Native | `0047C6C0` result initializer | `0047C6CA: 8B44240C` then `0047C6D5: 894108` copies the third argument into a dword at record+8 | Results CarID is a dword. Record+0 is participant index; +4 is DriverID; +8 is physical CarID. |
| Stock Native | `0047D6D0` results producer | Allocates each result with `0047D74D: 6A1C`; pointers grow in owner+2C/+30/+34 | 0x1C result record size is independent of vehicle-registry size. |
| Stock Native | `004CADF0` replay container allocator | `004CAE33: C1E204`, `004CAE36: 83C204`, `004CAE39:52`: `N*16+4` allocation. N is retained as array cookie; construction uses stride16 | Replay participant storage is count-driven, not a registry-sized array. |
| Stock Native | `004CB9B0` / `004CBB50`, `004CB150` / `004CB410` | Prior native analysis: recording/playback iterate cached participant N; each participant owns dynamic 0x30 frame records | No 32/64/128/256 vehicle cap follows. Replay file identity/header serialization remains unconfirmed. |
| Stock Native | `004333D0` offline Network mirror | `004333DA:8D6E60` begins flags+60; `00433449:83C504` advances dword; `0043344C:83FF08`, `0043344F:7C8C` iterates eight flags | Eight is a separate participant mirror bound. Do not enlarge it merely to register more vehicles. |
| Stock Native | `00480A20` frontend selection state | Current class dword+10; three selected ordinals+14/+18/+1C; class counts+20/+24/+28. `00480A4F:894620`, `00480A52:894624`, `00480A62:C746280B000000` initialize7/7/11 | Fourth-class indexing would enter adjacent state. Changing a class-count literal is insufficient for T4. |
| Stock Native | `00481E50` reverse class mapping | `00481E55:83F807`, `00481E68:83F80E`; three arms set class0/1/2. Class is stored as dword at+10 | Three native class policies are not a 2-bit serialized limit; a new class needs new selection state/mappings and downstream policies. |
| Stock Native | `00452640` championship snapshot | Unrolled Car0..Car5 paths read RaceData CarID and write named `MasterRallye/CarN/CarID` through generic integer setter `004D8000` | Six persisted campaign participants are an independent schema, not a six-vehicle registry limit. |
| Stock Native | `00452F..004539..` championship restore region | `00453008:6800376B00` selects Car0 key; `00453022:E839370800` calls integer getter `004D6760`; value is pushed in EAX. Equivalent Car1..5 string xrefs listed below | Restore uses numeric physical identity, so remapping old IDs can silently load a different car. |
| Current SDK | `addon_sdk/player_state.py`, `tools/build_sdk_roster.py` | Copies unchanged local PlayerState into disposable resource root; J3 policy forbids active-campaign remapping | Existing copy policy is not a serialization-width qualification. |
| Patchable / Unconfirmed | More registry entries with unchanged participant count | Dynamic participant arrays consume N, not total registered vehicles | Do not increase N with registry capacity. Preserve existing per-mode grids and roster policies. |
| Unconfirmed | Binary replay/network files, every save import path | No end-to-end integer-width and high-ID roundtrip established here | 255,65535 and INT_MAX must not be advertised as proven global maxima. |

Stock unlock policy is named Bool progress flags, not a demonstrated all-cars
bitset of26 or32 bits. Existing `tools/r5v_g1_unlock.py` maps special IDs3..25
to named flags and records an available default switch arm; preserve its
stock-fallback semantics. This does not assign a new progression policy to every
future addon automatically.

## Persistence schema independently read from stock corpus

The following metadata was read from the retail unpacked corpus, not inferred
from the owner's modified PlayerState. Its `SavePlayerState="True"` entries use
XML `Type="Int"` and decimal text, not a byte-sized XML field. The exact native
text-to-integer overflow behavior and every consumer's signedness are still
separate qualifications.

| File | Bytes | SHA-256 | Relevant original fields |
| --- | --- | --- | --- |
| `DataGame/frontend.xml` |2271|`72ccf7b4d4a9eca7702f82a65bcb8508dbb85ec63ffd734b7db4b9f25bc7025d`|QuickRace/Car0,Car1; Network/Car0; RallyeCup/CurrentClass|
| `DataGame/MasterRallye.xml` |6801|`ca8e3330101b0d0e7374de25c6208519f4994e97d417d6199971f746070f3506`|VehicleClass; GameSaved; PlayerT1/T2/T3Car0/1; Car0..5/CarID,CarClass,DriverID, times, positions and Player flags|
| `DataGame/RallyeCup.xml` |690|`b6a433420d09dc2640181936d422654ffdd8c93808ce37820dac0073b65eddd6`|PlayerT1/T2/T3Car0/1|
| `DataGame/Progress.xml` |23022|`404b0a3463f3cf5d659a31902b96018b608c156505ca790189d62711e27d1f51`|Named unlock, mode and completion state|

Original EXE key / code pointer pairs (pointer VAs point at the four-byte
immediate following PUSH68; they are not function starts):

| Saved key | String VA | Snapshot PUSH immediate | Restore PUSH immediate |
| --- | --- | --- | --- |
| MasterRallye/Car0/CarID |006B3700|00452642|00453009|
| MasterRallye/Car1/CarID |006B361C|004527BE|00453184|
| MasterRallye/Car2/CarID |006B3538|0045293A|004532FF|
| MasterRallye/Car3/CarID |006B3454|00452AB6|0045347A|
| MasterRallye/Car4/CarID |006B3370|00452C32|004535F5|
| MasterRallye/Car5/CarID |006B328C|00452DAE|00453770|

For Car0 snapshot, `00452658:E8D3DF0500` calls `004B0630`; `0045265D:50`
passes the full EAX integer; `0045266A:E891590800` calls `004D8000`. Restore
calls `004D6760`, then passes the full EAX to RaceData publication. No 8-bit
narrowing is visible at those boundaries. Inspecting only this boundary does
not prove all campaign transitions support arbitrary high physical IDs.

## Independent participant bounds

The normal Quick Race frontend stock policy offers1..3 opponents (one human
makes up to4). The existing R-AI2 work established different physical owners:

- Physics manager `0043DD40`, vector+18/+1C/+20, enumerated by `0043EF80`.
- Collision registration `0043A800`, vector+0C/+10/+14.
- AI manager `0042A540`, vector+88/+8C/+90, controller0xD4 per AI, destructor
  `0042A6B0` follows actual vector length.
- Finish/progress/reset owners `00489AF0`, `0048A880`, `0048B520`, `0048CFE0`,
  `004CC5F0`, `004CDF00` allocate cached-N arrays.
- Scene/HUD/Results XML author eight actor/marker/icon slots; the offline Network
  mirror has the independently observed eight dword flags. Eight-car previous
  Quick Race runtime evidence is bounded to its candidate/mode. Network packets
  and every alternate finish mode were not qualified by that evidence.
- Some alternate modes at `00449E90`, and FinishingType1 at `00489EC0`, explicitly
  operate on Car0..3. Four wheels per car, four intra-egg AI slots, two human
  viewports and three ahead/self/behind HUD rows are unrelated limits.

Consequently neither four nor eight is the vehicle-registry capacity. This
phase should preserve current participant counts while scaling the registry.

## Scalable ABI and admission implications

1. Keep physical IDs0..32 stable, retain tombstones and never reuse an absent
   reservation for a different family. Class-local/display order must remain
   a separate mapping from physical identity.
2. Add a portable roster-identity sidecar: version, stable roster namespace,
   physical-ID/family mapping and retired reservations. Compare the mapping for
   every saved selected/campaign ID, not only the executable SHA. An unchanged
   mapping with appended IDs does not require rewriting PlayerState.
3. Read-only preflight should enumerate stock selected IDs and saved campaign
   Car0..5 IDs, reject unknown/deleted/rebound mappings before launch and preserve
   the save unchanged. A valid decimal Int alone is insufficient admission.
4. `GameSaved=True` needs the exact old campaign mapping and policy. Do not
   migrate an active campaign implicitly. For experimentation use copied state.
5. Keep signed32-compatible IDs in any new SDK ABI until all original parsers,
   negative sentinels and arithmetic (`52*ID`, offsets, allocation size) are
   separately bounded. This is a conservative ABI design choice, not a proven
   engine maximum. Use checked arithmetic and explicit unsigned sizes.
6. More than three classes requires relocating selection arrays, replacing
   class maps/navigation and class-specific campaign/player-selection keys,
   UI nodes/localization/unlock rules, AI pools and per-mode class switches.
   Extra class metadata can exist in an SDK catalog while native projection
   remains T1/T2/T3; do not silently project a real T4 into T3.
7. Keep roster, class, race participants, UI bank frames and DriverID capacities
   distinct in a capability manifest. Unsupported network/high-ID replay paths
   must remain explicit gates; no blanket safe64/128/256 claim follows here.

## Remaining validation gates

Native integer getter/setter and XML save/reload at selected high IDs (127/128,
255/256) need a bounded offline CPU test, then owner lifecycle validation on an
isolated configuration. Test Quick Race selection, reopen PlayerState, Results,
replay start/seek/end, RallyeCup and MasterRallye save/re-entry with the identical
roster mapping. Verify old SDK33 state before and after an append-only profile.
Network serialization, standalone ghost/replay headers and active championship
migration remain unconfirmed until their own producers/readers are mapped.

## Follow-up: paired multiplayer identity serialization

This closes the earlier broad network-width unknown for the **selected vehicle
advertisement path**, not for every network message. Root REA/Ghidra evidence is
`scratch/network-batch.json` (`ev_1931b7b2e3c436fac3e17b883f1c0e93ec4ad8bc0611eb11952985bc8652dd3d`)
and `scratch/network-wire-batch.json`. Original instructions were independently
read from the pristine corpus by this report's probe.

The complete identity chain is:

1. `004819B0` frontend publication invokes dense class-to-physical mapping
   `00481E20` at `00481C68` (`E8B3010000`). It pushes full EAX at `00481C6D`
   (`50`), calls singleton getter `004ADA50` without consuming that argument,
   and setter `004AD840` at `00481C75` (`E8C6BB0200`). Therefore this is the
   physical vehicle ID, not the participant ordinal or class-local selection.
2. `004AD840` writes `FrontEnd/Network/selectedCar` using generic Int setter
   `004D8000`; `004AD9C0` reads the same key via Int getter `004D6760`.
3. Packet builder `004343C0` reads that getter at `0043440F` (`E8AC950700`)
   and caches full EAX at owner+30: `00434414:894530`.
4. **Narrowing occurs at the packet boundary:**
   `00434450:8A4530` loads only AL from owner+30, and
   `00434453:884605` stores AL at outgoing packet+5.
5. Sender `00433DC0` forwards the resulting packet buffer/length to the network
   backend virtual call at `00433E34:FF12`, with port/channel argument0x56CE.
6. Paired reader `00433EC0` loads the incoming buffer into ESI at `00433F98`.
   `00433F9F:33D2` clears EDX, then `00433FA5:8A5605` loads packet+5 into DL;
   `00433FAE:89542428` retains the resulting **zero-extended** dword. This is
   unsigned8-bit, not signed8-bit. `0043415A:8B4C2428` reloads it and
   `00434161:898804080000` stores the peer record's dword+804.

| Classification | Actual bounded domain | Consequence |
| --- | --- | --- |
| Stock Native | selected physical ID in this multiplayer advertisement is unsigned8-bit0..255 | ID256 aliases ID0 in this path; ID511 aliases255. These follow directly from paired byte write/zero-extension, not from a guessed table size. |
| Patchable | Wider/versioned packet field and paired reader with catalog negotiation | Both peers, packet layout/length and downstream preparation must be upgraded together; changing only local registry allocation cannot fix this. |
| Unconfirmed | Every other network packet, high-ID multiplayer lifecycle, compatibility with mixed clients |0..255 representation is not proof all IDs in that interval work or that a256-entry registry is globally safe. |

This is **a protocol-specific bound**, not the engine's global maximum CarID.
A scalable offline profile can exceed255 while multiplayer remains explicitly
blocked for the incompatible profile. Profiles at or below255 still need matching
physical-ID/family mappings on every peer and ordinary network qualification.
The frontend's initial -1 selected-car sentinel also narrows to255; valid
admission must distinguish inactive setup state from a legitimate selected ID255.
No safe multiplayer support for ID255 is claimed merely from unsigned decoding.

## Follow-up: standalone .ghost identity differs from in-memory race replay

Existing native ghost analysis is in the sibling ghost checkout's
`tools/ghost_file.py` and `research/ghost1/FINDINGS.md`. This format belongs to
SplineManager, not the cached-N in-memory `gaReplayRecorderAI` containers above.
The original writer/parser and playback consumer establish the main identity
as a **vehicle-family string**, rather than an8-bit physical CarID:

- Native file reader `004BBA00` checks magic0xAB59D02E and version3. The12-byte
  outer header is magic:u32,version:u32,payload-size:u32; no CarID field occurs
  in that outer header.
- Record producer `004C0B20` reads String `Race/Car%d/CarType` (literal006E6F18)
  and `Race/RaceName` (006E55F0), then passes them to `004BC590`. The latter
  stores family/race names at record+0/+4, participant ordinal at+8 and supplied
  start-grid position at+C. Physics terms are read from `Vehicles/CarN/...`;
  none of those six float terms is a registry ID.
- Writer `004BCBD0` obtains family text from record+0, determines strlen and
  uses a32-bit length followed by raw family bytes. For the first string length,
  `004BCC90:6A04` supplies4 bytes, `004BCC99:E862700100` calls writer004D3D00;
  the following bytes are written at `004BCCB3:E848700100`. Race text follows
  the same policy. Numeric participant and start-position fields are4-byte
  writes, not a packed CarID byte.
- Parser `004BCEB0` reads that length using
  `004BCF25:6A04`, `004BCF2A:E8816E0100` (reader004D3DB0), then copies exactly
  that many family bytes at `004BCF51:E82A27F5FF`.
- Playback `004BFE00` calls getter004BC8D0 for the stored family, converts it
  through the existing string APIs and formats `Vehicles/%sAlpha/car` using
  literal006E6EE8. Wheel lookup uses `Vehicles/%sAlpha/wheel` (006E6ED0).
  Getter004BC910 reads record+C; playback publishes it as Ghost start position.
  A new family therefore needs compatible Alpha resources for this ghost path;
  enlarging physical registry alone does not supply them.

Three existing owner-local .ghost files were inspected read-only with the
existing decoder. They are generated samples, **not claimed original shipped
assets**: Italy1.bestever.t2 and sessionbest both identify `Kiasportage`, and
Italy3.bestever.t3 identifies `Mattserati`. Their parsed payload ends equal file
sizes18808/18808/15711. Header/sample hashes and opaque numeric words are recorded
under ignored `scratch/v-cap-persistence/ghost-samples.json`. The first two
post-string words are0/4 and0/0 respectively, agreeing with participant0 and
different start positions rather than serving as evidence of physical CarID.

No high-ID game recording/playback was performed. Opaque tail semantics, every
SplineManager mode and saved binary race-replay formats remain unconfirmed.
Family string identity removes a specific guessed8-bit ghost-CarID limitation;
it does not establish unlimited family length, automatic resource resolution or
replay compatibility across changed vehicle assets.

### Reproduction of this follow-up

`tools/verify_vehicle_wire_identity.py` uses only Python's standard library, maps the PE section
table, asserts21 exact original instruction sequences and decodes the small
.ghost headers without writing any assets:

```powershell
py -3.11 tools/verify_vehicle_wire_identity.py --exe "D:/Game/Master Rallye/corpora/retail/MRallye.exe" --ghosts "D:/Game/Master Rallye/Ghosts" --output scratch/v-cap-persistence/wire-identity.json
```

Result: `PASS_ORIGINAL_WIRE_HEADER_EVIDENCE`. This means original-byte/static
paired-field and file-header validation. It is not execution of the game's file
writer, a network session, a live race, or a replay lifecycle acceptance.
