# Isolated Trooper `$chull` runtime candidate

Status update (R-DEMO2): the human test **CRASHED_IN_RUNTIME** in both demo 8.4.1 and 9.3.1. The source-position-only approach is not safe as tested. Do not create another hull mutation until the crash stage and source dependencies are identified. The structural audit below describes the 8.4.1 candidate; see `research/r-demo2/chull-crash.md`.

The same-build `Trooper.txt` names a final mesh `$chull(Trooper)`, GXM records 1911–1978 (68 records). Its position index triple references 36 unique Vector C entries, exactly 1317–1352. None is referenced by the preceding 1,911 records. After the established `(x,y,z)→(x,z,-y)` mapping and four-decimal rounding, 0/36 hull positions occur in the leading same-build `car.dx` position array, while 1,305 nonhull GXM positions do. This supports separation from visible render geometry; it does not identify a complete demo DX collision section.

The candidate translates source X by `+0.4` for these 36 positions only (observed source-to-DX mapping keeps X as X). GXM records, other position components, the 1,317 nonhull Vector C positions, materials, strings, topology, and hierarchy bytes are unchanged. The candidate reparses. No source corpus file was written.

| Item | Value |
|---|---|
| Original SHA256 | `fd08bc10c440fce261ef126e40445002fb56359d4011c1dcbf9c2f71b0e91047` |
| Candidate SHA256 | `0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699` |
| File size | 222,749 bytes, unchanged |
| Changed positions | 36 Vector C X components; 126 differing bytes within those float32 fields |
| Byte ranges | Full end-exclusive list in ignored `car.audit.json` beside candidate |
| Candidate | `.research-output/r-demo/runtime-tests/chull-translate-x040/DataGx/Vehicles/Trooper/car.gxm` |

Reproduce with `tools/scanner/r_demo_chull_candidate.py` using the source hash gate and same-build sidecar/DX. The generated `.gxm` and audit JSON remain ignored.

## Historical test protocol (already performed; crash reported)

The following was the original scratch procedure. Do not repeat the same crashing mutation without first localizing the failing cooker stage. Use a separate clean runnable demo 8.4.1 copy. Record baseline hashes. Replace only scratch `car.gxm` with the candidate; retain the original scratch `car.dx`, `complete.gxm`, `wheel.gxm`, textures and other files. Start the same vehicle/race scenario as the baseline. Approach a stable wall/obstacle slowly from both lateral directions; record game load, unchanged visible body, presence of primary collision, apparent collision offset and direction, normal wheel physics, and artifacts. Restore the scratch baseline after the test. A side-by-side video or fixed viewpoint is useful, but raw media stays outside Git.

If collision shifts laterally with the body unchanged, `$chull` participation is **CONFIRMED_BY_RUNTIME** for this path. If neither shifts, the source-to-runtime collision route remains unresolved. If the visible body shifts, the candidate did not isolate collision as expected. The observed outcome is a crash in both demos; collision offset remains untested.
