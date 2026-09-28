# Course assets and corpus (R5T-A)

This page records the read-only course formats and the exact supplied corpus. It does not assign runtime meaning to source directive names or opaque compiled sections.

## Corpus inventory

| Build | Course folders | DX | TXT | GXM | DXT | matched RaceTest XML | matched HNT | SFL | FL | SF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Demo 8.4.1 | 2 | 2 | 2 | 2 | 114 | 2 | 1 | 0 | 3 | 2 |
| Demo 9.3.1 | 2 | 2 | 2 | 0 | 145 | 2 | 0 | 2 | 0 | 0 |
| Demo 9.10.0 | 2 | 2 | 2 | 0 | 178 | 2 | 1 (empty) | 2 | 0 | 0 |
| Retail | 36 | 36 | 36 | 0 | 3,998 | 36 | 36 | 36 | 0 | 0 |

Counts and per-file hashes are in [`course-corpus.json`](../research/r5t_a/course-corpus.json). Retail has 41 RaceTest XML files and 36 HNT files in total; 36 are exact course-folder matches. The inventory also records 161 developer/test asset-name matches, including boinds, collisiontests, gordonTrack, RussiaTurkey1, RaceLineExample, and the named BSP testers.

## Resource relationships

Retail course folders pair by exact normalized course name with `DataScene/RaceTest/<course>.xml`, `DataScene/RaceTest/<course>.hnt`, and `DataScene/ICont/<course>.sfl`. HNT `Model` and `Texture` entries are resolved against exact case-insensitive paths under `DataGx`; the resolver does not guess from basenames.

Across the 36 retail HNT manifests, the parser finds 36 Model entries and 2,807 Texture entries. There are 2,842 resolved references, one unresolved reference, and no ambiguous paths. `misc/water/watersurface3.dxt` is shared by 33 course manifests. The unresolved reference is `Texture [course\turkey_s2_flip\pathesport-tga]` in `Turkey_s2_flip.hnt`. These are declared dependencies; runtime necessity has not been tested.

Each retail course folder contains one DX and one TXT sidecar. The existing sidecar parser accepts all 42 available course TXT files across the four builds. The 3,998 retail DXT files are inventoried with hashes; Blender preview reuses the existing DXT and material code.

## Format timeline

France1 and Italy1 are present in all four corpus snapshots. Their DX revisions are 127 in Demo 8.4.1, 131 in Demo 9.3.1, and 135 in Demo 9.10.0 and retail. The late revision-135 course render grammar is validated on both Demo 9.10.0 tracks and all 36 retail courses. The 8.4.1 and 9.3.1 draw grammars remain outside the course importer.

Both tracks have 20-byte-header SFL resources from Demo 9.3.1 onward. France1 and Italy1 SFL dimensions/header bytes are unchanged between 9.3.1, 9.10.0, and retail, while payload hashes change from 9.3.1 to 9.10.0 and then match retail exactly. Demo 8.4.1 has historical FL/SF files; each scanned candidate has a 20-byte header and four bytes per cell. A direct semantic FL/SF-to-SFL identity is not established.

The two available Demo 8.4.1 course GXM files have 32-byte headers and a bounded opaque 16-byte-stride bank. Their trailing node tables are now parsed against paired TXT: France1 has 2,322 nodes and Italy1 1,117; all names, classes, unknown-node child counts, and mesh spans match. Source transforms and geometry arrays remain undecoded. See [`docs/formats/gxm-course.md`](formats/gxm-course.md).

## Runtime compatibility observation

The project owner manually observed retail course packages loading in Demo 9.10.0 when required files were supplied or selected. The same newer retail packages produced an empty/void world in Demo 9.3.1 and Demo 8.4.1. This is `CONFIRMED_BY_RUNTIME` project-owner evidence. The responsible resource or combination remains unknown; the compatibility test plan is in [`research/r5t_a/compatibility-test-plan.md`](../research/r5t_a/compatibility-test-plan.md).

## 8.4.1 source recooked by Demo 9.10.0

The project owner separately reports that the original Demo 9.10.0 runtime
cooker can rebuild old 8.4.1 France1/Italy1 source into revision-135 courses
that load and run in the 9.10.0 runtime, with AI working. The recooked courses
retain old start/grid behavior; visual issues remain. This is
`CONFIRMED_BY_RUNTIME` owner evidence and is distinct from swapping retail
resources into older demos. The trigger is now reproduced: launch the 9.10.0
runtime and select France1 after removing the cached DX and DXT files in an
isolated course copy. Two forced rebuilds produced validated rev135 DX; DX
render prefixes vary, while all 172 non-DX resource hashes and the raw tag100
payload hash match across runs. The documented trigger, logs, output hashes,
and limitations are in [`docs/course-cooker.md`](course-cooker.md) and
[`research/r5t_b/cooker-baseline.json`](../research/r5t_b/cooker-baseline.json).

See [`docs/course-importer.md`](course-importer.md), [`docs/formats/dx-course.md`](formats/dx-course.md), and the machine-readable reports under [`research/r5t_a`](../research/r5t_a/).
