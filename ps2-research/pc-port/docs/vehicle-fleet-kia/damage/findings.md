# Kia damage-source preparation

Actual-capture correction (PID15036): source4/source9 share the same material-vector object and first-entry token. Their different authored source texture strings do not establish distinct compiled material objects. The original clone-copy proof remains valid, but material identity alone does not distinguish these two records. In all three actual captures both retain their distinct exact healthy ordered XYZ hashes. The safe current join uses that unchanged XYZ discriminator whenever UV/material candidates are ambiguous; if those ambiguous position certificates change, fail closed until an additional contract is established. No ordinal is used.

## Actual healthy/damage trio

`trio-15036-audit.json` records exact capture SHA-256s for frames2169/2956/4994 in one process/device/proxy/current owner. Frame2169 uses the original tree; both later frames use the selected native private tree. All26 sources join with exact UV/winding and current material identity, supplemented by unchanged exact XYZ for ambiguous sources4/9. Sources0/12/13/14/20 change positions. The static mapping gives2455 private body vertices with candidate deltas agreeing without any disagreement;43 private vertices move after first damage,101 after further damage, with maximum deltas0.20562965 and0.25593930. The956 authored static crew/interior vertices remain explicitly separate. These captured states support a bounded implementation, not every possible future damage state. Runtime code must retain all gates and reject candidate disagreement or ambiguous changed identity.

This bounded source audit prepares the accepted X-Trail style of native delta transfer for Kia. It does not authorize runtime deformation until healthy and damaged native mirrors are compared. No renderer code, original assets, native memory or builds were changed.

`prepare_correspondence.py` verifies both original PC car.dx and the converted original PS2 CAR asset against the existing pinned fleet profile. It emits an index-only draft and compact source correspondence; neither contains proprietary position/UV/texture bytes.

- Original PS2 CAR references 3,411 distinct private vertices across 22 unconditional meshes.
- The pinned runtime asset stores3,559 vertices, but its22 mesh index ranges reference exactly0..3410. The trailing148 vertices3411..3558 are unused by every submitted mesh. The damage map intentionally covers the3,411 referenced vertices only; do not confuse this domain with the full asset storage count or change source offsets. A runtime preparation check must retain the pinned3,559 asset count and validate actual referenced indices against the map.
- 2,440 vertices have original PC coordinate candidates within 0.00001 source units, the accepted offline serialization tolerance. All original candidate indices are retained. Runtime must compare every candidate's delta and reject disagreement; it must never search nearest positions in live data.
- Fifteen further vertices in PS2 roots 0, 4 and 16 have a small original authored difference (0.0004444–0.0047276). They are NOT mapped by proximity. Two already verified neighboring vertices identify the corresponding original PC triangle and therefore its third index. These independent topology proofs identify 15 mappings. Example: private vertex 34's closest PC vertex is source0/index389, but the actual adjacent original triangle proves source0/index437. The draft uses 437, never 389.
- 956 source vertices in original PS2 UnderDash/root17, Chair/root18 and MHelmet/root19 have no PC correspondence. They retain an explicit static original-PS2 crew/interior policy attached to the live chassis. No deformation is invented for those meshes. These source geometries are genuinely different from the PC occupants/interior.

The mapping therefore has an explicit policy for all 3,411 referenced vertices, with no silently unmapped body vertices. Original source normals remain source normals; this position-delta mechanism does not claim native damaged-normal reconstruction.

## Current native identity blocker

Twenty-four of the 26 native healthy sources have unique `(vertex count, triangle count, ordered UV/native winding SHA)` keys. Sources 4 and 9 share that key: both 19 vertices/29 triangles, but different healthy positions and primary textures `dnissanslave3-tga` versus `dnissanslave7-tga`. Unchanged ordered XYZ can distinguish them. If both deform, UV alone cannot. The runtime must prove the current material identity or original-to-private clone relation; a guessed ordinal or two-way assignment is not acceptable.

Latest PID10052 fleet captures at frames 3336, 3911 and 3913 contain 16 native wheel rows plus private CAR/glow diagnostics. They contain no raw chassis mirrors or damaged private-tree geometry. They cannot establish delta consensus, changed vertex counts or source4/9 disambiguation. The next bounded three-activation capture must retain all current root descriptors and mirrored source XYZ/UV/index bytes with exact owner, selected-list, generation/revision and WORLD metadata. Root indices may be recorded as diagnostic labels, not persistent identities.

## Validation

### Exact clone material discriminator

Bounded REA examination of original mesh vtable `00692364` identifies virtual slot+4 as `00576630`. The original clone allocates a 0x48-byte leaf and directly copies source+38 to clone+38 at instructions `005767A0 MOV EAX,[EBX+38]` and `005767A3 MOV [EBP+38],EAX`. This is the same material-vector object used by the verified emitter. Full assembly/pseudocode and original PE-mapped bytes are retained in `leaf-clone-evidence.json` and `leaf-clone-original-bytes.json`; EXE hash remains exact bf8aef32…96b4.

Retain each fully healthy-certified original leaf's material-vector pointer and verify the current selected private leaf's vector/first-entry identity along with count1. The first entry is an exact32-bit token, not an assumed pointer type. Sources4/9 do not have distinct material discriminators in actual PID15036, so they additionally require exact unchanged healthy orderedXYZ to disambiguate. A shared pointer by itself, a historical absolute address or unchanged root ordinal is insufficient. Any unreadable, replaced or ambiguous changed identity must fail closed. The native clone proof supports material consistency but does not independently solve every source identity.

`test_correspondence.py`: 3/3 PASS. Tests check 26 pinned certificates, all candidate index bounds, complete private-vertex policy, explicit static root set and source-topology mapping rather than nearest-point substitution. These are static/source tests; damage runtime acceptance remains pending.

### Upcoming bounded trio parser

`audit_trio.py` reads exactly three `fleet-damage-PID-dDEVICE-fFRAME.bin` captures in healthy/damaged/further-damaged order. It rejects malformed/truncated/trailing/overlapping input, unsupported native layouts, nonfinite XYZ/UV/WORLD, bad indices, empty generations/revisions and duplicate JSON/leaf identities. It requires one process/device/build and the same current owner triple; healthy sources must match all 26 original ordered XYZ and UV/winding signatures. Later sources join by current source dimensions, exact UV/winding and retained material-vector/first-material discriminator. No root ordinal authorizes a join.

Every mapped private vertex then requires all source candidate deltas to agree within 0.000001. The 956 explicit static crew/interior vertices are counted separately. Output distinguishes correspondence consistency from actual observed native deformation, and never authorizes implementation automatically. Usage: `python audit_trio.py HEALTHY.bin DAMAGED.bin FURTHER.bin --output trio-audit.json`.

Initial parser validation before the actual trio: `test_correspondence.py`4/4 and `test_capture_audit.py`4/4 PASS. Superseded by the actual-capture results above and updated tests below.

Updated focused validation after actual trio: source/clone tests4/4 and parser/join/delta tests6/6 PASS. The added negative test rejects shared-material/UV records if their exact healthy XYZ discriminator changes; reversing input order still joins the unchanged records correctly.
