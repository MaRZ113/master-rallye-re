# Definitive Edition — independent Forester preparation

**Historical preparation snapshot; superseded by [V-DEF1 restoration](V_DEF1_FORESTER_RESTORATION.md).** The original findings below are retained as pre-pilot history, not current unresolved status. User identifies demo/PS2 `FORESTER` driver as Darren Sutherland; original data-to-driver binding is not yet verified. Retail PC registry ID8 is named `Forester`, display `SUBPELKA WOOLDAND`, class T2; it is a distinct reference and must not be conflated with the demo/PS2 family. See `research/r5v_a/final-vehicle-registry.md`.

The actual local demo 9.3.1 `DataGx/Vehicles/Forester` has 56 files: two DX, 23 DXT, 24 GXI, three GXM and four TXT. Important source hashes:

| Resource | Bytes | SHA256 |
|---|---:|---|
| `car.gxm` | 219728 | `3d27573a2358f379de1c1914fb6a17ac525a5a709bd62ab824736d05ac4c2535` |
| `comlplete.gxm` (original spelling) | 257541 | `3fa2cff8c100b66236b1f076c164a402ac199fe3502838e0bc18be8a381b790f` |
| `wheel.gxm` | 27272 | `2f1542430065108649a4629f613493de85332e15a7755dda96ce66d79ea3e48d` |
| `car.dx` | 128327 | `eb2909b1d623f9e053a11114fe1d6d17283495bf7cab902755f87d2ee299e7de` |
| `wheel.dx` | 12937 | `1e2fefdf5fdaa4eba94490a3287de2fbc14863b6812c5902ba8f4d3a089d3dd7` |

The original folder lacks `complete.dx`. Existing r-demo cooker findings document qualified reconstruction of the complete role and an owner-reported runtime result for that exact prior package; it is not a proof of a new independent slot, driver, physics or damage. Preserve the typo in source and use a staged name only when required by the cooker.

Demo 9.3.1 `DataGx/Frontend/VehicleSelect/CarSheet.gxb` is 773848 bytes, SHA256 `4125500080fb5d4b9cdcabca2f116a79243f159de6bcadaa9a75c76b35d232b7`; existing research identifies a 340×569 atlas. Its exact Forester frame/UV binding remains unresolved. The owner-reported driver identity is not evidence of an atlas index. The local filename search found PS2 `WOOLDAND` references, but it was not a complete search of all packed PS2 members; do not infer PS2 `FORESTER` is absent.

The accepted 30-entry, 8/10/12 roster requires **one additional independent record and one T2 class position** for this goal. Two T2 positions remain arithmetically within the observed 12-position publisher, but no CarID, physical allocation, dense forward/reverse mapping, resource frame, unlock, AI, audio, replay, save or race lifecycle has been qualified for a 31st vehicle. CarID29 already has alternative accepted configurations and is not available for this purpose. Existing J.3 collection runtime supports ID26 and ID27 only; its successful static build does not establish 31-entry capacity. See CLASS_SLOT_RESEARCH.md.

Next evidence: locate and identify the PS2 source and original icon mapping; bind the owner-supplied driver name to original data; create a separate editable physics family from an evidenced donor; compare intact/breakable glass and native glow-on with retail `WOOLDAND`; qualify the independent registration path and a complete game lifecycle. No such integration or live test is claimed here.

Further source inspection: demo 9.3.1 `car.txt` names `glass $glass`, `rearlight $perspex` and `blight $perspex`; `FScreen32` references WindScreen32 and glass textures. These are source-side ownership leads, not proof that a particular intact pane or glow controller is retail-compatible. The existing Heritage `auto_features` and `native_brakes` writer can be evaluated on a complete staged family; the source `complete.dx` is missing, so no new glass/glow build is claimed.

The demo `vehicles.xml` contains 150 Forester value names; retail contains 147, and the retail unpacked XML was byte-verified against its clean SMA member. Several meaningful values differ: demo front/rear track width 1.70 versus retail 1.60, peak torque 350 versus 285, rev limit 7000 versus 6500, and final drive 3.82 versus 3.72. Both list mass 1340 and the same selected front/rear spring and damper values. This is evidence for a separate profile and against assuming full parameter equality; it is not evidence that demo physics can be copied unchanged into retail. A bounded search of the local demo DataGame/DataScene XML found no Darren/Sutherland string; PS2 binding remains unverified.
