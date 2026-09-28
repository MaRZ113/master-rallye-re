# Course TXT and source-label analysis (R5T-A)

The existing TXT sidecar parser was run without format-specific relaxations. Source name strings and directive-bearing lines are preserved verbatim in JSON.

| Build | Course | Parse | Materials declared/parsed | Mesh entries | Mesh span | Directive-bearing lines |
|---|---|---|---:|---:|---:|---:|
| Demo 8.4.1 | France1 | parsed | 121/121 | 2283 | 61917 | 86 |
| Demo 8.4.1 | Italy1 | parsed | 66/66 | 1082 | 47377 | 22 |
| Demo 9.3.1 | France1 | parsed | 150/150 | 2517 | 60650 | 86 |
| Demo 9.3.1 | Italy1 | parsed | 90/90 | 1102 | 46786 | 22 |
| Demo 9.10.0 | France1 | parsed | 158/158 | 2520 | 64105 | 81 |
| Demo 9.10.0 | Italy1 | parsed | 100/100 | 1098 | 46680 | 22 |
| Retail | France1 | parsed | 127/127 | 2527 | 64101 | 49 |
| Retail | France2 | parsed | 148/148 | 4871 | 72400 | 49 |
| Retail | France_M | parsed | 189/189 | 4108 | 75830 | 55 |
| Retail | France_S1 | parsed | 114/114 | 3908 | 69816 | 39 |
| Retail | France_S2 | parsed | 165/165 | 3964 | 70207 | 49 |
| Retail | France_W | parsed | 116/116 | 4090 | 73123 | 40 |
| Retail | France_W_flip | parsed | 118/118 | 4086 | 73123 | 40 |
| Retail | Italy1 | parsed | 100/100 | 1098 | 46687 | 22 |
| Retail | Italy2 | parsed | 88/88 | 2360 | 55299 | 25 |
| Retail | Italy3 | parsed | 79/79 | 3643 | 67391 | 32 |
| Retail | Italy_M1 | parsed | 95/95 | 1965 | 54968 | 23 |
| Retail | Italy_M1_flip | parsed | 95/95 | 1965 | 54968 | 23 |
| Retail | Italy_M2 | parsed | 79/79 | 3702 | 72744 | 29 |
| Retail | Italy_S1 | parsed | 89/89 | 1417 | 51695 | 24 |
| Retail | Italy_S2 | parsed | 92/92 | 2045 | 56735 | 23 |
| Retail | Italy_S3 | parsed | 116/116 | 3530 | 64419 | 46 |
| Retail | Italy_S3_flip | parsed | 116/116 | 3538 | 64695 | 46 |
| Retail | Italy_S4 | parsed | 76/76 | 3342 | 77415 | 31 |
| Retail | Italy_W1 | parsed | 88/88 | 1564 | 55721 | 24 |
| Retail | Italy_W2 | parsed | 75/75 | 3239 | 75943 | 29 |
| Retail | Spain1 | parsed | 64/64 | 206 | 32362 | 20 |
| Retail | Spain2 | parsed | 79/79 | 1107 | 57435 | 6 |
| Retail | Spain_M | parsed | 63/63 | 838 | 47978 | 20 |
| Retail | Spain_S1 | parsed | 63/63 | 732 | 52473 | 12 |
| Retail | Spain_S1_flip | parsed | 63/63 | 732 | 52473 | 12 |
| Retail | Spain_S2 | parsed | 68/68 | 612 | 51301 | 18 |
| Retail | Spain_W | parsed | 69/69 | 733 | 56374 | 14 |
| Retail | Spain_W_flip | parsed | 69/69 | 733 | 56374 | 14 |
| Retail | Turkey1 | parsed | 138/138 | 2743 | 44661 | 80 |
| Retail | Turkey2 | parsed | 100/100 | 1650 | 53721 | 38 |
| Retail | Turkey3 | parsed | 92/92 | 2574 | 42043 | 43 |
| Retail | Turkey_m | parsed | 216/216 | 3062 | 64654 | 145 |
| Retail | Turkey_s1 | parsed | 119/119 | 2528 | 63401 | 59 |
| Retail | Turkey_s2 | parsed | 115/115 | 2704 | 58429 | 64 |
| Retail | Turkey_s2_flip | parsed | 116/116 | 2704 | 58429 | 64 |
| Retail | Turkey_w | parsed | 146/146 | 1867 | 48690 | 85 |

