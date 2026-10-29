# Xbox Pajero — bounded rear-spare probe

29 October2026. Small optional part of v7.6; Michelin remained the main task. Original source scene SHA256 `fb9a91ee48b1fa762115945085e1804dd2cdb791dde08c61bb018b45cecbd8ad` remains pinned/unchanged. Old MR203 livery experiment was not reopened.

Three real nodes exist: PAJ_SPAREWHEEL1/2/3, IDs029/030/031, parent node024 PAJ_REARROLLCAGE. Each references two original submeshes,36 triangles total. They sit side-by-side **inside the rear cage**, axle along X. Approximate assembled bounds: X[-0.4646,-0.1758],[-0.1390,0.1498],[0.1778,0.4667]; common Y[0.0537,0.8542], Z[-1.7347,-0.9481]. They are not a recovered centered external rear-door configuration. HIR flags/lod flags/source visibility and parent/raw record hashes are retained; actual runtime equipment activation remains UNKNOWN.

Original materials reference xtx052 (source blend classification enabled) and xtx053 (opaque). Exact per-node source/world transforms, materials, flags, original mesh IDs and six-decimal position-weld edge counts are in private `pajero-final/probe.json`. Winding/cull/alpha information is inspected without changing it. Boundary counts alone cannot prove missing back geometry because seams and nonmanifold features also produce them. Original Xbox wheel shading/secondary stages remain L2 WARN.

**Optional B:** add one independent instance of original node030's mesh references, +90° authored Y rotation, center[0,0.45,-2.02] in source coordinates. No new tyre mesh, texture/UV edit, repainting, source-node relocation or source equipment-state claim. This is an **MR-inspired visual overlay**, not the original missing MR mesh or confirmed Xbox equipment setting. Mount hardware/collision/damage is absent; side-view gap/mount plausibility is still WARN and not a production fitment. The three originals and all original mesh/material/texture arrays stay intact. `overlay(scene,False)` restores exact A, rather than trying to invert rounded coordinates. Source/derived transformations are explicitly separate.

Wheel backing is **DEFERRED**. Original wheel cutouts and blend materials, mixed facing and incomplete source renderer semantics do not justify a global alpha/cull change. No black discs/caps were generated; no rim or tyre hidden. Original wheel close-ups are provided as diagnostics. Further mount/backing refinement belongs to a later user-controlled geometry task, not this milestone.

Private `.research-output/vehicles/michelin-assembly/pajero-final/`: A and B-derived-spare UVS projects, six views each, and six original wheel-isolation views. Rear and side captures inspected; wheel close-up exposes retained openings. Source hierarchy/material ownership and authored transform are recorded in probe.json. Synthetic tests cover unchanged original arrays/nodes, explicit derived ownership, absent-node rejection and exact restore. No physics, collision, spare damage, native CarID or accepted-project changes.

```powershell
python tools/pajero_spare_lab.py --source .research-output/vehicles/dakar2-fidelity/final/PAJERO/scene/scene.json --output .research-output/vehicles/michelin-assembly/new-spare-probe --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe
```

Stop: no full Pajero polish or continuation of old red-texture transfer.
