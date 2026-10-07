# Named graphics research targets

`graphics-targets.json` contains deterministic name-based inventories with
manifest indices, offsets and sizes. Families overlap. Resource existence and
location are CONFIRMED_BY_BOTH; a proposed rendering role is STATIC_INFERENCE.
No PC visual feature was implemented.

| Family | Name-matched files | Fresh extraction |
| --- | ---: | --- |
| HUD / frontend candidates | 135 | HUD-TEMPLATE.PSB, HUD-NUMS.PSB, NEWHUD_000.GXI |
| Grass/detail/particles candidates | 175 | FRANCE2/GRASS-TGA.GXI, ITALY3/I2A_GRASSPATH-TGA.GXI |
| Water/puddle candidates | 46 | FRANCE1/WATER-TGA.GXI |
| Environment/reflection candidates | 19 | CommonTextures/ENVSOURCE64X64.GXI, REAR128-TGA.GXI |

Manifest confirms particles/GRASS1.GXI, particles/BUSH1.GXI and
CommonTextures/WATERSURFACE2.GXI. ELF contains exact `particles/bush1` and
`particles/grass1` strings at 0x00486180/0x00486190,
`CommonTextures/windscreen-reflect` at 0x004874d0 and
`CommonTextures/watersurface2` at 0x00487690. These are string evidence only;
placement/spawning/render-path callers were not reversed in this phase.

ELF also confirms `$detail(grass)`, `$detail(shrubs)`, `$detail(stones)` and
`$detail(none)` at 0x00486140/0x00486150/0x00486160/0x00486170,
`$surfacetype(grass)` at 0x004746f8 and `$surfacetype(water)` at 0x004747a0
(also 0x00485968). `CommonTextures\rendertarget64x64` and
`CommonTextures\envsource64x64` occur at 0x00485900/0x00485928. Their existence
is CONFIRMED_BY_BYTES; graphics data flow remains UNKNOWN. A `RENDERTARGET64X64` filename does not prove
a dynamic reflection map. HUD filenames likewise do not assign screen elements.

All six extracted GXI files have little-endian magic 0x00013039, u16 width/height,
and exact size 8 + width*height*4. They are classified SIMPLE_4_BYTES_PER_PIXEL.
Channel order remains UNKNOWN; no image conversion, swizzle/palette/mipmap
interpretation or shader/material mapping was attempted. Nonmatching GXI is
classified UNKNOWN/OTHER rather than force-decoded.
