# Exact PS2 HUD resource map

Every asset below was addressed structurally through the canonical PackFS
manifest and freshly decoded. TNG.000 ranges, stored/decoded hashes, codec and
sizes are in `extraction-provenance.json`. No old string-carved offset or
historical extracted binary supplies the authoritative data.

All ten banks have prefix **`\TNG\DATAPSM\HUD\`**:

| Bank | Decoded bytes | Keys | Images | Triangles | Texture stems |
| --- | ---: | ---: | ---: | ---: | ---: |
| HUD-NUMS.PSB | 2656 | 10 | 4 | 32 | 3 |
| HUD-TEMPLATE.PSB | 3004 | 11 | 11 | 34 | 8 |
| MASTER_TEMPLATE.PSB | 4714 | 10 | 10 | 54 | 10 |
| PACENOTES.PSB | 4192 | 24 | 24 | 48 | 24 |
| NEWHUD.PSB | 11768 | 10 | 38 | 148 | 15 |
| HUD-NUMSSMALL.PSB | 2414 | 10 | 4 | 28 | 2 |
| HUD-SPLIT.PSB | 2902 | 11 | 11 | 34 | 6 |
| HUD-DAMAGE.PSB | 1072 | 6 | 6 | 12 | 2 |
| CARDAMAGEBITS.PSB | 1982 | 8 | 8 | 22 | 1 |
| HUD.PSB | 2446 | 4 | 4 | 32 | 8 |

Counts/bytes are mechanically reproduced by `psb-manifest.json`, which is the
authority if presentation tables drift. Texture stems resolve within the same
logical HUD directory; all **79 HUD GXI** files are 64×64 simple GXI. Inventory
includes NEWHUD_000..014, HUD-SPLIT_000..005, HUD-DAMAGE_000..001,
CARDAMAGEBITS_000, all other referenced HUD atlases, and the complete list of
**54 PSB paths** in TNG (only the ten HUD PSBs were parsed in this pass).

Primary byte provenance:

| PSB | TNG.000 offset | Stored bytes | Codec |
| --- | ---: | ---: | --- |
| HUD-NUMS | 1209465583 | 1005 | PackFS / LZO |
| HUD-TEMPLATE | 1209525455 | 1095 | PackFS / LZO |
| MASTER_TEMPLATE | 1209642928 | 1582 | PackFS / LZO |
| PACENOTES | 1209795467 | 485 | PackFS / LZO |

The primary bank hashes are stored in `psb-manifest.json`; every referenced
texture has its own decoded hash/dimensions/alpha statistics in
`texture-metadata.json`. `psbtool verify --texture-dir` checks actual UV sample
bounds inside the serialized cell and actual texture dimensions.

HUD-NUMS keys are ASCII 48–57. Its three atlas stems are `hud-nums_000..002`.
Four reconstructed images show digits 1–4, with alias table
`0->0, 1->0, 2->1, 3->2, 4->3, 5->3, 6->3, 7->3, 8->3, 9->3`.
Geometric image bounds are `(0,-47)..(34,1)`, `(0,-47)..(46,1)`,
`(0,-47)..(45,1)`, `(0,-47)..(48,1)`. Height is 48; widths include all
serialized geometry, including Null pieces. No baseline/advance/bearing is
invented. Confidence: **CONFIRMED_BY_BOTH** for keys/geometry and
**CONFIRMED_BY_VISUAL_RECONSTRUCTION** for drawn digits.

NEWHUD's complete large-digit lookup is `0->37`, `1->28`, `2->29`, `3->30`,
`4->31`, `5->32`, `6->33`, `7->34`, `8->35`, `9->36`. Large-digit geometry
widths in character order are 43,34,46,45,48,47,43,47,44,44; height 48.
Images 10–19 are visually small digits 0–9. These separate sets explain why
substituting the four-image HUD-NUMS bank would be incorrect.

PACENOTES has identity keys/image indices 0–23 and 48 triangles. Image i uses
`pacenotes_{23-i:03d}` (two triangles each). All 24 atlases reconstruct upright
road/hazard diagrams. Exact gameplay pace-note IDs/trigger meanings remain
UNKNOWN; file order does not by itself prove left/right/severity enums.

Authored scene resources are under `\TNG\DATASCENE\HUD\`: HUD0.XML,
HUD1.XML, HUDDEBUG.XML, ATTRACTMODE.XML, HUD0.XML.DISABLED. The disabled copy
is kept distinct. There are **40** exact resources under
`\TNG\DATASCENE\FRONTENDSCREENS\PS2\`, all text XML in this audited set.
These 45 resources were read for bounded model/owner/MAP128STRIPED references;
only the five HUD resources were extracted. Exact paths and audit provenance
are in `resource-inventory.json`; extracted authored relationships are in
`hud-elements.json`. No BXML stripping or guessed header removal was used.

MAP128STRIPED is present as exactly
`\TNG\DATAPSM\COMMONTEXTURES\MAP128STRIPED1-TGA.GXI`: 65544 decoded bytes,
128×128, alpha 255 everywhere. It depicts a striped world map. No reference
was found among the ten PSBs or 45 audited XML resources; this is a bounded
negative result, not proof of global non-use. The complete dynamic course
minimap path is **not known**. Candidate owner is gaHudAiMap; UI2 should follow
its course-dependent geometry and GPS/vehicle overlay relationship.

Bonus texture metadata (all names are present in the manifest):

| Exact tail under DATAPSM | Dimensions | Alpha min–max | Unique A | Visually observed picture |
| --- | --- | --- | ---: | --- |
| PARTICLES\GRASS1.GXI | 32×32 | 0–255 | 223 | Grass cutout |
| PARTICLES\BUSH1.GXI | 32×32 | 0–255 | 213 | Bush cutout |
| COMMONTEXTURES\WATERSURFACE2.GXI | 64×64 | 4–131 | 128 | Blue water pattern |
| COMMONTEXTURES\ENVSOURCE64X64.GXI | 64×64 | 0–255 | 2 | Environment sphere |
| COMMONTEXTURES\RENDERTARGET64X64.GXI | 64×64 | 0–255 | 2 | Environment capture |
| COMMONTEXTURES\STATICRENDERTARGET64X64.GXI | 64×64 | 110–110 | 1 | Course landscape capture |
| COMMONTEXTURES\WINDSCREEN-REFLECT.GXI | 32×32 | 255–255 | 1 | Blurred environment sphere |

Average RGBA and exact hashes/ranges are in `texture-metadata.json`. These
are stored-image observations only; no grass/water/reflection code path was
reversed and no live target update, shader, blending or material role is proved.
