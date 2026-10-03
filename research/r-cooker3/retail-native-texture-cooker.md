# Retail-native texture cache cooker — T1

**Historical preparation plan; superseded by the completed result in
[oracle-t1-texture-miss.md](oracle-t1-texture-miss.md).** T1 observed a missing
DXT failure with no GXI read or DXT write in the tested ordinary consumer path.
Do not follow the pending-run instructions below as a new task.

**Gate:** prove that the retail runtime reads one Mercedes GXI on a DXT cache
miss, writes a DXT cache file, then loads that cache. This test is only for
the chosen texture and exact harness/source pair.

## Locked candidate

`underdash-tga` is listed in the parsed `complete.dx` texture slots and in the
source `complete.gxm` material references. It is also referenced by `car`,
so drive the frontend `complete` load first and correlate texture log/path
details. The exact inputs are:

| File | Prepared location | Bytes | SHA256 |
|---|---|---:|---|
| harness EXE | `.research-output/r-cooker3/oracle-t1/runtime/MRallye.exe` | 3,121,214 | `a6a5f0590405e1a2051ef21f2be58197857e72f4a651506627c8966083a21d91` |
| GXM | `.research-output/r-cooker3/oracle-t1/runtime/DataGx/Vehicles/Mercedes/complete.gxm` | 231,795 | `95caced8716239d4fa093fc0320e737e13dc1eedc8b649456d4cc89444fe354d` |
| GXI | `.research-output/r-cooker3/source-bridge/authoring-root/Mercedes/Underdash-tga.gxi` | 65,544 | `c8e3578ac885531aad2dc8c56ba2b5edcdf35237b325a09452626b6ae436ded5` |
| historical DXT | `.research-output/r-cooker3/oracle-t1/runtime/DataGx/Vehicles/Mercedes/underdash-tga.dxt` | 65,556 | `d2eda2c6196d9d50448f90828450d81c4f6dc1d8041b7c0ae04ddbbcb81f8a9f` |
| frozen baseline copy | `.research-output/r-cooker3/oracle-t1/results/underdash-historical.dxt` | 65,556 | `d2eda2c6196d9d50448f90828450d81c4f6dc1d8041b7c0ae04ddbbcb81f8a9f` |

The GXI is 128×128. The historical DXT passes the current parser and matches
the existing offline GXI-to-DXT encoder byte-for-byte. That is only the
baseline; native retail output is not known yet. The Data.sma index has zero
`DataGx/Vehicles/Mercedes/` entries, so no archive member at that exact
namespace should mask the removed loose cache.

The existing offline comparison was re-run as a preflight and saved to
`.research-output/r-cooker3/oracle-t1/results/underdash-preflight-comparison.json`.
It reports original DXT = offline encoding, valid CRC, and 128×128 dimensions.
At that preflight stage the runtime verdict was correctly still pending; the
later T1 runtime test is closed as a negative result in
[`oracle-t1-texture-miss.md`](oracle-t1-texture-miss.md).

## Safe preflight and run

1. From the demo-cooker repository root, use the prepared T1 copy only.
   Verify `MRallye.exe`, `complete.gxm`, the runtime DXT, frozen baseline
   copy, and GXI hashes above. Both DXT files must match the recorded SHA256.
   Do not delete a file in the demo corpus, source bridge, retail install, or
   parallel R5V workspace.
2. Run the copied
   `.research-output/r-cooker3/source-bridge/scripts/SETUP_MERCEDES_JUNCTION.ps1`.
   Its prepared-copy SHA256 is
   `d28084e3894bac8001b3f0ae189e3641d1f2e12d3b4cbb7c2f44744bc6846920`.
   From the repository root, invoke it with:

   ```powershell
   & ".\.research-output\r-cooker3\source-bridge\scripts\SETUP_MERCEDES_JUNCTION.ps1"
   ```

   It refuses an existing ordinary target directory, an unknown reparse point,
   a mismatched link target, and incorrect GXI hashes. Verify
   `Get-Item -Force 'D:\projects\MRallyeTNG\DataGx\Vehicles\Mercedes'`
   reports `LinkType = Junction` and target
   `.research-output/r-cooker3/source-bridge/authoring-root/Mercedes`.
   If the helper fails or the target is not exact, stop; do not manually
   replace the path.
