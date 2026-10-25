# V-LAUNCH1 — graphics proxy compatibility

## Result and exact former block

The external J.1/J.2 launcher stopped the integrated launch in `Launch()`
before `CreateProcessW`. `HasUnqualifiedProxy()` treated every adjacent wrapper
name as incompatible, including `d3d8.dll`, and returned the generic
`graphics/input proxy compatibility is not qualified` failure. Bundle
verification could pass because this check only ran on integrated/canary
launch. This was a launcher policy block, not a resource-root or graphics
loader failure.

The launcher now permits only an adjacent `d3d8.dll` whose complete SHA256 is
in the audited allowlist below. It opens the proxy read-only while denying
write/delete sharing and holds that file handle through game exit, so the file
Windows resolves cannot be replaced between verification and normal process
startup. The EXE identity, mapped image checks, native preimages, operation
manifest, bundle/resource inventory, and all other proxy refusals remain in
force. `d3d9.dll`, `ddraw.dll`, `dinput8.dll`, `dsound.dll`, `winmm.dll`,
`version.dll`, and `dxgi.dll` still fail closed.

## Verified proxy files

Each candidate was checked with the renderer project's PE/export verifier:
PE32/I386 DLL, direct `Direct3DCreate8` ordinal 5,
`ValidateVertexShader` ordinal 3, `ValidatePixelShader` ordinal 2, no recursive
`d3d8.dll` import, and no delay-import directory.

| Source | Size | SHA256 |
|---|---:|---|
| `master-rallye-re-general/ps2-research/pc-port/.build/baseline/Release/d3d8.dll` | 2,550,784 | `eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4` |
| `master-rallye-re-general/ps2-research/pc-port/.build/ps2-enabled/Release/d3d8.dll` | 6,295,040 | `235aae55e077fca1e5b5208d4ac158b1a00dd80041fa5885bd06890a041b1eb8` |
| `master-rallye-re-general/modernization/renderer/.build-msvc/Release/d3d8.dll` | 2,550,784 | `339174529605b6b4602715470ac67e0bf39d7f95197b0d07fe2dbd048a960ea1` |
| `master-rallye-re-general/modernization/renderer/.build-msvc-hudperf/Release/d3d8.dll` | 2,499,072 | `f84fd763dcf26ab2d79c254cfe49f1b4deb19f8b6378882971a08659d2318b77` |

Only these exact proxy builds are accepted. A rebuilt or edited proxy must be
audited and added as a new exact hash before this launcher accepts it. The
launcher does not copy, replace, or configure the proxy.

## Launch layout and instructions

Windows resolves the game's adjacent `d3d8.dll` from the executable's
application directory. The external launcher uses the bundle's
`resource-root` as the child working directory, but does not redirect the
application directory. Therefore the chosen proxy must be copied as
`<game-directory>\d3d8.dll`; leaving it only in a build directory does not load
it. Do not overwrite an existing `d3d8.dll`. If that filename already exists,
check its SHA first and stop if it is not one of the four approved files.

The audited renderer source derives `MRRRenderer.ini` from the loaded proxy
module's directory and writes diagnostics below that same directory as
`MRRRenderer\logs`. Keep the intended config file beside `MRallye.exe` and
`d3d8.dll`; the current `D:\Game\Master Rallye\MRRRenderer.ini` already
provides it. Do not copy build-tree `MRRRenderer\logs` into the game. The
launcher changes the process working directory to the external resource root,
but this proxy's config/log paths are module-directory-relative.

The current V-MESH4 handoff targets
`D:\Game\Master Rallye\MRallye.exe`. That directory currently has no adjacent
wrapper DLL, so launcher-only operation remains available. Verify both the
runtime bundle and launch environment before starting:

```powershell
$game = 'D:\Game\Master Rallye'
$exe = Join-Path $game 'MRallye.exe'
$proxy = 'D:\Game\Master Rallye\master-rallye-re-general\ps2-research\pc-port\.build\ps2-enabled\Release\d3d8.dll'
$candidate = 'D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\vmesh4\vlaunch1-final'
$loader = Join-Path $candidate 'mr-runtime-launcher.exe'
$bundle = 'D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\vmesh4\v4-exp-001\runtime'

Get-FileHash -Algorithm SHA256 $exe
Get-FileHash -Algorithm SHA256 $proxy
if (Test-Path -LiteralPath (Join-Path $game 'd3d8.dll')) {
    if ((Get-FileHash -Algorithm SHA256 (Join-Path $game 'd3d8.dll')).Hash.ToLower() -ne (Get-FileHash -Algorithm SHA256 $proxy).Hash.ToLower()) {
        throw 'The existing game-directory d3d8.dll differs from the selected proxy; preserve it and resolve the choice explicitly.'
    }
} else {
    Copy-Item -LiteralPath $proxy -Destination (Join-Path $game 'd3d8.dll')
}
& $loader --verify $exe $bundle
if ($LASTEXITCODE -ne 0) { throw 'Bundle verification failed; do not launch' }
& $loader --verify-launch-environment $exe $bundle
if ($LASTEXITCODE -ne 0) { throw 'Proxy/environment verification failed; do not launch' }
& $loader --integrated $exe $bundle
```

For the renderer build, set `$proxy` to the desired exact `.build-msvc` or
`.build-msvc-hudperf` path above. The integrated launch must print
`APPROVED_GRAPHICS_PROXY sha256=<approved hash>` before creating the child.
After testing, leave the pre-existing proxy in place or restore only a backup
made before a deliberate proxy replacement. Never delete a pre-existing file. Recheck the retail
EXE SHA before and after; the expected value is
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

## Compatibility matrix

| Configuration | Result / evidence |
|---|---|
| Launcher only, no adjacent proxy | **Supported path retained.** The exact retail/runtime gates still apply. This candidate has static verification; the previously qualified J.1/J.2 runtime evidence remains the gameplay evidence. |
| Proxy only, original EXE launched normally | **Independent existing path.** The renderer proxy and its normal settings remain untouched. This task did not rerun a proxy-only gameplay test. |
| Launcher + one allowlisted proxy | **Ready for human runtime test.** Static DLL identity/exports are verified and the launcher no longer rejects it. Combined rendering/free-camera/HUD capture behavior is not claimed until tested live. |
| Launcher + unknown proxy or any other adjacent wrapper | **Fail closed.** No blanket proxy bypass is introduced. |

The launcher installs its complete native patch set while the child is
suspended, then resumes it. The D3D8 proxy initializes through normal Windows
DLL loading after resume. This does not alter the proxy's code or native
renderer behavior. A combined runtime test must verify normal frontend,
Vehicle SDK vehicle materialization, free camera/HUD controls, and clean exit.

## Validation boundary

The exact launcher source change and allowlist regression are covered by the
synthetic suite. The four DLLs passed static PE/export verification. The new
launcher was built from the existing J.2 bundle, and its `--verify` path checks
the unchanged retail EXE and sealed bundle. No combined proxy+launcher game
session was run in this phase; report that as pending human runtime rather than

The separate `D:\Game\Master Rallye Pristine` directory was also inspected:
its `d3d8.dll` matches the approved PS2-enabled proxy, but it has an adjacent
`dinput8.dll` with SHA256
`52ee1332e7a587878ea846a19dd7fcd5ca4cdd41694355558ee47e72c9c77c36`. That
input proxy remains unqualified and is intentionally refused. Use the
V-MESH4 target `D:\Game\Master Rallye` for this compatibility test; do not
remove or replace the unrelated input proxy in the Pristine installation.
