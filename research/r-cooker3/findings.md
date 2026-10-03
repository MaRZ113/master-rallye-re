# R-COOKER3 — retail-native source cooker

## Current result

**R-COOKER3 V1 ORCHESTRATION IMPLEMENTED; MERCEDES T1/T2/T3 CLOSED.** The
retail runtime can produce the supported Mercedes model DX from its GXM source
in the exact tested build/harness. T1 established that the ordinary DXT cache
miss path does not regenerate a missing DXT from GXI; V1 therefore resolves
textures separately through validated DXT reuse or the existing offline GXI
encoder. The tool prepares isolated human-assisted native-cook jobs, validates
their outputs, and assembles cache-only packages. It is not a general GXM
cooker and does not launch the game or create Junctions itself.

The new evidence comes from the separate Mercedes source-cook work. The
unique source is Demo 8.4.1 `DataGx/Vehicles/Copy of Mercedes`, not the
same-named folder whose car/wheel sources alias LandCruiser. Retail cooked
its `complete.gxm`, `car.gxm`, and `wheel.gxm` to revision-135 DX. Fresh Cook
A and Cook B outputs were byte-identical for all three roles. The six
role-specific output hashes and source identities are recorded below.

| Role | GXM SHA256 | Retail DX SHA256 | Cook A/B |
|---|---|---|---|
| complete | `95caced8716239d4fa093fc0320e737e13dc1eedc8b649456d4cc89444fe354d` | `ddad0c7b13be70388a60a541255eaaf3af7f9b1815f5aa02f2b60050862dc28b` | byte-identical |
| car | `ff238b391da254ef10904bb59b7430d17e1000cfceec8821d61f98b7158993fe` | `5ec5f7480ddfc1380131a012b300a4cdeb28b869a1668b6f8bbe97210893ff44` | byte-identical |
| wheel | `74bfb66a0b411cb3814bbc16f4c672bc9d42b5b7b7e7e7415686ba805ac517ea` | `8707d887a75c452eb739775e21f94109521d9fc6be07726cee28a8e911c590ff` | byte-identical |

The native retail rebuild of `car.dx` contains a structurally valid tag101.
Its core hull geometry/topology matches the legacy revision-127 Mercedes
control within measured float drift. About 36 bytes in secondary face
descriptor lists differ; their semantics remain unresolved. The retail cook
can emit those bytes itself, but this is not proof that they are irrelevant or
that an offline writer can reproduce them.

The three runtime oracles now close as follows:

| Oracle | Result | Evidence |
|---|---|---|
| T1 missing `underdash-tga.dxt` while source GXI was available | Retail reported the missing DXT; no GXI read or cached DXT write followed | `CONFIRMED_BY_RUNTIME` negative result for this ordinary cache-miss path |
| T2 cache-only Mercedes | `complete.dx`, `car.dx`, `wheel.dx` and 25 Mercedes DXT loaded; no Mercedes authoring reads or `D:\projects\MRallyeTNG` access | `CONFIRMED_BY_RUNTIME` |
| T3 collision | Solid barrier response, no gross offset/pass-through | `CONFIRMED_BY_RUNTIME` |
| T3 external/internal damage | Both observed working | `CONFIRMED_BY_RUNTIME` |

The T2 log also contains unrelated global GXM activity (an empty `.gxm` path
and a GPS test resource). The negative source assertion is scoped to Mercedes.
Glass breakage is not expected for this early Mercedes model and is not a
failure of collision/damage cooking.

Mercedes Cook A and Cook B are byte-identical for `complete`, `car`, and
`wheel` for the exact GXM source, retail build, and harness. These hashes were
rechecked from the T2 cache manifest; they do not establish determinism for
arbitrary GXM inputs.

This complements rather than replaces R-COOKER2:

```text
supported rev131 vehicle DX -> project upgrader -> retail-compatible rev135 DX
GXM/GXI source -> original retail runtime cooker -> rev135 DX / DXT cache
```

The retail-native path is directly runtime-evidenced only for this exact
Mercedes source and test environment. R-COOKER2 remains the independent
supported rev131-to-rev135 strategy.

## Original oracle workspaces (historical preparation record)

Byte-verified isolated copies are under the ignored current-branch location
`.research-output/r-cooker3/`:

- `oracle-t1/runtime/`: the existing `mercedes-cook-harness` runtime-cook
  workspace, copied without changing any file (145 files, 362,593,788 bytes).
- `oracle-t1/results/`: prepared for logs and captured texture outputs; the
  frozen `underdash-historical.dxt` baseline is already present and hash-checked.
  `underdash-preflight-comparison.json` records that the historical DXT parses
  and matches the offline encoder output. That preflight alone was not a runtime
  verdict (`RUNTIME_PENDING` at that stage); the later T1 runtime result is the
  completed negative cache-miss observation recorded above.
- `source-bridge/`: a copy of the 25 hash-locked Mercedes GXI files, their
  source manifest, and the fixed Junction setup/check/remove helpers.
- `oracle-t2-t3/runtime/`: the prepared cache-only runtime package (142
  files, 362,138,859 bytes). Its Mercedes model directory has exactly three
  revision-135 DX and 25 DXT files; no GXM/GXI/TXT are present.
- `oracle-t2-t3/results/`: prepared for T2/T3 logs and runtime observations.
- `oracle-t2-t3/cache-manifest.json`: expected hashes and package invariants.

Each copied runtime tree was compared file-by-file and hash-by-hash with its
read-only source workspace. The old authoring Junction is currently absent.
All new test logs/results belong under `.research-output/r-cooker3/` in this
branch; no files in the source or R5V worktrees were modified.

## Historical test plan (closed)

1. **T1 texture cache miss:** prove one retail GXI-to-DXT write from a missing
   cache entry. Candidate: `underdash-tga`, referenced by parsed
   `complete.dx` and the selected source GXM.
2. **T2 cache-only portability:** preview and load the three cooked DX plus
   25 DXT with the authoring Junction absent and no Mercedes GXM/GXI/TXT in
   the runtime model directory.
3. **T3 collision and damage:** using the same cache-only harness, observe
   normal gameplay collision and damage independently. This does not resolve
   secondary descriptor semantics.

The original preparation plan is retained in [the Mercedes oracle record](mercedes-oracles.md).

The implemented strategy selection and validation layers are summarized in
[strategy-matrix.md](strategy-matrix.md) and [validation-model.md](validation-model.md).
The current CLI and package path are documented in [architecture.md](architecture.md).

## Scope boundary

No general retail cooker is claimed until more GXM families pass controlled
native-cook qualification. No GXM rewrite, retail DXT cache-miss regeneration,
executable patch, Vehicle Composer integration, or roster expansion is part
of this phase. R-DEMO2 collision findings remain intact: native retail cooking
provides usable tag101 for the tested package, while the independent offline
secondary-descriptor producer remains unresolved.