## France1 and Italy1 source strings

### Demo 8.4.1 — France1

Directive-family counts (a line may contain more than one token): `$bsp` 1, `$draw` 1, `$grnd` 104, `$grndu` 10, `$grndv` 3, `$landdb` 1, `$nodraw` 1, `surface_dirt_hard` 3, `surface_dirt_hardnoise` 3, `surface_grass_hard` 9, `surface_grass_hardnoise` 9, `surface_gravel_hard` 1, `surface_gravel_hardnoise` 1, `surface_mud_hard` 2, `surface_mud_hardnoise` 2, `surface_stones_hard` 8, `surface_stones_hardnoise` 8, `surface_tarmac` 8, `surface_tarmacnoise` 8

- `Material number [ 0] has name [$grnd:surface_tarmac$grnd:surface_tarmacNoise Pass]`
- `Material number [ 1] has name [$grnd:grass_hard$grnd:grass_hardNoise Pass]`
- `Material number [ 2] has name [$grnd:surface_grass_hard$grnd:surface_grass_hardNoise Pass]`
- `Material number [ 3] has name [$grnd:surface_gravel_hard$grnd:surface_gravel_hardNoise Pass]`
- `Material number [ 4] has name [$grnd:surface_dirt_hard$grnd:surface_dirt_hardNoise Pass]`
- `Material number [ 5] has name [$grnd:surface_dirt_hard$grnd:surface_dirt_hardNoise Pass]`
- `Material number [ 6] has name [$grnd:surface_dirt_hard$grnd:surface_dirt_hardNoise Pass]`
- `Material number [ 7] has name [$grnd:surface_tarmac$grnd:surface_tarmacNoise Pass]`
- `Material number [ 8] has name [$grnd:surface_tarmac$grnd:surface_tarmacNoise Pass]`
- `Material number [ 9] has name [$grnd:surface_tarmac$grnd:surface_tarmacNoise Pass]`
- `Material number [11] has name [$grnd:surface_stones_hard$grnd:surface_stones_hardNoise Pass]`
- `Material number [12] has name [$grnd:surface_stones_hard$grnd:surface_stones_hardNoise Pass]`
- … 74 additional exact lines are retained in JSON.

### Demo 8.4.1 — Italy1

Directive-family counts (a line may contain more than one token): `$bsp` 1, `$draw` 1, `$grnd` 24, `$grndu` 12, `$landdb` 1, `$nodraw` 1

- `Material number [29] has name [$grnd:dirt_soft$grnd:dirt_softNoise Pass]`
- `Material number [30] has name [$grndu:50:grass_soft_wet:dirt_soft$grndu:50:grass_soft_wet:dirt_softNoise Pass]`
- `Material number [31] has name [$grndu:50:dirt_soft:grass_soft_wet$grndu:50:dirt_soft:grass_soft_wetNoise Pass]`
- `Material number [32] has name [$grnd:grass_soft_wet$grnd:grass_soft_wetNoise Pass]`
- `Material number [33] has name [$grndu:50:stones_hard:grass_hard$grndu:50:stones_hard:grass_hardNoise Pass]`
- `Material number [34] has name [$grndu:50:grass_hard:stones_hard$grndu:50:grass_hard:stones_hardNoise Pass]`
- `Material number [35] has name [$grnd:stones_hard$grnd:stones_hardNoise Pass]`
- `Material number [36] has name [$grnd:dirt_soft$grnd:dirt_softNoise Pass]`
- `Material number [37] has name [$grndu:50:dirt_soft:grass_soft_wet$grndu:50:dirt_soft:grass_soft_wetNoise Pass]`
- `Material number [38] has name [$grndu:50:grass_soft_wet:dirt_soft$grndu:50:grass_soft_wet:dirt_softNoise Pass]`
- `Material number [39] has name [$grnd:dirt_soft$grnd:dirt_softNoise Pass]`
- `Material number [40] has name [$grnd:dirt_hard$grnd:dirt_hardNoise Pass]`
- … 10 additional exact lines are retained in JSON.

