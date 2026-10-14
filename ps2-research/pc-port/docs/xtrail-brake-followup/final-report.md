Phase: PS2-VEHICLE-MODEL-PORT1 — Brake/lamp follow-up
Repository: D:/Game/Master Rallye/master-rallye-re-general
Branch: master
Starting HEAD: eb44f0115d94ea5530a68c3f7d03a03825584f01
Ending HEAD: source commit in archive release-provenance.json
Overall status: PARTIAL — Terrano controls implemented, new runtime pending

The original PC brake owner already selects blight=2 above float32(0.1), otherwise
blight=1. This was independently verified in original x86 bytes. The user's
Terrano F10 pair 1288/1569 confirms native off versus on+glow submissions.
Original PS2 mode 14 uses Cd+Cs, alpha test OFF, depth writes masked and fog OFF.
These static and runtime evidence layers remain separate.

Implemented a default-disabled Terrano glow control on the exact current
native-emitted 20-face mesh. It checks full geometry, original normal/UV attributes,
current resources, race and native state before changing states. The PC texture,
geometry, brake timing, draw order and single native draw/HRESULT are preserved.
This approximates the PS2 primary additive contract; PS2 texture, sampling and
complete inherited/secondary GS behavior are not claimed as reproduced.

Added a Terrano lamp-source partition: 22 rear faces retain native PC material;
36 other faces retain Mode 4. There is no global lamp reflection ban. The previous
capture shows that the conditional off lamp itself was not receiving a Mode 4
transaction, so neither this control nor the screenshots prove one universal
cause of the overlap. The source component and visual result are separately graded.

Body/decal and the previous X-Trail cover remain intact. The user reports the cover
looks closer but still needs work; visual acceptance is withheld. Frontend F10
support now includes 24 X-Trail COMPLETE records, with bounded two-frame evidence.
Actual frontend suppression, full race model and wheel transfer remain blocked on
the precise owner/transform contracts in model-readiness.md. No working full model
replacement is claimed.

Both Win32 Release builds passed; CTest 24/24 baseline and 33/33 PS2; Python
133/133 plus 12/12 original brake/runtime contract checks passed. Exports,
interface-generator determinism and diff-check passed. Baseline DLL unchanged.
No original assets, renderer, SDK, physics, course or HUD changes. No deployment
or push. The handoff contains clean sources, patches, manifests and both DLLs,
without original models/textures or raw dumps.

Next: perform the Terrano A/B, then obtain the two X-Trail frontend F10 captures
with the new read-only observer before completing its current owner/cache join.
