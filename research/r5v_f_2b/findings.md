# R5V-F.2b — retail-native Mercedes cook proof

## Current result

Retail DebugView proves native GXM-to-DX cache cooking for complete, car and wheel. Each output is revision 135 and passes strict modern parsing. Car and wheel render semantics match the selected demo-8.4.1 Copy of Mercedes rev127 files except for tiny precision/color quantization.

Cook A is frozen for a determinism comparison. It combines complete.dx from the first capture with car.dx and wheel.dx from the later capture; complete was loaded from cache in that later session. It is not one three-role launch. All three files and the matching DXT hashes are recorded in research-output/r5v_f_2b/cook-a/hashes.json, with immutable DX copies under cook-a/cache_snapshot/.

The authentic Mercedes car tag101 passes structural checks: finite, in-range, closed, Euler-2, convex, and zero-edit serializer identity. Core hull geometry/topology matches the rev127 Mercedes control within measured float drift. Thirty-six bytes in secondary face descriptors differ, and their runtime semantics remain unresolved. This is the remaining collision comparison gate; no donor collision was substituted.

All 25 non-null texture dependencies resolve, parse, match the locked source hashes, and appear in runtime load logs. The junction verifier bug is fixed in source tools and regression-tested. The exact Junction remains for Cook B.

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
`D:/projects/MRallyeTNG/DataGx/Vehicles/Mercedes/`. The validated Junction at
that path targets the isolated
`research-output/r5v_f_2b/authoring-root/Mercedes` copy. Runtime evidence shows
the retail process reading the staged `complete.gxm` from its isolated runtime
tree and writing the DX cache without rewriting GXM bytes. The log does not
contain a `Reading GXI` event; because the validated historical DXT files were
staged, this cook does not by itself prove a GXI-to-DXT source conversion.

F.2a's static chain is confirmed by runtime messages: the retail cache reports
the model missing/stale, reads `vehicles\\mercedes\\complete.gxm`, builds
`vehicles\\mercedes\\complete`, saves
`DataGx/Vehicles/Mercedes/complete.dx`, and reloads that DX. The output SHA-256
is `ddad0c7b13be70388a60a541255eaaf3af7f9b1815f5aa02f2b60050862dc28b`.
The rev127 DX has 18 draw records; the bounded raw draw scan consumed all
1,342 bytes. All draw cores and texture-slot tuples match the rev135 output by
index. The detailed line references and parser output are in
`research-output/r5v_f_2b/cook-a/complete-cook-validation.md` and `.json`.

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

Run research-output/r5v_f_2b/COOK_B_INSTRUCTIONS.txt to recook all three roles from absent DX caches. Compare each result with the frozen Cook A SHA-256 values. Keep the Junction until that comparison is complete. The secondary tag101 descriptor meaning and cache-only portability remain open; no final Mercedes acceptance is claimed.