### Demo 9.3.1 — France1

Directive-family counts (a line may contain more than one token): `$bsp` 1, `$draw` 1, `$grnd` 69, `$grndu` 10, `$grndv` 1, `$landdb` 3, `$nodraw` 2, `$surfacetype` 32, `surface_stones_hardnoise` 1

- `Material number [ 0] has name [$surfacetype(tarmac)$grnd(tarmac)Noise Pass]`
- `Material number [ 1] has name [$surfacetype(harddirt)$grnd(gravel)Noise Pass]`
- `Material number [ 2] has name [$surfacetype(harddirt)$grnd(gravel)Noise Pass]`
- `Material number [ 3] has name [$surfacetype(grass)$grnd(grass)Noise Pass]`
- `Material number [ 4] has name [$surfacetype(gravel)$grnd(gravel)Noise Pass]`
- `Material number [ 5] has name [$surfacetype(gravel)$grnd(gravel)Noise Pass]`
- `Material number [ 6] has name [$surfacetype(gravel)$grnd(gravel)Noise Pass]`
- `Material number [ 7] has name [$surfacetype(tarmac)$grnd(tarmac)Noise Pass]`
- `Material number [ 8] has name [$surfacetype(tarmac)$grnd(tarmac)Noise Pass]`
- `Material number [ 9] has name [$surfacetype(tarmac)$grnd(tarmac)Noise Pass]`
- `Material number [113] has name [$grnd:dirt_hard]`
- `Material number [11] has name [$surfacetype(mud)$grnd:surface_stones_hardNoise Pass]`
- … 74 additional exact lines are retained in JSON.

### Demo 9.3.1 — Italy1

Directive-family counts (a line may contain more than one token): `$bsp` 1, `$draw` 1, `$grnd` 12, `$grndu` 6, `$landdb` 1, `$nodraw` 1, `$surfacetype` 18

- `Material number [49] has name [$surfacetype(harddirt)$grnd:dirt_softNoise Pass]`
- `Material number [50] has name [$surfacetype(harddirt)$grndu:50:grass_soft_wet:dirt_softNoise Pass]`
- `Material number [51] has name [$surfacetype(harddirt)$grndu:50:dirt_soft:grass_soft_wetNoise Pass]`
- `Material number [52] has name [$surfacetype(grass)$grnd:grass_soft_wetNoise Pass]`
- `Material number [53] has name [$surfacetype(grass)$grndu:50:stones_hard:grass_hardNoise Pass]`
- `Material number [54] has name [$surfacetype(grass)$grndu:50:grass_hard:stones_hardNoise Pass]`
- `Material number [55] has name [$surfacetype(gravel)$grnd:stones_hardNoise Pass]`
- `Material number [56] has name [$surfacetype(harddirt)$grnd:dirt_softNoise Pass]`
- `Material number [57] has name [$surfacetype(gravel)$grndu:50:dirt_soft:grass_soft_wetNoise Pass]`
- `Material number [58] has name [$surfacetype(gravel)$grndu:50:grass_soft_wet:dirt_softNoise Pass]`
- `Material number [59] has name [$surfacetype(gravel)$grnd:dirt_softNoise Pass]`
- `Material number [60] has name [$surfacetype(gravel)$grnd:dirt_hardNoise Pass]`
- … 10 additional exact lines are retained in JSON.

### Demo 9.10.0 — France1

