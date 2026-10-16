# PS2 GS state audit

This is a verification of the existing TREEBLEND1 result and its proof limits;
it is not a new REA disassembly. The canonical PS2 ELF was outside the
configured REA backend's R5900 support.

| Material | Handler mode | Queue | Alpha test | Alpha blend | Blend model | Depth test | Depth write |
|---|---:|---:|---|---|---|---|---|
| `tree` | 6 | 0 | `A > 64`, fail `KEEP` | Disabled | inactive | `GEQUAL` selected; enable inherited | Z writes allowed (`ZMSK=0`) |
| `treeblend` | 2 | 1 | Disabled | Enabled | `(Cs - Cd) * As / 128 + Cd` | `GEQUAL` selected; enable inherited | masked (`ZMSK=1`) |

The prior `render-contract.json` stores explicit masks and decoded fields for
the handler writes. The values below distinguish direct handler writes from
state inherited by the packet:

| GS field | `tree` | `treeblend` | Scope |
|---|---|---|---|
| GIF `PRIM` | Triangle strip, textured | Triangle strip, textured | Selected template/path |
| `TEST.ATE` | 1 | 0 | Written by mode handler |
| `TEST.ATST/AREF/AFAIL` | GREATER / 64 / KEEP | Inactive while ATE=0 | Mode-specific |
| `TEST.ZTST` | GEQUAL | GEQUAL | Selected by handler |
| `TEST.ZTE` | Inherited | Inherited | Not supplied by mode handler |
| `ALPHA` selectors | A=Cs, B=Cd, C=As, D=Cd; inactive | Same selector tuple; active with ABE | Exact formula from GS selectors |
| GIF `ABE` | 0 | 1 | Handler/template state |
| `ZBUF.ZMSK` | 0 | 1 | Handler write |
| `TEX0.TFX/TCC` | Modulate / texture alpha enabled | Modulate / texture alpha enabled | Relevant path/template |
| `FRAME`, `PABE`, `TEXA` | Inherited | Inherited | Unknown live values |

The equation is based on the PS2 GS alpha coefficient convention. It is not
numerically identical to ordinary D3D8 `SRCALPHA` interpolation. The
contributing runtime `As` after texture/vertex combine, TEXA conversion,
PABE, and frame context were not captured. The alpha values stored in a GXI
file are not themselves proof of the final coefficient.

No claim of pixel-exact PS2 rendering is made. The current PC pilot uses
D3D8 `SRCALPHA` / `INVSRCALPHA` as an approximation and retains the PC texture.
