# R-GFX1 validation and completion gate

Status: **MORE WORK NEEDED**. Static reconnaissance and its tools are reviewable;
the full requested confidence gate is not satisfied. Runtime observations are
absent. No test result below is a game-rendering PASS.

## Checks performed

* Exact external MRallye.exe SHA256 verified before PE/Ghidra analysis and before
  every scanner run; build identity and 14 import DLLs recorded in build.json.
* Ghidra12.1.4, newest installation found on D:, with installed ghidra-bridge
  exporter. Read-only project/program APIs; temporary queries rolled back; no
  program save. 191 curated function instruction fingerprints in evidence-index.
  Mid-function exploratory queries were excluded from that evidence index.
* Python3.14.0; pefile2024.8.26; capstone5.0.9. Ghidra exporter uses its existing
  Python3.11 environment and Java25.0.2 installation.
* `python -m compileall modernization/renderer-recon`: PASS.
* `python -m unittest discover -s modernization/renderer-recon/tests -v`:
  **11 tests PASS**. They cover exact-build rejection before output/project access,
  output boundaries, ambiguous COM offsets, direct-IAT/register-call exclusion,
  reviewed bytes/slot/receiver validation, CALL versus return-PC addresses,
  VA/RVA consistency and agreement between master map, API inventory and passes.
* Two independent scanner outputs matched all four committed scanner artifacts
  byte-for-byte: build.json, imports.json, d3d8-callmap.json, d3d8-callmap.tsv.
  224 reviewed calls, 4,434 untyped candidates. Untyped candidates are not promoted.
* JSON parse and local Markdown-link checks: PASS. New research is entirely under
  modernization/renderer-recon; raw analysis/cache/bytecode is ignored there.
* `git diff --check` and staged `--check`: PASS. Staged scope/file audit:49 new
  files, zero modifications to previously tracked files; each file under the new
  directory and below1MB. No proprietary EXE/assets/Ghidra DB/raw export tracked.

The synthetic suite does not execute Java/Ghidra; database protection follows the
reviewed read-only API path and rollback lifecycle. Receiver semantics remain
human-reviewed evidence, not a result of offset matching alone. Linear Capstone
scan and existing Ghidra disassembly have different coverage; neither proves that
every executable path or register-indirect call has been discovered.

## Requested 28-question gate

MAPPED means the static source/mechanism is identified, with actual hardware,
options and runtime frequency still to observe. PARTIAL means a material missing
link remains. CONDITIONAL is a feasibility judgment. None means runtime-confirmed.

| # | Question | Static result | Evidence / remaining requirement |
|---|---|---|---|
| 1 | Obtain IDirect3D8 | MAPPED | static d3d8 import, SDK120,0055905B; d3d8-entry |
| 2 | Create device | MAPPED |0055AB90/0055ACD7, full argument sources; device-creation |
| 3 | Presentation parameters | MAPPED | all13 fields; runtime-selected format/depth/mode still to capture |
| 4 | Main frame loop | MAPPED |005AFE30 ->00653080; frame-lifecycle |
| 5 | Actual methods | PARTIAL |224 reviewed sites; optional helpers/register dispatch not fully reachable-mapped |
| 6 | Major draw categories | PARTIAL | common indexed plus particles/UI/video/debug; road/terrain/vegetation identity unresolved |
| 7 | Vertex formats | PARTIAL | observed142/42/62, helper144, eight derived layouts; all realized layouts need capture |
| 8 | Textures created/bound | PARTIAL |005587E0 ->005589CD ->cache/bind; full input decoding/eviction coverage open |
| 9 | Pipeline model | PARTIAL | mapped families fixed function; shader absence is bounded to reviewed paths |
| 10 | Materials to states | MAPPED |16 families, ordered slots, final instance overrides; material-state-map |
| 11 | VIEW/PROJECTION/WORLD | MAPPED |005614A0,00561A40,00583B90; body/wheel producers004F5440 |
| 12 | FOV/near/far/aspect | MAPPED |004F2350,0056D020, camera/client dimensions; all camera producers still partial |
| 13 | Lighting | PARTIAL | families set LIGHTING0; packed diffuse copied; original prelighting/native-light source open |
| 14 | Fog | MAPPED | linear vertex fog, sky palette, ViewDist/span and instance enable |
| 15 | Sky | PARTIAL |004B1180 +15 protected resources + network selection; final depth/order/local policy unobserved |
| 16 | Terrain/road | PARTIAL | common hierarchy/culling identified; chunks, LOD, road versus terrain resource ownership open |
| 17 | Vehicles | PARTIAL | body/four wheels/physics and ghost matrices; exact damage/glass/interior policy open |
| 18 | Foliage/transparency | PARTIAL | alpha-test128/GREATER and alpha queues; vegetation-specific provenance open |
| 19 | Particles | MAPPED | billboards/trails/shadows, dynamic layout and mode states; weather spawning still unknown |
| 20 | HUD/frontend separation | PARTIAL | immediate/deferred packet UI; semantic HUD/frontend ownership not exhaustive |
| 21 | Backbuffer/offscreen | PARTIAL | ordinary mapped path implicit backbuffer; D3DX RT/Cube reachability open |
| 22 | Depth lifecycle | PARTIAL | implicit auto-depth, clear and state/format sources; complete special resource use open |
| 23 | Device loss/reset | PARTIAL | cooperative HRESULTs/pre-reset destruction/post-reset cache; all slice recreation open |
| 24 | Transparent proxy plausible | CONDITIONAL | ordinary import + native forwarding; loader/identity/compatibility runtime audit required |
| 25 | Minimum wrapper surface | MAPPED | complete IDirect3D8/Device8 ABI; raw child forwarding initially, identity escape audit required |
| 26 | Reliable classification | PARTIAL | distinct particle/trail/shadow/UI/video/debug callers; world categories share draw tail |
| 27 | Modernization seams | MAPPED |26 feature ratings with observed seam and missing prerequisites; feasibility, not implementation |
| 28 | Runtime unknowns | MAPPED | runtime-handoff specifies scenarios, logs and PASS/FAIL |

## Reproduction

Run from master-rallye-re, with the pristine external EXE and installed dependencies:

```powershell
python modernization/renderer-recon/tools/scan_d3d8.py ../MRallye.exe --output modernization/renderer-recon/data
python -m compileall modernization/renderer-recon
python -m unittest discover -s modernization/renderer-recon/tests -v
git diff --check
```

For raw Ghidra queries use tools/ghidra_readonly.py in the installed bridge Python
environment, supplying --install, --java, --project, --binary and an output beneath
.analysis. README identifies the installations/project used. The Ghidra program
stored SHA must match the supplied exact retail image. No new project analysis,
saved function definitions or edits to existing research are required.

R-GFX2 remains unstarted. The next phase should validate transparent stock
forwarding and extend missing provenance; lighting/effects/camera changes must wait.