Directive-family counts (a line may contain more than one token): `$bsp` 1, `$draw` 1, `$grnd` 64, `$grndu` 10, `$grndv` 1, `$landdb` 3, `$nodraw` 2, `$surfacetype` 32, `surface_stones_hardnoise` 1

- `Material number [ 0] has name [$surfacetype(tarmac) $shader(ground)$grnd(tarmac)Noise Pass]`
- `Material number [ 1] has name [$surfacetype(harddirt) $clamp(u) $shader(ground)$grnd(gravel)Noise Pass]`
- `Material number [ 2] has name [$surfacetype(harddirt) $clamp(u) $shader(ground)$grnd(gravel)Noise Pass]`
- `Material number [ 3] has name [$surfacetype(grass) $shader(ground)$grnd(grass)Noise Pass]`
- `Material number [ 4] has name [$surfacetype(gravel) $clamp(u) $shader(ground)$grnd(gravel)Noise Pass]`
- `Material number [ 5] has name [$surfacetype(gravel) $shader(ground)$grnd(gravel)Noise Pass]`
- `Material number [ 6] has name [$surfacetype(gravel) $clamp(u) $shader(ground)$grnd(gravel)Noise Pass]`
- `Material number [ 7] has name [$surfacetype(tarmac) $shader(ground)$grnd(tarmac)Noise Pass]`
- `Material number [ 8] has name [$surfacetype(tarmac) $shader(ground)$grnd(tarmac)Noise Pass]`
- `Material number [ 9] has name [$surfacetype(tarmac) $shader(ground)$grnd(tarmac)Noise Pass]`
- `Material number [11] has name [$surfacetype(mud) $shader(ground)$grnd:surface_stones_hardNoise Pass]`
- `Material number [124] has name [$grnd:dirt_hard]`
- … 69 additional exact lines are retained in JSON.

### Demo 9.10.0 — Italy1

Directive-family counts (a line may contain more than one token): `$bsp` 1, `$draw` 1, `$grnd` 12, `$grndu` 6, `$landdb` 1, `$nodraw` 1, `$surfacetype` 18

- `Material number [58] has name [$surfacetype(harddirt) $shader(ground) $mip(1.0)$grnd:dirt_softNoise Pass]`
- `Material number [59] has name [$surfacetype(harddirt) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:grass_soft_wet:dirt_softNoise Pass]`
- `Material number [60] has name [$surfacetype(harddirt) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:dirt_soft:grass_soft_wetNoise Pass]`
- `Material number [61] has name [$surfacetype(grass) $shader(ground) $mip(1.0)$grnd:grass_soft_wetNoise Pass]`
- `Material number [62] has name [$surfacetype(grass) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:stones_hard:grass_hardNoise Pass]`
- `Material number [63] has name [$surfacetype(grass) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:grass_hard:stones_hardNoise Pass]`
- `Material number [64] has name [$surfacetype(gravel) $shader(ground) $mip(1.0)$grnd:stones_hardNoise Pass]`
- `Material number [65] has name [$surfacetype(harddirt) $shader(ground) $mip(1.0)$grnd:dirt_softNoise Pass]`
- `Material number [66] has name [$surfacetype(gravel) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:dirt_soft:grass_soft_wetNoise Pass]`
- `Material number [67] has name [$surfacetype(gravel) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:grass_soft_wet:dirt_softNoise Pass]`
- `Material number [68] has name [$surfacetype(gravel) $shader(ground) $mip(1.0)$grnd:dirt_softNoise Pass]`
- `Material number [69] has name [$surfacetype(gravel) $shader(ground) $mip(1.0) $clamp(u)$grnd:dirt_hardNoise Pass]`
- … 10 additional exact lines are retained in JSON.

### Retail — France1

Directive-family counts (a line may contain more than one token): `$bsp` 1, `$draw` 1, `$grnd` 43, `$landdb` 3, `$nodraw` 2, `$surfacetype` 33, `surface_stones_hardnoise` 1

