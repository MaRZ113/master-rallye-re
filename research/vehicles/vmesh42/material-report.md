# V-MESH4.2 material report (from `reports/validation-report.json`)

Pools = donor draws whose fixed-size DXT now carries packed GT UV islands. `pass`: opaque (draw without blending), blend (alpha-enabled draw), special (lamp/glass keep their donor draw and its alpha flag). Densities are texels per m2 of body surface; draw indices are per file (car.dx / complete.dx).

| donor texture | size | pass | car / complete draw | islands | triangles | density | GT materials |
|---|---|---|---|---|---|---|---|
| `underdash-tga` | 128x128 | blend | 0 / 0 | 16 | 124 | 2035 | Mat1_Tex0, Mat1_Tex12, Mat1_Tex13, Mat1_Tex15, Mat1_Tex16, Mat1_Tex19, Mat1_Tex20, Mat1_Tex21, Mat1_Tex29, Mat1_Tex30, Mat6_Tex1, Mat6_Tex26, Mat6_Tex41 |
| `grillenav-tga` | 64x64 | blend | 11 / 11 | 9 | 95 | 1486 | Mat1_Tex0, Mat1_Tex11, Mat1_Tex14, Mat1_Tex17, Mat1_Tex19, Mat1_Tex33, Mat6_Tex22, Mat6_Tex5 |
| `nisbackbadge-tga` | 64x64 | blend | 14 / 14 | 10 | 194 | 934 | Mat-1_Tex38, Mat1_Tex0, Mat1_Tex18, Mat1_Tex36, Mat1_Tex7, Mat6_Tex10, Mat6_Tex34, Mat6_Tex41 |
| `inbak-tga` | 32x32 | blend | 15 / 15 | 4 | 44 | 425 | Mat1_Tex0, Mat1_Tex15, Mat6_Tex32 |
| `sidenav1-tga` | 128x128 | opaque | 4 / 4 | 3 | 253 | 1300 | Mat1_Tex0, Mat1_Tex14, Mat1_Tex15 |
| `frontwa-tga` | 64x64 | opaque | 22 / 18 | 6 | 254 | 1146 | Mat1_Tex11, Mat1_Tex13, Mat1_Tex14, Mat1_Tex6, Mat6_Tex4 |
| `new chrome logo-tga` | 64x64 | opaque | 13 / 13 | 3 | 72 | 1808 | Mat1_Tex15, Mat1_Tex19, Mat6_Tex1 |
| `foglight-tga` | 32x32 | opaque | 10 / 10 | 5 | 59 | 884 | Mat-1_Tex39, Mat1_Tex15, Mat1_Tex6, Mat6_Tex26 |
| `masterral-tga` | 32x32 | opaque | 7 / 7 | 3 | 46 | 714 | Mat1_Tex6, Mat6_Tex28, Mat6_Tex5 |
| `mastersticker258-tga` | 32x32 | opaque | 12 / 12 | 2 | 47 | 1289 | Mat1_Tex15, Mat1_Tex7 |
| `shine-tga` | 32x32 | opaque | 6 / 6 | 2 | 8 | 2167 | Mat1_Tex15, Mat6_Tex27 |
| `colourfade-tga` | 16x16 | opaque | 5 / 5 | 3 | 64 | 547 | Mat1_Tex16, Mat1_Tex18, Mat6_Tex5 |
| `inlights-tga` | 16x16 | opaque | 23 / 19 | 2 | 22 | 1034 | Mat1_Tex15, Mat6_Tex2 |
| `line-tga` | 16x16 | opaque | 8 / 8 | 3 | 18 | 490 | Mat1_Tex12, Mat1_Tex15, Mat1_Tex17 |
| `headlamp-tga` | 64x64 | special | 25 / 25 | 1 | 100 | 10460 | Mat6_Tex23 |
| `backlightjnavp-tga` | 32x32 | special | 24 / 16 | 1 | 38 | 2084 | Mat6_Tex25 |
| `windscreen32-tga` | 32x32 | special | 35 / 24 | 1 | 44 | 182 | Mat6_Tex37 |

## Triangle classes by source role (alpha judged over each triangle's UV footprint)