3. The frozen baseline copy is already staged at
   `.research-output/r-cooker3/oracle-t1/results/underdash-historical.dxt`.
   Recheck its hash, then remove **only** the
   `.research-output/r-cooker3/oracle-t1/runtime/DataGx/Vehicles/Mercedes/underdash-tga.dxt`
   file from the disposable T1 copy. Compare the directory against its
   preflight inventory and prove this was the sole deleted asset.
4. Start DebugView and clear old output. Start ProcMon if available with
   filters for the isolated `MRallye.exe` and `underdash` / Mercedes model
   paths; capture `CreateFile`, `ReadFile`, and `WriteFile` results.
5. Launch the copied T1 `MRallye.exe` with its own directory as the working
   directory. Select the harness vehicle at physical ID26 / T1 local7 and load
   the frontend preview. Capture the full DebugView output to
   `.research-output/r-cooker3/oracle-t1/results/texture-cook-A-debugview.log`.

## Required observations

The same test session must show the chosen texture through this sequence:

```text
Cached texture out of date or missing
Reading GXI
Saved cached texture
Loaded cached DX texture
```

Correlate the messages to `underdash-tga`; use ProcMon’s successful GXI read
and DXT create/write path if DebugView omits the exact filename. The runtime
must not report a GXI open/parse failure. If it loads an archive/other DXT,
the miss was masked and this run is inconclusive.

## Validate and optional Cook B

After the run, require a newly created DXT at the observed cache path. Copy it
to `results/underdash-cook-A.dxt`; do not overwrite the historical baseline.
Run the canonical comparison/parser tool on the captured bytes. From the
repository root, after setting `PYTHONPATH` to `src`, use:

```powershell
$oldPythonPath = $env:PYTHONPATH
try {
  $env:PYTHONPATH = (Resolve-Path '.\src').Path
  python '.\tools\scanner\r_demo_texture_compare.py' `
    --corpus-id demo-8.4.1 `
    --corpus-root 'corpora\demo-8.4.1\DataGx\Vehicles\Copy of Mercedes' `
    --gxi 'Underdash-tga.gxi' `
    --original-dxt 'underdash-tga.dxt' `
    --scratch-root '.research-output\r-cooker3' `
    --regenerated-dxt '.research-output\r-cooker3\oracle-t1\results\underdash-cook-A.dxt' `
    --output '.research-output\r-cooker3\oracle-t1\results\underdash-cook-A-comparison.json'
  if ($LASTEXITCODE -ne 0) { throw 'DXT comparison failed.' }
} finally {
  $env:PYTHONPATH = $oldPythonPath
}
```

This parses the GXI, historical DXT, and captured DXT, and records dimensions,
header fields, payload hashes, and byte/payload comparisons. Require 128×128
and a valid pixel payload. If bytes differ, report the exact header/payload
delta; do not label the generated result corrupt solely because it differs
from the old DXT.

If Cook A succeeded, repeat once: delete only the newly cooked DXT from the
same disposable T1 runtime copy, clear DebugView, run the same preview, copy
the result to `underdash-cook-B.dxt`, parse it, and compare A/B byte-for-byte.
The A/B repeat is optional only if the first successful load makes a repeat
unsafe or impractical; report why if skipped.

After all captures, restore the runtime copy's original DXT from the frozen
baseline after verifying the baseline hash. Keep Cook A/B outputs separate.
This returns the scratch harness to its known starting state and does not
change the historical demo asset.

## Cleanup and status rule

After T1, run the copied
`.research-output/r-cooker3/source-bridge/scripts/REMOVE_MERCEDES_JUNCTION.ps1`.
It verifies the ownership marker, link type, exact target, and preserved
GXIs, then removes only the Junction node. If it refuses, stop and leave the
target untouched for manual inspection. Confirm the link path is absent and
all 25 source GXIs remain.

Classify T1 as `CONFIRMED_BY_RUNTIME` only when the full miss → GXI read → DXT
write → cached DXT load chain is observed. Parser success alone is not a
runtime cook result. Determinism is `CONFIRMED_BY_BYTES` only if two clean
native cooks produce byte-identical DXT files.
