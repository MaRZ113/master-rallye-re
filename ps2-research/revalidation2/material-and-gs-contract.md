# Material handlers and GS contract

## Callback output

The source PSM material contains `$shader(treeblend)`. The parser resolves the
shader token through the registered callback table; the runtime mode is not
inferred from the nearby string order. The callback at `0x003ae618` writes:

| Mesh offset | Value | Meaning in shared consumer |
|---:|---:|---|
| `+0x28` | 2 | treeblend material mode |
| `+0x2c` | 1 | render queue bucket |
| `+0x3c` | 1 | texture/cache creation option |
| `+0x40` | 0 | secondary option |
| `+0x44` | float32 `0.15` (`0x3e19999a`) | MIP/strip coefficient, not opacity |

The comparison callback at `0x003ae710` writes mode 6, bucket 0, texture
option 0 and coefficient `0.20` (`0x3e4ccccd`). Thus the PSM token
`$alphatest()` does not determine final treeblend GS alpha test by itself;
the selected shader handler and later common state producer do.

## Controlled GS fields

The original mode-state producer is in the `0x00312610` switch path. Its
mode-2 and mode-6 templates are byte-backed in TREEBLEND1's
`instruction-evidence.json`; relevant selected ranges were independently
decoded again in [instruction-probes.json](instruction-probes.json).
The masks preserve inherited bits rather than substituting zero.

| Register/field | `treeblend` mode 2 | `tree` mode 6 | Provenance |
|---|---|---|---|
| `GIF_TAG.PRIM` | triangle strip, IIP/TME/FGE, ABE=1 | same low controlled bits, ABE=0 | material mode write plus common tag template; other high/context bits inherited |
| `TEST.ATE` | 0 | 1 | mode-2/mode-6 template |
| `TEST.ATST/AREF/AFAIL` | inactive | GREATER / 64 / KEEP | mode templates |
| `TEST.ZTST` | GEQUAL selector | GEQUAL selector | selected field only |
| `TEST.ZTE` | inherited | inherited | not forced on by this mode evidence |
| `TEST.DATE/DATM` | inherited | inherited | unknown live values |
| `ALPHA` | A=Cs, B=Cd, C=As, D=Cd, FIX=0 | same stored selectors but ABE off | mode/shared template |
| `ZBUF.ZMSK` | 1, depth write masked | 0, depth write permitted | mode template |
| `FBA_1` | bit 0 set to 0 | bit 0 set to 0 | helper at `0x00341198` maps global `0x0042df10` to GS register `0x4a` (`FBA_1`) |
| `TEX0.TCC/TFX` | 1 / MODULATE | 1 / MODULATE | selected template fields; address/format remain dynamic |
| `TEX1.MMAG/MMIN` | 1 / 5 | 1 / 5 | selected fields; other mip fields partly inherited |
| `CLAMP` | authored clamp is retained; final descriptor values unknown | same | no selected live descriptor capture |
| `FRAME`, `TEXA`, `PABE` | inherited/unknown | inherited/unknown | no reliable selected live values |

The actual GS alpha equation is:

```text
Cout = (Cs - Cd) * As / 128 + Cd
```

This follows from A=Cs, B=Cd, C=As, D=Cd, FIX=0 with ABE enabled. The
equation is active for `treeblend`; it is inactive for `tree` because ABE is
off. `0x0042df10` is FBA, not PABE. Nearby words `0x0042dea0` and
`0x0042deb0` participate in state updates but their complete AD-register
identity and effect are not resolved here.

## Precision boundary

`ZMSK=1` is confirmed. A complete frame-wide depth story is not: ZTE is
inherited and the bucket ordering is only within one queue-drain invocation.
No per-foliage GS save/restore or global transparent pass has been proved.
Machine-readable field masks and inherited state are in
[render-contract.json](render-contract.json).