| role : class | triangles |
|---|---|
| black:clear | 16 |
| black:cutout | 20 |
| black:opaque | 290 |
| black:translucent | 126 |
| glass:mixed | 28 |
| glass:translucent | 16 |
| head_lamp:clear | 4 |
| head_lamp:cutout | 47 |
| head_lamp:opaque | 53 |
| interior:cutout | 24 |
| interior:opaque | 253 |
| paint:clear | 16 |
| paint:cutout | 140 |
| paint:mixed | 123 |
| paint:opaque | 703 |
| paint:translucent | 24 |
| tail_lamp:opaque | 38 |

## Routing result

| destination | triangles |
|---|---|
| blend:grillenav-tga | 95 |
| blend:inbak-tga | 44 |
| blend:nisbackbadge-tga | 194 |
| blend:underdash-tga | 124 |
| dropped | 36 |
| opaque:colourfade-tga | 64 |
| opaque:foglight-tga | 59 |
| opaque:frontwa-tga | 254 |
| opaque:inlights-tga | 22 |
| opaque:line-tga | 18 |
| opaque:masterral-tga | 46 |
| opaque:mastersticker258-tga | 47 |
| opaque:new chrome logo-tga | 72 |
| opaque:shine-tga | 8 |
| opaque:sidenav1-tga | 253 |
| role:black | 403 |
| special:backlightjnavp-tga | 38 |
| special:headlamp-tga | 100 |
| special:windscreen32-tga | 44 |

Dropped because the whole texel footprint is clear: 36 triangles (`source-map/dropped-faces.json`). Rejected for lack of pool space: 0.
Flat black regions drawn with the unchanged donor black trim texture: counted under `role:black`.

## Alpha flags in the built files

`car.dx` alpha-enabled draws: [0, 11, 14, 15, 25, 26, 27, 30, 31, 32, 33, 34, 35, 36] (switched on by V-MESH4.2: [0, 11, 14, 15]).
`complete.dx` alpha-enabled draws: [0, 11, 14, 15, 24, 25] (switched on: [0, 11, 14, 15]).

## Why the V-MESH4.1 artefacts appeared (front region, per source material)

