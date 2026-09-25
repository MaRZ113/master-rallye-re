# Isolated Trooper `$chull` runtime candidate (historical protocol)

The user tested the isolated source-position candidate in both demo builds; it **CRASHED_IN_RUNTIME**. The 8.4.1 DebugView trace ends after `Building convex hull -`, localizing that observed crash inside convex-hull construction. The 9.3.1 crash was reported but no matching DebugView stage trace was observed. Exact failing input dependency and cause remain **UNKNOWN**. Do not repeat the same mutation or treat this as a safe hull-edit recipe. Current parsed analysis is in `research/r-demo2/chull-crash.md` and `cooker-stages.md`.

The same-build `Trooper.txt` names a final mesh `$chull(Trooper)`, GXM records 1911–1978 (68 records). Its position index triple references 36 unique Vector C entries, exactly 1317–1352; none is referenced by the preceding records. After `(x,y,z)→(x,z,-y)` mapping and four-decimal rounding, 0/36 hull positions occur in the leading same-build `car.dx` position array, while 1,305 nonhull GXM positions do. This supports separation from visible render geometry; it does not identify a complete demo DX collision section.

The candidate translates source X by `+0.4` for these 36 positions only. GXM records, other position components, the 1,317 nonhull Vector C positions, materials, strings, topology, and hierarchy bytes are unchanged. It reparses; no source corpus file was written.

| Item | Value |
|---|---|
| Original SHA256 | `fd08bc10c440fce261ef126e40445002fb56359d4011c1dcbf9c2f71b0e91047` |
| Candidate SHA256 | `0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699` |
| File size | 222,749 bytes, unchanged |
| Changed positions | 36 Vector C X components; 126 differing bytes within those float32 fields |
| Candidate | `.research-output/r-demo/runtime-tests/chull-translate-x040/DataGx/Vehicles/Trooper/car.gxm` |

Any future hull work needs a newly justified, independently safe test design and must first address the observed crash; this historical candidate note does not authorize repeating it.
