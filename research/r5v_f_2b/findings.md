# R5V-F.2b — retail-native Mercedes cook proof

## Current result

**PREPARED; RUNTIME COOK NOT RUN.** The phase has a hash-locked source, an
isolated retail runtime copy, and an ID26-only cook-harness candidate. Retail
itself contains the GXM→DX cache path documented in F.2a. The remaining gate
is a human Vehicle Select run that proves the newly staged `complete.gxm`
actually produces a revision-135 `complete.dx`.

No canonical retail executable, retail `Data.sma`, demo asset, or source file
was modified. No runtime cook, Practice load, Cook B, cache-only test, or final
Mercedes P0/P1 test has been run.

## Locked inputs

- Source: demo-8.4.1 `DataGx/Vehicles/Copy of Mercedes`; 59 root files:
  3 GXM, 25 GXI, 25 DXT, 3 TXT, and 3 legacy DX files. Exact per-file hashes
  are in `research-output/r5v_f_2b/source-manifest.json`.
- GXM SHA-256: `car.gxm`
  `ff238b391da254ef10904bb59b7430d17e1000cfceec8821d61f98b7158993fe`;
  `complete.gxm`
  `95caced8716239d4fa093fc0320e737e13dc1eedc8b649456d4cc89444fe354d`;
  `wheel.gxm`
  `74bfb66a0b411cb3814bbc16f4c672bc9d42b5b7b7e7e7415686ba805ac517ea`.
- Retail `MRallye.exe`: SHA-256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Retail `Data.sma`: SHA-256
  `03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f`.
- Retail archive index contains **zero** `DataGx/Vehicles/Mercedes/` members.
  The loose cook tree therefore starts without an archive-provided Mercedes
  cache that could mask a missing loose `.dx`.

The selected folder also contains an adjacent `lpha` directory with 44 files:
2 GXM, 19 GXI, 19 DXT, 2 TXT, and 2 legacy DX. Its GXM references use the
separate `MercedesAlpha` path family. It is hash-inventoried but not copied
into the Mercedes cook harness. The selected root GXM references use
`Vehicles/Mercedes/`.

The DXT round-trip validator passed **44/44** source DXT samples across the two
inventoried source families, with zero header or payload differences. Only the
25 root Mercedes DXT files were staged for this phase.

## Cook harness

The generated isolated candidate is
`research-output/r5v_f_2b/runtime-cook/MRallye.exe`, SHA-256
`a6a5f0590405e1a2051ef21f2be58197857e72f4a651506627c8966083a21d91`. It uses
the fixed `mercedes-cook-harness` profile at ID26 / T1 local7. The original
27-record expansion, capacities T1=8, T2=7, T3=12, and ID25 Trooper profile
remain intact. The profile preserves the red F.1 race-marker canary and the
donor stats; it changes the owned internal/resource name to `Mercedes` to
trigger the retail resource loader. It is not final Mercedes presentation or
gameplay data.

Compared with the F.1 cleanup profile, the 72-operation patch has only two
different operation records: the code-cave payload and derived `.text`
VirtualSize. The payload shrinks from 396 to 393 bytes because `Mercedes` is
shorter than `Landcruiser`; the other 70 operation records match. The F.1
profile remains the default and its existing tests still pass.

The runtime tree contains byte-identical copies of retail `Data.sma`, the
candidate executable, retail `DataAudio`/`DataVideo`, 3 GXM files, and 25
historical DXT files. It has 25 separate copied GXI files under the authoring
root. No legacy `.dx` was staged in the runtime vehicle directory. The
candidate rebuild check passed; this is static patch validation only.

## Authoring path and cooker evidence

The byte-identical GXM files refer to
`D:/projects/MRallyeTNG/DataGx/Vehicles/Mercedes/`. The exact Windows path was
absent at preflight. `CHECK_AUTHORING_PATH.ps1` confirmed that state without
writing anything. The safe setup helper is ready to create a Junction to
`research-output/r5v_f_2b/authoring-root/Mercedes`; the Junction has **not** yet
been created.

F.2a's static chain is reused: retail `FUN_0053C3F0` chooses `.gxm`/`.dx`,
reaches the GXM parse/build path and writer `FUN_00551260`, which emits DX
revision `0x87` (135). The texture route separately reads GXI and writes DXT.
Raw exports and assembly/P-code from F.2a remain the static source. No runtime
message has yet proven the source path, a cache miss, or a new cache write.

## Ghidra provenance

F.2a used the existing Ghidra 12.1.4 PUBLIC installation at
`D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\ghidra_12.1.4_PUBLIC`.
That is the newest installed version on D: and the version required by the
repository instructions. The bridge YAML had been pointing to the older
`C:\Useful\ghidra_12.0.4_PUBLIC`; `GHIDRA_INSTALL_DIR` was unset. This phase
updated only the bridge YAML `install_dir` to the D: 12.1.4 path. The existing
bridge and project were not replaced or migrated. This phase did not launch the
bridge or generate new Ghidra exports; it reused the F.2a raw evidence.

## Historical cooker research checked

The bounded beta review found the existing `R-COOKER` closeout at commit
`0fb0a6ff6d89f2fbca5f6600578a2614b9b8f91a`, files
`research/r-cooker-closeout/final.md` and
`research/r-bridge/r-bridge2-demo-910-bridge.md`. R-COOKER's production path
converts supported revision-131 DX to revision 135; it does not perform this
phase's retail GXM→DX cache cook. The bridge report concerns a separate old
demo and has no exact Copy-of-Mercedes input/output proof. Its findings are
historical context only; no beta code or asset was copied into this phase.
Existing Vehicle SDK parsers and R4G collision tools remain the planned
validators after human cooking.

## Next gate

Follow `research-output/r5v_f_2b/HUMAN_COOK_INSTRUCTIONS.txt`: create the
verified Junction, launch the isolated candidate, select T1 local7, capture
the complete preview cook, and stop after `complete.dx` appears. Codex must
validate that file before the Practice car/wheel cook is started.
