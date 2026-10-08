# GS material and producer state

This document separates forced template bits, inherited state, source alpha and
live draws. The field interpretation follows the original PS2SDK GS definitions
([primary source](https://ps2dev.github.io/ps2sdk/gs__gp_8h_source.html)); register
values come from canonical ELF312610/31a518, not an SDK example.

## Vehicle material modes

| Field | mode3 body primary | mode3 secondary | mode20 glass primary | mode20 secondary |
|---|---|---|---|---|
|Primitive|Triangle strip|Triangle strip|Triangle strip|Triangle strip|
|IIP/TME|1/1|1/1|1/1|1/1|
|ABE / FGE|0 /1|1 /0|1 /1|1 /0|
|TEX0 TCC|0 RGB|0 RGB|1 RGBA|0 RGB|
|TEX0 TFX|0 MODULATE|1 DECAL|0 MODULATE|1 DECAL|
|ALPHA low/fixed word|44, inactive ABE|0000008000000029|44|0000006000000068|
|ZBUF ZMSK|0 writes allowed|1 masked|1 masked|1 masked|
|TEST ATE / ZTST|0 /2 GEQUAL|0 /2 GEQUAL|0 /2 GEQUAL|0 /2 GEQUAL|
|ZTE/DATE|Inherited|Inherited|Inherited|Inherited|
|TEX1 low OR|160|120 +computed K|120|120 +computed K|

TFX occupies bits35..36, TCC bit34. The actual secondary OR800000000 sets
TFX=1; describing both layers as MODULATE would be wrong. Likewise body stored
texture alpha is not a blend coefficient when TCC=0 and C=FIX.

ALPHA selectors use `(A-B)*C/128+D`:

| Word | A,B,C,D,FIX | Equation |
|---|---|---|
|44|Cs,Cd,As,Cd,0|Source-alpha interpolation when ABE=1|
|0000008000000029|Cd,zero,FIX,Cs,128|Cd+Cs|
|0000006000000068|Cs,zero,FIX,Cd,96|Cs*.75+Cd|
|00000050000000a8|Cs,zero,FIX,zero,80|Cs*.625, target generation first pass|
|0000003000000068|Cs,zero,FIX,Cd,48|Cs*.375+Cd, target generation second pass|

The actual mask operations are part of render-contract.json and312610 provenance.
Primary TEST preserves old &fff9c000 then OR41000; secondary preserves the same
mask then OR4040c. This establishes ATE=0/ZTST2, not the value of every inherited
bit. Source alpha, GS TCC/TFX, ABE, ALPHA, ATE, ZTE and ZMSK remain separate.

`311c50`/`312130` provide descriptor-derived TEX0 base/format/dimensions and TEX1
fields; `31e478`/`31e6a8` serialize primary/secondary state. Exact live texture base,
CLAMP, FRAME, TEXA, fog parameters, global glass ordering and inherited depth
enable must be captured or traced further. No complete live state is fabricated.

## Target-generation sprites

`31a518` emits a GIF tag with PRIM156: SPRITE6,TME1,ABE1,FST1,context1.
TEX0 uses TCC0/TFX1, source PSM argument2; target FRAME PSM argument2.
TEX1=61 (LCM1,MMAG1,MMIN3,MXL0); the numeric fields are the supported contract,
not a guessed mip-chain. TEST31000 has ATE0,ZTE1,ZTST1 ALWAYS. ZBUF is ORed
with132000000, masking depth writes. FRAME/XYOFFSET are restored afterwards.
Per-column CLAMP=source-width32 bounds, UV fixed-point corners and XYZ2 positions
form the actual copy geometry; no BITBLT local-to-local copy is substituted.

These sprite equations explain the nominal target mixture; GS16 quantization and
physical VRAM contents are not evaluated offline. Render-target/source stored
GXI alpha does not universally flow into the FIX equations.
