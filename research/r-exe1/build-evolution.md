# Cross-build evolution

## Method

Function pairing uses exact semantic strings/xrefs, call neighborhoods, decompiled behavior, data/corpus names, and (for selected matching functions) normalized mnemonic-sequence similarity. Similarity is `difflib.SequenceMatcher` over instruction mnemonic sequences extracted from Ghidra disassembly; operands, addresses, constants, and control-flow topology are not normalized into a full semantic signature. A high score supports a match but is not proof of equivalent behavior; a low score can reflect an actual rewrite or code-layout/control-flow differences. The correspondence JSON records which evidence applies to each pair. The values can be regenerated from the ignored function exports with `tools/scanner/r_exe1_function_metrics.py`.

## Build-to-build changes

### 8.4.1 → 9.3.1

- Image grows from 2,084,926 to 2,637,886 bytes; linker field remains 6.0, image base stays `0x00400000`, and both are PE32/D3D8 applications.
- Resource-root registration gains `DataVideo` by 9.3.1; the other root-registration structure is recognizable (mnemonic similarity 0.928).
- Progress's win-status prefix changes from `Progress/Won/` to `Progress/WinStatus/`; the setter/getter remain behaviorally similar at the semantic level (mnemonic similarity 0.899 on the mapped setter/getter candidate).
- UDP listener path remains semantically paired but changes more than later builds (0.874 mnemonic similarity); the same configured port remains 22,222.
- Course component registrations, including `gaRaceFinishAreaAI`, `gaRaceLineAI`, and `gaRaceSplitTimeAI`, remain represented by direct name xrefs.
- 9.3.1 still lacks the later `ddraw.dll` import, retail `data.sma` lookup literal, and `BuildData` string family.

### 9.3.1 → 9.10.0

- Image grows to 2,883,646 bytes. `ddraw.dll` appears in imports while D3D8 remains.
- The shader registry is a high-confidence structural rewrite: normalized mnemonic similarity is 0.447. The later registry has explicit alpha-test shader family names in addition to base, alpha, environment, noise, and particle families.
- Resource-root constructor, network listener, progress wrapper, and default parameter-broker registration remain near-identical by mnemonic sequence (1.000 for the mapped root/network/progress/broker pairs).
- The application setting registration sequence is substantially different (0.886 similarity to 9.3.1) and its inferred array entry stride changes from 0x1c to 0x94. This is a raw layout observation; the reason and full type are unresolved.
- No retail-style `data.sma` archive parser or `BuildData` command string family was found in 9.10.0.

### 9.10.0 → retail

- Image grows to 3,121,214 bytes; the PE32/D3D8 lineage continues. Debug records still name `MRallyeTNG.pdb` at a local development path, but the PDB is not present.
- Root registration and UDP listener bodies are identical by normalized mnemonic sequence; shader registry is 0.992 similar. These are stable late-lineage anchors.
- Retail adds the `data.sma` reader/index path, loose-file-first archive fallback, ZIP central-directory member reader, and retail-only `BuildData` strings/walker/callback registration.
- Progress WinStatus wrappers remain identical by mnemonic sequence. The WrongWay HUD constructors have a small retail delta (0.857 similarity); this does not identify the underlying detector.
- The app-setting routine changes substantially again (0.377 similarity); the decompilation's inferred entry stride returns to 0x1c after 0x94 in 9.10.0. Treat the layout clue conservatively until the registration container is typed.
- Audio, input, frontend, route, and vehicle-specific function counts grow, but raw count growth alone is not treated as feature proof.

## Stable anchors

1. Resource-root constructors: `004CECF0`, `00513E10`, `0052A320`, `00541640` (8.4.1, 9.3.1, 9.10.0, retail); 0.928 then 1.000 then 1.000.
2. UDP listener: `0042FBF0`, `00430F20`, `00431F50`, `00433240`; 0.874 then 1.000 then 1.000.
3. Default parameter broker registration: `00456590/00456650`, `00471380/00471440`, `00485550/00485610`, `0048FA10/0048FAD0`; stable constructor pair, including exact adjacent sequence match from 9.3.1 onward.
4. WrongWay HUD constructor pair: `0046ADE0/0046AEB0`, `00489080/00489150`, `0049ECB0/0049ED80`, `004A91E0/004A92B0`; constructor mnemonic sequence is identical through 9.10.0 and 0.857 similar to retail, with no detector semantics claimed.
5. Retail and demo progress wrappers are paired by their literal prefixes and matching typed accessor call neighborhoods.
6. GXM/GXI source loaders are paired by their distinctive `Reading GXM/GXI` strings, cache diagnostics, and caller/callee neighborhoods across all builds.

## Limits of historical inference

PE timestamp order is only approximate chronology; none of these observations implies that all code changed monotonically. Retail-only string absence in a demo can mean a feature was added, the literal moved, or the pathway is represented differently. Similarity values are comparable only under the stated mnemonic-only method. Build-specific addresses must be resolved again before any future instrumentation.