- `Material number [ 0] has name [$surfacetype(tarmac) $shader(ground)$grnd(tarmac)Noise Pass]`
- `Material number [ 1] has name [$surfacetype(harddirt) $clamp(u) $shader(ground)$grnd(gravel)Noise Pass]`
- `Material number [ 2] has name [$surfacetype(harddirt) $clamp(u) $shader(ground)$grnd(gravel)Noise Pass]`
- `Material number [ 3] has name [$surfacetype(grass) $shader(ground)$grnd(grass)Noise Pass]`
- `Material number [ 4] has name [$surfacetype(gravel) $clamp(u) $shader(ground)$grnd(gravel)Noise Pass]`
- `Material number [ 5] has name [$surfacetype(gravel) $shader(ground)$grnd(gravel)Noise Pass]`
- `Material number [ 6] has name [$surfacetype(gravel) $clamp(u) $shader(ground)$grnd(gravel)Noise Pass]`
- `Material number [ 7] has name [$surfacetype(tarmac) $shader(ground)$grnd(tarmac)Noise Pass]`
- `Material number [ 8] has name [$surfacetype(tarmac) $shader(ground)$grnd(tarmac)Noise Pass]`
- `Material number [ 9] has name [$surfacetype(tarmac) $shader(ground)$grnd(tarmac)Noise Pass]`
- `Material number [11] has name [$surfacetype(mud) $shader(ground)$grnd:surface_stones_hardNoise Pass]`
- `Material number [12] has name [$surfacetype(harddirt) $clamp(u) $shader(ground)$grnd(harddirt)Noise Pass]`
- … 37 additional exact lines are retained in JSON.

### Retail — Italy1

Directive-family counts (a line may contain more than one token): `$bsp` 1, `$draw` 1, `$grnd` 12, `$grndu` 6, `$landdb` 1, `$nodraw` 1, `$surfacetype` 18

- `Material number [58] has name [$surfacetype(harddirt) $shader(ground) $mip(1.0)$grnd:dirt_softNoise Pass]`
- `Material number [59] has name [$surfacetype(harddirt) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:grass_soft_wet:dirt_softNoise Pass]`
- `Material number [60] has name [$surfacetype(harddirt) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:dirt_soft:grass_soft_wetNoise Pass]`
- `Material number [61] has name [$surfacetype(grass) $shader(ground) $mip(1.0)$grnd:grass_soft_wetNoise Pass]`
- `Material number [62] has name [$surfacetype(grass) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:stones_hard:grass_hardNoise Pass]`
- `Material number [63] has name [$surfacetype(grass) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:grass_hard:stones_hardNoise Pass]`
- `Material number [64] has name [$surfacetype(gravel) $shader(ground) $mip(1.0)$grnd:stones_hardNoise Pass]`
- `Material number [65] has name [$surfacetype(harddirt) $shader(ground) $mip(1.0)$grnd:dirt_softNoise Pass]`
- `Material number [66] has name [$surfacetype(gravel) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:dirt_soft:grass_soft_wetNoise Pass]`
- `Material number [67] has name [$surfacetype(gravel) $shader(ground) $mip(1.0) $clamp(u)$grndu:50:grass_soft_wet:dirt_softNoise Pass]`
- `Material number [68] has name [$surfacetype(gravel) $shader(ground) $mip(1.0)$grnd:dirt_softNoise Pass]`
- `Material number [69] has name [$surfacetype(gravel) $shader(ground) $mip(1.0) $clamp(u)$grnd:dirt_hardNoise Pass]`
- … 10 additional exact lines are retained in JSON.

## Parser boundary

The shared sidecar parser extracts material names, texture records, declared material count, and `moMesh` spans. `moUnknown`/special directive-bearing lines remain preserved by the corpus probe but are not interpreted as scene nodes. `$bsp`, `$draw`, `$nodraw`, `$landdb`, `$grnd*`, and `$surfacetype` are string evidence only; their compiled/runtime meanings remain UNKNOWN.
