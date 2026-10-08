# PS2-WATER1 findings

**PS2-WATER1 STATUS: COMPLETE at the bounded static RE level.** Runtime
validation is **NOT_PERFORMED**. The two primary questions now have an
asset/executable-backed answer; actual frame visibility, inherited GS state
and live VU residency remain separate capture requirements.

Turkey3 has authored visual `puddle` meshes in the landscape scene tree:
17 mesh records, 51 strips, 745 non-suppressed nondegenerate source triangles,
537 distinct XYZ positions and 11 diagnostic edge-connected components.
Their surfaces have no triangle/vertex counterpart in the validated PC
landscape draw corpus. A separate all-PC-triangle height test also finds no
coplanar centroid at a 0.001-world-unit tolerance. This is
**EXTRA_PS2_VISUAL_GEOMETRY_IN_SCANNED_COMPILED_LANDSCAPE**, not just an extra
material string. It does not prove that every source triangle is visible.

The controls prevent generalizing that finding: France1's 3,586 water-related
triangles and Italy_S1's 1,329 triangles all match PC geometry in the same
coordinate system. Italy changes shader classification from PC `water` to
PS2 `puddle` on shared surfaces.

`391690 -> 3a6c58` selects real mesh modes: `puddle=9`, `water=10`,
`waterfall=waterall=19`. The latter spellings have separate registrations and
handlers with the same material result. Water/puddle preserve the course's
first texture and add `CommonTextures/watersurface2`. Puddle updates cached
UVs per frame; ordinary water's auxiliary frame callback is empty. The traced
callbacks write UV/color, not XYZ. There is no newly generated puddle plane
in this path.

The second puddle layer is particularly informative: TCC=0, alpha blending
`Cs*56/128+Cd`, depth writes masked. Ordinary water instead has TCC=1 and
`(Cs-Cd)*As/128+Cd`. Texture alpha, GS alpha test and blending are different
contracts. The traced mode setup disables alpha testing; ZTE remains inherited.

The four chains below use **CONFIRMED_BY_BOTH** for byte layout plus matching
ELF consumer, **CONFIRMED_BY_EXE** for CPU flow, and explicitly bounded static
VU decoding. No arrow asserts an independently observed runtime frame.

```mermaid
flowchart LR
  A[PSM node-2 material bytes] -->|390ba8 / 390d98; BOTH| B[Authored shader argument]
  B -->|391690 / 3a6c58; EXE| C[Interned shader registry]
  C -->|3aea50 / 3ae9a0 / 3ae800 / 3ae8d0; EXE| D[mesh+28: 9 / 10 / 19]
```

```mermaid
flowchart LR
  A[Classified node-2 mesh] -->|391d38; BOTH| B[mesh+74 strip vector]
  B -->|3a5598 / 3a5560; BOTH| C[Shared model vertices]
  C -->|3900f0 / 31f4e0; BOTH| D[Authored visual source surface]
  D -->|UNKNOWN LINK: selected live instance/LOD and occlusion| E[Visible frame surface]
```

```mermaid
flowchart LR
  A[Water mesh and two resource names] -->|3714e0 / 2fd7d0; EXE| B[mesh+dc / +e4 texture handles]
  A -->|31f4e0 and auxiliary callbacks; EXE| C[64-byte vertex/UV/color records]
  B -->|31cd98 / 311c50 / 312130 / 312610; EXE| D[Two GS state templates]
  C -->|31d7c8 / 31e010; EXE| E[VIF geometry and frame DMA chain]
  D -->|31e478 / 31e6a8; EXE| E
  E -->|316b88 / 30ea80; EXE| F[VIF1 DMA TADR and CHCR start]
  U[317208 CALL to 442170: upload producer proved] -->|MPG addresses and static decode| V[Embedded VU state/strip/XGKICK contract]
  F -->|UNKNOWN LINK: independently captured live residency/state| V
  V -->|Static XGKICK decode; runtime NOT_PERFORMED| G[GIF / GS]
```

```mermaid
flowchart LR
  A[Turkey3: puddle material and 745 source faces] -->|Identity coordinates validated by 22679 ordinary positions; BYTES| B[All 42237 PC draw triangles]
  B -->|Corner-permutation test plus independent height projection; BYTES| C[0 triangle matches; 0 coplanar centroid hits]
  C -->|Bounded compiled landscape conclusion| D[Extra authored PS2 visual surfaces]
  D -->|UNKNOWN LINK: controlled visible-frame correlation| E[User-observed extra PS2 puddles]
```

Read [Turkey3 delta](turkey3-delta.md), [material contract](water-material-contract.md),
[geometry](psm-water-geometry.md), [draw pipeline](draw-pipeline.md),
[validation](validation.md) and [final report](final-report.md). Compact
original-data facts are in `case-evidence.json`, `texture-evidence.json` and
`elf-functions.json`; full extracted content remains ignored.
