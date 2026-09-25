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

The selected serialized Trooper node is a leaf, so its serialized/pre-normalizer stream has one contributor: `$chull(Trooper)`. Range `[1911,1979)` yields 68 records, 204 corner references and 36 unique Vector-C IDs. The ordered serialized triangle C-index list is retained in `hull-hierarchy.json`. This list is **CONFIRMED_BY_BYTES**, not yet an exact runtime stream.

## Loader post-pass blocks exact stream proof

After typed node construction, `FUN_005c9990` recursively visits nodes. For positive even-sized meshes it processes pairs of triangles via `FUN_005ca370`. If the operation succeeds, the function copies generated 0x34-byte records into the shared internal mesh store and rewrites the node's `+0x1c` start and `+0x20` count. If it does not take that branch, the serialized range remains in place. `FUN_005ca370` constructs/tests candidate rotated mesh data; whether and how it transforms this exact `$chull` range has not been resolved.

Thus we know the runtime tree links and collector traversal, but do not know the post-pass branch taken for `$chull(Trooper)`, the final internal record count/order, the mapping of internal corner indices to raw Vector-C IDs, or whether the final positions are identical to raw Vector C. No dynamic node/mesh pointer capture exists for 9.3.1.

## Flat-vs-runtime classification

**UNRESOLVED.** We cannot classify `[1911,1979)` as exact, subset, superset or remapped relative to final `FUN_005df370` input. Missing and extra runtime triangles are unmeasured. No transform in the collector itself is confirmed, but a transform/representation change in the pre-collector normalizer remains possible.

The old +0.4 source-X offline candidate passes only flat GXM invariants. The available 9.3.1 DebugView test has no output, so it does not provide a fresh crash stage or emitted DX. The 8.4.1 controlled C-only runtime candidate crashed inside hull construction; it is not evidence about this 9.3.1 post-pass.

## Exact remaining mapping

Resolve only this linkage next: for the `$chull(Trooper)` input to `FUN_005ca370` and its return branch, recover the final 0x34-byte record sequence and trace each emitted corner index through the post-pass store to its Vector3 buffer value. This determines whether the final collector stream equals the 68 serialized triangles or is remapped. Do not make another runtime mutation before that mapping is established.
