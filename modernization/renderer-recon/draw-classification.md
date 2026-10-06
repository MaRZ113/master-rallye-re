# Classification for future proxy observations

The exact caller PCs identify API-owner paths; they do not alone recover game
object meaning inside shared indexed queues. All addresses below are VA; JSON also
records RVA. No semantic classifier was implemented or validated at runtime.

| Category | Useful signals | Current status / evidence |
|---|---|---|
| SKY | CloudNumber resource identity; mode2 camera-relative X/Z world transform; packet fog bit cleared | RESOURCE_PROVENANCE_REQUIRED / STATIC_INFERENCE |
| TERRAIN | scene model resource identity; hierarchy/entity ownership | UNRESOLVED / HYPOTHESIS |
| ROAD | material/resource identity plus surface linkage | UNRESOLVED / HYPOTHESIS |
| STATIC_OPAQUE | opaque queue; base family; scene resource | RESOURCE_PROVENANCE_REQUIRED / STATIC_INFERENCE |
| VEGETATION_ALPHA_TEST | ALPHATEST=1/REF128/FUNC5; foliage texture/model identity | RESOURCE_PROVENANCE_REQUIRED / STATIC_INFERENCE |
| VEHICLE_BODY | vehicle resource and compiled instance identity; entity model binding /car in004B6A00 | RESOURCE_PROVENANCE_REQUIRED / STATIC_INFERENCE |
| VEHICLE_WHEEL | wheel.dx instance/resource provenance; entity parent/Wheel0..3; Physics/<name>/Transform; ordinary vs Alpha/replay resources | RESOURCE_PROVENANCE_REQUIRED / STATIC_INFERENCE |
| VEHICLE_GLASS | vehicle material identity and alpha queue | RESOURCE_PROVENANCE_REQUIRED / STATIC_INFERENCE |
| PARTICLE | 005641C0 caller; FVF142 stride24; particle texture | API_OWNER_CONFIRMED / CONFIRMED_BY_EXE |
| TRANSPARENT_WORLD | alpha queue; blend signature; instance/model | RESOURCE_PROVENANCE_REQUIRED / STATIC_INFERENCE |
| HUD | 0056D110 packet; ortho projection; HUD resource/state | UNRESOLVED / HYPOTHESIS |
| FRONTEND_UI | 0056D110 packet; frontend resource/state | UNRESOLVED / HYPOTHESIS |
| UNKNOWN | default if multiple matches or missing provenance | DEFAULT_POLICY / STATIC_INFERENCE |

Caller00564ECA reliably identifies the inspected billboard emission path statically.
005722E8 identifies trail triangles;005881E5 stock projected shadows. Packet
0056D7BE identifies text/2D emission, but does not split HUD/frontend/world labels.
0056C0D0 is video;00589B70 and0058A4F0 are optional debug. These auxiliary families
should be retained separately rather than incorrectly forced into terrain/UI.

Caller00577078 or00580242 alone cannot distinguish sky/terrain/road/static/car/wheel/
glass. All can reuse buffers and material families. A base/env/alpha signature
is a material signal, not a unique semantic category. Alpha-test also matches
nonvegetation cutouts;0x142 also matches particles/UI/video and some base meshes.
Current material pointers/entity names are engine-side information, not D3D API
arguments, so a pure proxy does not automatically receive them.

Combine return PC normalized to module RVA, texture and VB/IB slice identity,
FVF/stride, effective depth/blend/TSS, WORLD/view/projection/viewport, frame-camera
order and optional later read-only resource provenance. Use UNKNOWN for overlapping
signatures or missing provenance; preserve confidence and original raw signals.
Match proxy return PCs against callmap `return_rva`, not the CALL-instruction `rva`.
Resource hashing/upload records must account for shared slices and post-damage
content. No body/wheel/glass classifier is declared runtime reliable.
