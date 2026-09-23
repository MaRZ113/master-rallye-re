# R4D.1 corpus hardening

Run `py -3 tools/scanner/material_hardening.py "..\Data.sma_unpacked\DataGx\Vehicles" --output research/r4d_1/corpus-hardening.json`. It reparses local DX/TXT/DXT sources; JSON records counts and exceptions, no game bytes.

**CONFIRMED_BY_CORPUS:** 1,478/1,478 draws satisfy `unknown_0x24 = (slot0 != Null ? 1 : 0) | (flags_0x20[2] != 0 ? 2 : 0) | (slot1 != Null ? 4 : 0)`. Mask distribution: 1=21, 2=2, 3=363, 5=151, 6=3, 7=938. Slot presence (1=present): 000=2, 010=3, 100=384, 110=1,089. Slot 2 is Null throughout this vehicle corpus.

**CONFIRMED_BY_CORPUS:** flag byte 0 matches uniquely matched sidecar slot-0 UsesAlpha in 1,364/1,365 draws: false/false 1,141; true/true 223; false/true 1. Exception: Kamaz/complete.dx draw 19, lamp1-tga + glass-tga, Material #62; binary flag 0, sidecar UsesAlpha=Yes. Flag byte 2 controls mask bit 0x2 in 1,478/1,478.

| Flag byte | Value distribution |
|---|---|
| 0 | 0: 1,241; 1: 237 |
| 1 | 0: 1,478 |
| 2 | 0: 172; 1: 1,306 |
| 3 | 0: 2; 1: 1,476 |

Among uniquely matched alpha-enabled draws, byte2=0 names are mostly brake/glow-like (25 draws); byte2=1 names are mostly glass/windscreen/light-like (198). Names support grouping, not render modes. Byte 3 is zero only for IceCream/car.dx draw 3 and IceCream/complete.dx draw 3, both with no texture; its loader destination is +0x21 and its precise pass effect remains unknown.

The alpha table counts **2,395 sidecar texture entries inside uniquely matched physical draw/material bindings**, including repeated resource bindings. It does not count 2,395 physical draws.

| HasAlpha | UsesAlpha | DXT alpha <255 | Texture entries |
|---|---|---|---:|
| No | No | No | 2,114 |
| Yes | Yes | Yes | 223 |
| Yes | No | Yes | 48 |
| Yes | No | No | 6 |
| No | Yes | No | 4 |
