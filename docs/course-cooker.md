# Demo 9.10.0 course cooker workflow

Status: **runtime-confirmed bridge, variable DX output** (R5T-B).

## Observed invocation

The cooker is the Demo 9.10.0 runtime path: launch `MRallye 9.10 runtime` and
select France1. No separate cooker executable, command-line switch, or batch
command was observed. The user supplied cooker-log screenshots under the local
ignored `inputs/9.10.0_France1_log-screens/`; no raw screenshots are committed.

The repeatability lab used an isolated runtime clone under ignored
`.research-output/r5t_b/cooker-lab/`. Its `MRallye.exe` SHA-256 matched the
user's executable (`13eaa642…f1e0b78`). Original course assets and the user
installation were not edited. The cloned France1 input consisted of the old
GXM/TXT and 104 GXI resources. Before each run, the clone's `france1.dx` and
all 66 `*.dxt` files were absent. The user launched the runtime and selected
France1 twice with identical source hashes.

## Log sequence observed in the supplied screenshots

- `Cached model out of date, missing or invalid format. Reading GXM: ...france1.gxm`
- `Making dx model for moModel named [course\france1\france1]`
- `Inserting moSortPlane nodes - done`, `Vertex weld - done`
- `Building convex hull - not necessary`, `Building BSP tree - done`
- `Generating projected texture UVs`, `Building land database`, and `Generating BSP draw planes`
- Per-object `Generated BSP ... Opaque [...] Transparent [...] Planes [...]`
- Render-sort errors including `Didn't find a suitable candidate triangle for a cutting plane - giving up` and `AHHHHHH - bad BSP plane choice - giving up`
- `Saved cached model: ...france1.dx`, `Loaded cached model`, RaceTest XML loading, and `Loaded Successfully`

These log strings describe cooker steps; they do not establish that each
generated subsystem is valid or that an error affects the separate DX tag100
payload.

## Repeated output

Both forced cooks emitted revision-135 France1 DX and 66 DXT files. All 172
non-DX course files were byte-identical between the two results and matched the
source-tree hashes. The DX render data changed: run 1 had 85,212 vertices,
75,456 triangles, and 4,621 draws; run 2 had 84,738 vertices, 75,246 triangles,
and 4,638 draws. Both passed the current render-index validation.

The tag100 region had the same 10,118,248-byte payload hash in both outputs,
while its file offset moved with the render-prefix size. This is evidence that
the render prefix varies independently from the observed tag100 bytes; it does
not identify why the DX render output varies.

Exact hashes, counts, and the runtime evidence label are in
[`research/r5t_b/cooker-baseline.json`](../research/r5t_b/cooker-baseline.json).
Repeat the report from the ignored lab and local inputs with:

```powershell
python tools/r5t_b_report.py
```

The report tool reads game assets and writes only derived metadata. It does not
modify the input tree. Full source-tree copies and generated DX/DXT remain under
ignored local directories.

## 8.4.1 source to 9.10.0 runtime

The user reports that 8.4.1 France1 and Italy1 source recooked by the 9.10.0
runtime load and run in that runtime, with AI working; older start/grid
behavior survives and some visual problems remain. This is `CONFIRMED_BY_RUNTIME`
owner evidence. The isolated France1 reload also reached the logged successful
load after each forced rebuild. The bridge proves that DX revision 135 can
contain a substantially different course graph from native 9.10.0 or retail;
revision alone is not a complete compatibility signature.

No course writer is provided. All cooker outputs are temporary research data.
