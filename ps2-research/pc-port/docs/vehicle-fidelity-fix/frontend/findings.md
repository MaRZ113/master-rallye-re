# X-Trail frontend: new same-session evidence

Session 35860 uses the accepted c8c91ed5 proxy and exact protected retail PC EXE.
Both requested captures independently contain all **24/24 Xtrail/complete.dx
source records**, 2,487 source triangles. Current CPU-upload geometry hashes,
VB/IB generations/revisions and draw ranges are retained in runtime-evidence.json.
These are geometry/resource identities, not persistent draw ordinals.

Frame 1040 and frame 2051 share VB generation 693 / IB generation 694 and
the same source geometry, while the model world rotation changes. Every one
of the 24 records has the same world matrix within its respective frame;
translation is (8,-2,189). Native view and projection stay unchanged, all
GetTransform HRESULTs are zero, and native values match effective tracked
matrices. This positively verifies coherent menu rotation and transform
ownership at draw time. It does not establish PS2-to-PC local origin alignment.

Evidence grade: CONFIRMED_BY_RUNTIME for the proxy observations. Static PS2
COMPLETE geometry remains 4,636 authored faces / 24 meshes; those counts are
not interchangeable with the PC compiled source triangles.

## Exact missing admission link

The observer intentionally reports model_owner_join_verified=false and
replacement_enabled=false. No current frontend CarMover/Egg/en3d/cache pointer
appears in these records. Source uploads plus coherent rotation therefore
cannot prove safe replacement ownership or model cache teardown.

The remaining chain is current VehicleSelect CarMover/Egg -> en3d name +0xc,
owned cached model +0x74 -> its mesh consumers -> these current-generation
uploads. Existing verified x86 observation point 0x44c4f6 exposes EDI CarMover,
EBP Egg, [EBP+0x50] en3d and ESI selection. It is still a targeted next capture,
not a hook or proven structure walk implemented by this audit. A bounded
read-only observation there must correlate the same session's active
Xtrail/complete resource and cache consumer, then invalidate on car change,
menu exit and true device Reset. No private loader, cache mutation or model
suppression is authorized by the present evidence.

Four session lines (649,664,679,1305) fail JSON parsing. They are explicitly
recorded, not silently converted into missing proof; all 48 requested frontend
identity records parse successfully. Both complete frame files parse fully.

Focused evidence tests verify complete coverage, current matrix HRESULTs,
changed world rotation, unchanged view/projection and the unproved owner gate.
No source integration, build, game memory read/write or native replacement
was performed in this workstream.
