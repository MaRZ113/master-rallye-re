# R5V-F.2d cache-only portability

## Package status

**READY_FOR_HUMAN_CACHE_ONLY_RUNTIME_TEST.** The package is assembled, integrity-checked, and isolated from the Mercedes authoring inputs. Runtime portability is not yet proven.

Package paths:

- Runtime: `research-output/r5v_f_2b/cache-only/runtime/`
- Manifest with every DX/DXT size and SHA-256: `research-output/r5v_f_2b/cache-only/cache-manifest.json`
- Human DebugView steps: `research-output/r5v_f_2b/cache-only/CACHE_ONLY_TEST_INSTRUCTIONS.md`

The runtime executable is the existing `mercedes-cook-harness` profile used for Cook B. It is not a final display-identity candidate. The retail `Data.sma` and the rest of the isolated runtime tree are copied from that harness unchanged.

`DataGx/Vehicles/Mercedes/` contains exactly 28 files: `complete.dx`, `car.dx`, `wheel.dx`, and the 25 required DXT dependencies. It contains zero GXM, GXI, or TXT files. The DX hashes equal Cook A and Cook B; DXT hashes match the validated source manifest and all 25 parser results are PASS. The retail `Data.sma` index contains zero `DataGx/Vehicles/Mercedes/` members, so the archive cannot supply a hidden Mercedes model cache.

## Authoring Junction

The fixed phase helper `research-output/r5v_f_2b/scripts/REMOVE_MERCEDES_JUNCTION.ps1` was byte-identical to `tools/r5v_f_2b/REMOVE_MERCEDES_JUNCTION.ps1` (SHA-256 `d31cc152aaaccaafd4d13e34cae7616e9709c8078c758fa793a0caee97a5b926`). It verified the `R5V-F.2b` marker at state `created`, the exact `Junction` link type, and its actual target before removing only `D:\projects\MRallyeTNG\DataGx\Vehicles\Mercedes`.

After removal, the link path is absent; the authoring target `research-output/r5v_f_2b/authoring-root/Mercedes` remains and all 25 GXI files are intact. No recursive deletion was used.

## Human runtime gate

Not yet run. Start DebugView and launch the isolated `cache-only/runtime/MRallye.exe` from its own working directory. Select T1 local7 / ID26 for the Mercedes preview, then enter a short Practice or Quick Race and wait for the car and wheel. Save the log to `research-output/r5v_f_2b/cache-only/cache-only-debugview.log`.

Pass requires cached loads for all three Mercedes DX files and all 25 required DXT dependencies, with no Mercedes GXM read, GXI/source-authoring lookup failure, or access to `D:\projects\MRallyeTNG`. The old Junction is already absent. The remaining test result must be supplied by an actual run; package assembly alone does not prove portability.

Cache-only PASS will close the asset portability gate and allow the final Mercedes profile work to begin. It will not prove the final display identity or gameplay behavior.
