# Capacity matrix for the five-car proof

**Exact five-car target: CLOSED / CONFIRMED_BY_RUNTIME.** Stock Quick Race remains four; the guarded research candidate completed one-human/four-AI lifecycle. Storage categories below remain static descriptions, while the tested five-car result is recorded separately in [runtime closeout](runtime-closeout.md). `DYNAMIC_N` describes
the inspected container/allocation, not an unlimited supported participant count.

| Subsystem | Physical storage / active bound | Five-car assessment |
|---|---|---|
| Frontend | **FRONTEND_POLICY_4**: three opponent choices + one human; setup uses both effective reads | Guarded five-car setup CONFIRMED_BY_RUNTIME |
| Participant records | **DYNAMIC_N**: scalar Race path cache; independent AI/physics/result objects | Five-participant pipeline CONFIRMED_BY_RUNTIME; no participant[4] expansion |
| Race/CarN Broker | **DYNAMIC_N**: decimal formatting, scalar key handles | Car0..4 captured state CONFIRMED_BY_RUNTIME; paths alone are not actor proof |
| Vehicle actors | **CAPACITY_8** in chosen stock scene; linked-list ownership; N<NumCars activation | Five real actors CONFIRMED_BY_RUNTIME; higher active counts UNKNOWN |
| Physics | **DYNAMIC_N** vehicle and collision vectors; construction N, update/cleanup vector length | Five independent cars including Car4 collision/damage CONFIRMED_BY_RUNTIME |
| AI | **DYNAMIC_N** 0xD4 objects and manager vector | Four AI driving/progress CONFIRMED_BY_RUNTIME |
| Offline Network mirror | **CAPACITY_8** paths/inline flags; finish keys also allocated per N | Car0..4 captured offline state CONFIRMED_BY_RUNTIME; no packet support claim |
| Start grid | **DYNAMIC_N** row/column generation from existing StartArea | Index4 spawned successfully; five-car grid CONFIRMED_BY_RUNTIME |
| Progress/timing/reset | **DYNAMIC_N** byte/dword arrays and transient N*8 rank pairs | Five progress/timing/ranking/finish CONFIRMED_BY_RUNTIME; other finish modes excluded |
| HUD | **CAPACITY_8** progress markers; dynamic comparison inputs / three visible comparison rows | Five-participant HUD and 5TH display CONFIRMED_BY_RUNTIME |
| Results | Dynamic result objects/lists; **CAPACITY_8** authored icons/browser rows | Five logical and visibly rendered rows CONFIRMED_BY_RUNTIME |
| Camera/Replay | **DYNAMIC_N** cached enumeration / N*0x10 replay headers and per-car frames; one human viewport | Tested five-car Replay lifecycle CONFIRMED_BY_RUNTIME; other camera paths unproven |
| Cleanup | **DYNAMIC_N** list/vector traversal and pointer-block release | Stable five-car frontend return CONFIRMED_BY_RUNTIME; full heap reclamation unproven |

Addresses, owners, count sources, storage descriptions and evidence labels are
canonical in [capacity-map.json](capacity-map.json). The full lifecycle and
native offsets are in [pipeline](participant-pipeline.md) and
[native storage](native-storage.md).

The old Results clue is now explained: `47C840` publishes the sorted vehicle's
**registry image integer** at each occupied `Frontend/RaceResults/CarN`; it
fills N..7 with blank image12. These values are neither absolute vehicle IDs nor
proof of active Car4..7. Position/Name/Time lists follow actual result count.
The XML establishes eight authored icon positions and browser Height8, beyond
the earlier path-only clue; eight active engine participants remain unproven.

No structural CAPACITY_4 allocation requiring relocation was identified in the
selected ordinary offline Race path. This conclusion is bounded by this map and
proof configuration. Gameplay, collision, damage, finish, presentation, Replay and stable exit passed the human five-car gate. All thirteen mapped subsystems now have exact-N5 runtime evidence; Network evidence is limited to offline captured mirrors, and no multiplayer support is claimed.
