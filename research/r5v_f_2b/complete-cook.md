# Complete model native cook

The first successful retail run remains the baseline proof for complete.gxm to complete.dx revision 135.

In cook-a/complete-cook.log, lines 1499-1522 show cache miss, staged complete.gxm read, retail model build, save to runtime-cook/DataGx/Vehicles/Mercedes/complete.dx and cache reload. Output SHA-256 is ddad0c7b13be70388a60a541255eaaf3af7f9b1815f5aa02f2b60050862dc28b; size is 122372 bytes; strict current parsing returns VALID.

The modern DX parser confirms 2305 vertices, 2096 triangles, 18 draw records, complete index/vertex coverage and finite positions, normals, UVs and marker bounds. The footer56 bounds match the render AABB. Tag102 and marker-1339 are accepted. Twenty non-null textures resolve, parse and load.

Comparison with the matching Copy of Mercedes rev127 output preserves local/global indices, normals, UVs and bounds. Position drift is at most 1.42e-14. Thirty RGB bytes change 178 to 179; alpha is unchanged. This is a small bounded cooker/precision change.

The later car/wheel DebugView log loaded complete.dx from cache; it did not recook complete. Therefore the immutable Cook A set is assembled from the first complete capture and the later car/wheel capture. A fresh Cook B must recook all three from absent caches.