| GT material | role | triangles | V-MESH4.1 | V-MESH4.2 |
|---|---|---|---|---|
| Mat-1_Tex39 | interior | 3 | drawn opaque with one donor texel | pool:foglight-tga (opaque) |
| Mat1_Tex0 | paint | 111 | drawn opaque with one donor texel | pool:sidenav1-tga (opaque) |
| Mat1_Tex0 | paint | 2 | drawn opaque with one donor texel (cut-out ignored) | pool:underdash-tga (cutout) |
| Mat1_Tex0 | paint | 5 | drawn opaque with one donor texel (cut-out ignored) | pool:nisbackbadge-tga (cutout) |
| Mat1_Tex15 | paint | 12 | drawn opaque with one donor texel | pool:line-tga (opaque) |
| Mat1_Tex15 | paint | 10 | drawn opaque with one donor texel | pool:mastersticker258-tga (opaque) |
| Mat1_Tex15 | paint | 14 | drawn opaque with one donor texel (cut-out ignored) | pool:underdash-tga (mixed) |
| Mat1_Tex15 | paint | 1 | drawn opaque with one donor texel (cut-out ignored) | pool:underdash-tga (cutout) |
| Mat1_Tex15 | paint | 21 | drawn opaque with one donor texel | pool:foglight-tga (opaque) |
| Mat1_Tex15 | paint | 12 | drawn opaque with one donor texel | pool:inlights-tga (opaque) |
| Mat1_Tex15 | paint | 13 | drawn opaque with one donor texel (cut-out ignored) | pool:inbak-tga (mixed) |
| Mat1_Tex15 | paint | 14 | drawn opaque with one donor texel (cut-out ignored) | pool:inbak-tga (translucent) |
| Mat1_Tex15 | paint | 2 | drawn opaque with one donor texel | pool:shine-tga (opaque) |
| Mat1_Tex15 | paint | 1 | drawn opaque with one donor texel | pool:sidenav1-tga (opaque) |
| Mat1_Tex16 | paint | 24 | drawn opaque with one donor texel | pool:colourfade-tga (opaque) |
| Mat1_Tex16 | paint | 4 | drawn opaque with one donor texel (cut-out ignored) | pool:underdash-tga (cutout) |
| Mat1_Tex17 | paint | 4 | dropped (decal) | pool:line-tga (opaque) |
| Mat1_Tex17 | paint | 4 | dropped (decal) | pool:grillenav-tga (cutout) |
| Mat1_Tex18 | paint | 28 | drawn opaque with one donor texel | pool:colourfade-tga (opaque) |
| Mat1_Tex18 | paint | 2 | drawn opaque with one donor texel (cut-out ignored) | pool:nisbackbadge-tga (mixed) |
| Mat1_Tex18 | paint | 6 | drawn opaque with one donor texel (cut-out ignored) | pool:nisbackbadge-tga (cutout) |
| Mat1_Tex19 | paint | 42 | dropped (decal) | pool:new chrome logo-tga (opaque) |
| Mat1_Tex19 | paint | 13 | kept solid (unsupported overlay) | pool:new chrome logo-tga (opaque) |
| Mat1_Tex19 | paint | 6 | dropped (decal) | pool:grillenav-tga (mixed) |
| Mat1_Tex19 | paint | 4 | dropped (decal) | pool:grillenav-tga (cutout) |
| Mat1_Tex19 | paint | 5 | dropped (decal) | pool:underdash-tga (cutout) |
| Mat1_Tex19 | paint | 1 | kept solid (unsupported overlay) | pool:underdash-tga (cutout) |
| Mat1_Tex29 | paint | 10 | drawn opaque with one donor texel (cut-out ignored) | pool:underdash-tga (cutout) |
| Mat1_Tex33 | paint | 4 | dropped (decal) | pool:grillenav-tga (cutout) |
| Mat1_Tex36 | paint | 4 | drawn opaque with one donor texel (cut-out ignored) | pool:nisbackbadge-tga (cutout) |
| Mat1_Tex7 | paint | 4 | drawn opaque with one donor texel (cut-out ignored) | pool:nisbackbadge-tga (mixed) |
| Mat1_Tex7 | paint | 9 | drawn opaque with one donor texel (cut-out ignored) | pool:nisbackbadge-tga (cutout) |
| Mat1_Tex7 | paint | 11 | drawn opaque with one donor texel | pool:mastersticker258-tga (opaque) |
| Mat1_Tex9 | paint | 4 | kept solid (unsupported overlay) | drop (clear) |
| Mat6_Tex10 | black | 2 | drawn opaque with one donor texel (cut-out ignored) | pool:nisbackbadge-tga (cutout) |
| Mat6_Tex22 | black | 2 | drawn opaque with one donor texel (cut-out ignored) | pool:grillenav-tga (cutout) |
| Mat6_Tex23 | head_lamp | 53 | drawn opaque with one donor texel | head_lamp (opaque) |
| Mat6_Tex23 | head_lamp | 47 | drawn opaque with one donor texel (cut-out ignored) | head_lamp (cutout) |
| Mat6_Tex23 | head_lamp | 4 | drawn opaque with one donor texel | drop (clear) |
| Mat6_Tex26 | black | 2 | drawn opaque with one donor texel (cut-out ignored) | pool:underdash-tga (cutout) |
| Mat6_Tex26 | black | 2 | drawn opaque with one donor texel | pool:foglight-tga (opaque) |
| Mat6_Tex27 | black | 2 | drawn opaque with one donor texel | pool:shine-tga (opaque) |
| Mat6_Tex28 | black | 2 | drawn opaque with one donor texel | pool:masterral-tga (opaque) |
| Mat6_Tex3 | black | 81 | drawn opaque with one donor texel | black (opaque) |
| Mat6_Tex32 | black | 4 | drawn opaque with one donor texel (cut-out ignored) | pool:inbak-tga (cutout) |
| Mat6_Tex34 | black | 5 | dropped (decal) | pool:nisbackbadge-tga (translucent) |
| Mat6_Tex34 | black | 6 | kept solid (unsupported overlay) | pool:nisbackbadge-tga (translucent) |
| Mat6_Tex40 | black | 3 | dropped (decal) | drop (clear) |
| Mat6_Tex40 | black | 1 | kept solid (unsupported overlay) | drop (clear) |
| Mat6_Tex41 | black | 20 | kept solid (unsupported overlay) | pool:nisbackbadge-tga (translucent) |
| Mat6_Tex41 | black | 2 | dropped (decal) | pool:nisbackbadge-tga (translucent) |
| Mat6_Tex42 | black | 4 | kept solid (unsupported overlay) | drop (clear) |
| Mat6_Tex43 | black | 4 | kept solid (unsupported overlay) | drop (clear) |
| Mat6_Tex8 | black | 4 | kept solid (unsupported overlay) | drop (clear) |
