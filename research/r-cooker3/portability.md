# Mercedes cache-only portability — T2

**Closed — `CONFIRMED_BY_RUNTIME`.** This file is the historical test plan;
the verified log observations are in
[oracle-t2-cache-only.md](oracle-t2-cache-only.md). Do not repeat the run
unless new evidence requires it.

**Gate:** determine whether the already-cooked Mercedes package loads from DX
and DXT alone, without GXM/GXI authoring access.

## Prepared package

Use `.research-output/r-cooker3/oracle-t2-t3/runtime/`, a byte-verified copy
of the prior isolated `mercedes-cook-harness` cache-only runtime. The EXE is
the existing ID26 / T1 local7 test profile, SHA256
`a6a5f0590405e1a2051ef21f2be58197857e72f4a651506627c8966083a21d91`; it is
not a final Mercedes identity profile. Retail `Data.sma` hash is
`03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f` and its
index has zero Mercedes-namespace members.

Under `runtime/DataGx/Vehicles/Mercedes/` the manifest expects exactly:

- `complete.dx`: `ddad0c7b13be70388a60a541255eaaf3af7f9b1815f5aa02f2b60050862dc28b`
- `car.dx`: `5ec5f7480ddfc1380131a012b300a4cdeb28b869a1668b6f8bbe97210893ff44`
- `wheel.dx`: `8707d887a75c452eb739775e21f94109521d9fc6be07726cee28a8e911c590ff`
- the 25 DXT listed with hashes in `.research-output/r-cooker3/oracle-t2-t3/cache-manifest.json`.

The folder contains no GXM, GXI, or TXT. The global authoring Junction
`D:\projects\MRallyeTNG\DataGx\Vehicles\Mercedes` is currently absent. Do
not recreate it for T2. If a real directory or any reparse point appears at
that path, stop; do not remove or replace it.

## Human test

1. Recheck package DX/DXT hashes against the copied `cache-manifest.json` and
   verify the source-file absence above. Confirm the Junction remains absent.
2. Start DebugView, clear old output, then launch the copied
   `oracle-t2-t3/runtime/MRallye.exe` from its own working directory.
   Capture Process Monitor for this `MRallye.exe` as well, filtering file
   operations to `D:\projects\MRallyeTNG\` and the runtime process. This is
   the evidence for the negative source-path assertion; DebugView alone may
   not expose every attempted file open.
3. Select T1 local7 / physical ID26 and wait for the Mercedes frontend
   preview. Enter a short Practice or Quick Race and wait for car and wheel.
4. Save the full log to
   `.research-output/r-cooker3/oracle-t2-t3/results/cache-only-debugview.log`.
   Record whether the preview, `car.dx`, and `wheel.dx` loaded, and which of
   the 25 Mercedes DXT files logged as cached loads.
5. Check only Mercedes model-source paths for negative assertions. Unrelated
   base-game GXM activity does not fail this test.

## Pass criteria

One run must show a cached load for `complete.dx`, `car.dx`, and `wheel.dx`,
and load all required Mercedes DXT dependencies. It must show no Mercedes
`Reading GXM`, no Mercedes `Reading GXI` or source-open failure, and no access
to `D:\projects\MRallyeTNG`.

After exiting normally, hash all 28 DX/DXT files again against the manifest.
Report any cache or config file the game added separately. Only when load
observations and post-hashes pass may this package be classified
`CACHE_ONLY_PORTABLE` / `CONFIRMED_BY_RUNTIME` for this Mercedes harness. This
does not prove final vehicle identity or gameplay handling.
