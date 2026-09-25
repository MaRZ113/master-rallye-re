# R-DEMO2.4 — Runtime hull input reconstruction

## Static collector order

Exact 9.3.1 EXE analysis of `FUN_005de630`, `FUN_005df060` and `FUN_005df370` establishes this collector behavior:

```text
find a node whose name contains "$chull"
count = current_mesh.triangle_count * 3
for each child in child/sibling order:
    count += recursive_count(child)
for each current-node mesh triangle in stored range order:
    append position(record.corner[0])
    append position(record.corner[1])
    append position(record.corner[2])
for each child in child/sibling order:
    recursively append child stream
```

The collector uses the current node's mesh first, then walks child head at `+0x04` and sibling at `+0x08`. `FUN_005df370` reads three indices from each post-load 0x34-byte internal record at `+0x1c`, `+0x20`, `+0x24`. Position storage is reached from the model data object at `+0x38` and buffer `+0x04`. These offsets and order are **CONFIRMED_BY_EXE**. The collector applies no node-local transform itself.

The selected serialized Trooper node is a leaf, so its serialized/pre-weld stream has one contributor: `$chull(Trooper)`. Range `[1911,1979)` yields 68 records, 204 corner references and 36 unique Vector-C IDs. The ordered serialized triangle C-index list is retained in `hull-hierarchy.json`. This list is **CONFIRMED_BY_BYTES**. R-DEMO2.5 proves the same C indices reach the hull collector for the pinned baseline/candidate; numerical coordinate streams are reproduced offline with loader precision variants, not captured runtime bytes.

## R-DEMO2.5 control-flow correction

`FUN_005c98d0 -> FUN_005c9990 -> FUN_005ca370` runs during Parsing 2d geometry, after convex hull, BSP and cylinder. R-DEMO2.4's use of this chain as a pre-hull blocker was incorrect. Its mesh-rewrite observations apply only to that later stage.

The true pre-hull sequence is `FUN_005cab00` (sort planes), `FUN_005ca990` (vertex welder), then `FUN_005de630 -> FUN_005df370` (hull). The initial R-DEMO2.5 gate was UNRESOLVED; the completed result is **Path B for the pinned 9.3.1 pair**.

## Completed buffer provenance

The earlier parser starts each raw record at its material word, 12 bytes into the native 0x34-byte record. `005be940` preserves the underlying bytes: raw word4/5/6 are native +0x1c/+0x20/+0x24. `005bdf40` fills model+0x34 records and model+0x38 C vectors, then rotates C around X by -90 degrees through `005b64d0`. `005ca990` can copy coordinates in place, but never changes those pointers, counts, indices or node ranges.

All 36 hull C indices (1317..1352) are more than 0.01 from every other global position for both inputs. No queued weld can touch them, regardless of native sort order or guards. Thus `005df370` emits the same 68 triangle records / 204 corners from the leaf after welding. The candidate is a rigid +0.4-X translation within float32 noise: maximum fitted residual `3.25780289e-8`, zero degenerates, unchanged index topology/winding/adjacency. No sort-plane or removed-node match occurs.

Full proof, arithmetic limitations, hashes and repeatable report: `vertex-welder.md`. This result is **CONFIRMED_BY_EXE** data flow plus **REPRODUCED_OFFLINE** measurements, not a debugger dump. Other render weld classes and the differently hashed 8.4.1 crash input are not reconstructed by this oracle. The crash cause remains unknown inside the hull-library investigation; no new runtime mutation was performed.
