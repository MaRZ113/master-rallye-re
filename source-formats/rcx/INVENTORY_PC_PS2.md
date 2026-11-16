# Rally Championship Xtreme (PC) and Rally Championship (PS2) — inventory

Date: 2026-11-16. Goal: a new Master Rallye category "RCX" (cars via Vehicle SDK, stages via
Course Studio), then weather. Sources (read-only):

* PC: `E:\RallyWorkshop_Sources\sources\Rally Championship Xtreme` (`Rally.exe` SHA-256
  `efc94948...a355`, Warthog, 2001).
* PS2: `E:\RallyWorkshop_Sources\sources\Rally Championship PS2` (SLES-50763, Europe, 2002).

Tools: `rcx_census.py` (PC archive census/extract), `../rally-championship-ps2/*`.
Private outputs: `.research-output/rcx-pc/`, `.research-output/rally-championship-ps2/`.

## 1. Cars

Both games share the same 27 car models; the PC adds one livery variant.

| # | Car | PC archive (full / arcade) | PS2 (`CARS` / `M_CARS`) | PC spec | PS2 spec | Difference |
|---|---|---|---|---|---|---|
| 1 | Audi Quattro | audi_quattro | AUDI | 2109cc 5cyl, 370 bhp, 135 mph | 2.11 L 5cyl turbo, 370 bhp, 165 mph | top speed text |
| 2 | Citroen Saxo | Citroen Saxo | CITROEN | 1600 16v, 6-sp, 215 bhp | 1.6 16v, 5-sp, 165 bhp, 0-60 7.5 s | **different spec** |
| 3 | Ford Escort Maxi | Escort Maxi | ESCORT | 2.0, 270 bhp | same | — |
| 4 | Ford Focus WRC | ford focus | FORDF | 2.0 Zetec, 300 bhp | same | — |
| 5 | Ford Puma (stock) | Ford Puma | FORDP | 1400, 115 bhp | listed as "Ford Puma" 1.6, 220 bhp | naming swapped |
| 6 | Ford Puma SP / Mod | Ford Puma SP | FORDPSP | 1600, 220 bhp ("Puma Mod") | "Puma SP" 1.4, 160 bhp | **different spec** |
| 7 | Honda Civic | honda civic | HONDA | 1600 VTEC, 215 bhp | same | — |
| 8 | Hyundai Accent WRC | Hyundai Accent | HYUNDAIA | 2.0, 300 bhp | same | — |
| 9 | Hyundai Coupe | hyundai coupe | HYUNDAIC | 2.0, 265 bhp | same | — |
| 10 | Mitsubishi Lancer Evo V | Lancer Evo5 | LANCER5 | 300 bhp, H-pattern | same | — |
| 11 | Mitsubishi Lancer Evo VI | Lancer Evo6 | LANCER6 | 300 bhp, sequential | same | — |
| 12 | Lancia Stratos | lancia stratos | LANCIA | 2400 V6, 270 bhp, RWD | same | — |
| 13 | Mini Cooper | Mini Cooper | COOPER | 1275cc, 115 bhp | same | — |
| 14 | Nissan Micra | Nissan Micra | NISSAN | 1300, 150 bhp | same | — |
| 15 | Peugeot 106 Maxi | Peugeot106 | PEUGEOT1 | 1600, 210 bhp | same | — |
| 16 | Peugeot 206 WRC | peugeot206 | PEUGEOT2 | 2.0, 300 bhp | same | — |
| 17 | Proton Compact / Satria | Proton Compact | PROTON | 1600, 207 bhp | named "Proton Satria" | name |
| 18 | Renault Megane Maxi | renault megane | RENAULT | 2.0, 260 bhp | same | — |
| 19 | Seat Cordoba WRC | Seat Cordoba | SEATC | 2.0, 300 bhp | same | — |
| 20 | Seat Ibiza Kit Car | Seat Ibiza | SEATI | 2.0, 275 bhp | same | — |
| 21 | Skoda Felicia | skoda felicia | SKODAF | 1600 8v, 110 bhp | 1.4, 110 bhp | engine text |
| 22 | Skoda Octavia WRC | Skoda Octavia | SKODAO | 2.0 20v, 300 bhp | same | — |
| 23 | Subaru Impreza 1998 | subaru impreza98 | SUBARU98 | EJ20, 300 bhp | same | — |
| 24 | Subaru Impreza 2000 | subaru impreza00 | SUBARU00 | EJ20, 300 bhp | same | — |
| 25 | Subaru Impreza 2001 | subaru impreza01 | SUBARU01 | EJ20, 300 bhp | same | — |
| 26 | Vauxhall Astra Kit Car | Astra | ASTRA | 2.0 Ecotec, 280 bhp | same | — |
| 27 | VW Golf Kit Car | VW Golf | GOLF | 2.0 20v, 265 bhp | same | — |
| — | Subaru Impreza 2000 "sun" | subaru impreza00sun | — | — | — | **PC only** (livery variant) |

Model variants:

* PC full model: about 90 members, about 62 QTO parts (body, panels, damage parts
  `damage_xmesh.qto`, collision `collision_xmesh.edg`), 20-25 TEX (512x512 BGRA/DXT).
  PC `_arcade`: 14 QTO, 4-6 TEX (low detail). PC physics: binary `CarStats/*.cog` (all 28 differ
  from `OldCarStats/`, which looks like an earlier balance).
* PS2 `CARS`: 256x256 textures; `M_CARS`: 128x128 (multiplayer). PS2 tuning text blocks are in
  `TWEAK0.PAR`.
* Classes (both games): Amateur, Privateer, 1600 Modified, 2000 Modified, Pro (WRC), Classic;
  PS2 championships 1600 / 2000 / A8. The per-car class table is not decoded yet; the obvious
  split by spec is WRC (Impreza x3, Lancer V/VI, 206, Focus, Cordoba, Octavia, Accent),
  2.0 kit cars (Astra, Golf, Megane, Ibiza, Escort Maxi, Hyundai Coupe), 1600 (Saxo, Civic, 106,
  Proton, Puma SP/Mod, Micra), road/amateur (Puma, Felicia), Classic (Quattro, Stratos, Mini).

**Source choice for MR:** PC full models (more detail, damage parts, 512 textures, Astra pilot
decoder already exists). PS2 models stay a reference; their geometry has not been compared.

## 2. Stages

### PS2: 33 stages + 1 unused map (table dump `ps2_tables.py`)

| Rally | Stage (map, km, weather) |
|---|---|
| Kenya (safari) | Tsavo (MAP84, 7.1, afternoon dry), Rift Valley (MAP81, 6.0, morning windy), Mount Longonot (MAP83, 6.5, dusk), Turkana River (MAP82, 6.6, morning) |
| Scotland | Glengap (MAP33, 8.0, **rain**), Black Loch (MAP34, 7.0, **rain**), Twiglees (MAP31, 8.5, misty), Dumfries (MAP44, 9.0, misty), **Bennon** (MAP35, 4.5, bonus stage) |
| Wales | Pen-y-Coed (MAP22, 7.4, dusk), Gartheiniog (MAP32, 8.4, **rain**), Llandudno (MAP21, 7.5, misty), Llanberis (MAP41, 8.0, sunny) |
| Manx | Glenmooar (MAP43, 7.1), Baldrine (MAP42, 9.3, windy), Knocksharry (MAP24, 7.5, **rain + fog**), Laxey (MAP23, 6.8) |
| Arctic (snow tyres) | Kaihuavaara (MAP72, 6.7), Rovaniemi (MAP73, 3.6), Kemijärvi (MAP74, 5.2, twilight), Ristilampi (MAP71, 6.9, ice) — all **snowfall** |
| USA | Arizona (MAP64, 6.0), Nevada (MAP61, 7.4), Hualapai Nation (MAP62, 7.8, tarmac 100 %), Bullhead (MAP63, 5.8) |
| Special / multiplayer (2-4 km) | Conway (MAP51), Eairy (MAP52), Aberporth (MAP53), Loch Lomond (MAP54, fog), **Hanhikoski** (MAP50, snow, no snowfall), Kajiado (MAP57), Mbaruk (MAP58), Laughlin (MAP59) |
| Unused | **MAP29**: a complete point-to-point stage on the disc that no table row references (cut content; strings also name an unused "Wrexham" and "Twisted Dawn") |

Each stage carries its own fog colour / distance / saturation, sun and car-reflection values in
the table — directly usable for MR course atmosphere.

### PC: 24 stages (6 rallies x 4), fictional names

| Rally | Stages (archive) | Weather (PC text) |
|---|---|---|
| East African Safari | Fire Rock (kenya1), Twin Bridges (Kenya2), Vertigo Rift (Kenya3), Dark Safari (kenya4, **night**) | dry |
| Vauxhall Rally of Wales | Mountain Descent (welsh1), Lake Llyn Brenig (welsh2), Lakeside Storm Clouds (welsh3), Foggy Forest (welsh4, **rain + fog**) | |
| Kumho Scottish | Sunset Stones (scottish1), Clashin Darroch (scottish2), Sunshine Loch (scottish3), Stormy Loch (scottish4, **rain**) | |
| International Manx | Harbour Mist (manx1, mist), Plantation (manx2, **rain**), Coastal Edge (manx3), The Curraghs (manx4, fog) | |
| Arctic Lapland | Frozen Falls (arctic1), Glacier Run (arctic2), Lowland Village (arctic3, **snowing**), Snowy Mountain (arctic4, **night**) | snow 80-100 % |
| Rally USA | Canyon Ridge (usa1, **sandstorm**), Truckers Tunnel (usa2, tarmac), The Abyss (usa3), Naked Thunder (usa4, **night thunderstorm**) | |

Plus `carfloor.rcx` (garage floor). 14 stages also exist as `_arcade` archives (same member
counts; arcade copies). Archive content: `<stage>.map` (world: node tree with bboxes; about 45 mesh leaves,
each = 0x80-byte header + u16 indices + 32-byte vertices in **world** coordinates), `config.cfg` (`TCFG`: environment, mesh list, insulated objects),
5-33 QTO/MSH object meshes, 120-370 TEX textures, optional `.tan` (animation).

### PC vs PS2 — geometry comparison (2026-11-16)

Method (`shared_geometry.py`, `coverage_matrix.py`, `refine_pairs.py`, `overlay.py`): PC leaf
vertices vs PS2 map vertices. **The PS2 world is the PC world with X negated, same origin**
(found on manx1 / MAP21, then holds for every shared pair). Measures: share of PC 6-m road cells
present in the PS2 map, share of PC vertices with a PS2 vertex within 0.1 m. Unrelated pairs
score <= 0.3 cells / 0.000 vertices.

| PC stage (fictional name) | PS2 map (real name) | PC cells in PS2 | exact vertices | Verdict |
|---|---|---|---|---|
| manx1 Harbour Mist | MAP21 Llandudno (Wales 3) | 0.70 | 0.24 | **same geometry**, PC = one route of the PS2 map |
| manx2 Plantation | MAP32 Gartheiniog (Wales 2) | 0.79 | 0.34 | same |
| manx3 Coastal Edge | MAP42 Baldrine (Manx 2) | 0.51 | 0.46 | same (PC route partly differs) |
| manx4 The Curraghs | MAP24 Knocksharry (Manx 3) | 0.85 | 0.29 | same |
| scottish2 Clashin Darroch | MAP33 Glengap (Scotland 1) | 0.82 | 0.45 | same |
| scottish3 Sunshine Loch | MAP34 Black Loch (Scotland 2) | 0.80 | 0.40 | same |
| scottish4 Stormy Loch | MAP35 Bennon (Scotland 5) | 0.63 | 0.29 | same |
| usa2 Truckers Tunnel | MAP62 Hualapai Nation (USA 3) | 0.88 | 0.40 | same |
| usa4 Naked Thunder | MAP64 Arizona (USA 1) | 0.34 | 0.17 | partly same |
| welsh1 Mountain Descent | MAP41 Llanberis (Wales 4) | 0.80 | 0.57 | same |
| welsh4 Foggy Forest | MAP44 Dumfries (Scotland 4) | 0.77 | 0.26 | same |
| scottish1 Sunset Stones | MAP22 Pen-y-Coed | — | 0.14 (shifted) | a section re-used at another position, rest new |
| usa1 Canyon Ridge | MAP41 Llanberis | — | 0.14 (shifted) | section re-used, rest new |
| welsh3 Lakeside Storm Clouds | MAP43 Glenmooar | — | 0.17 (shifted) | start re-used, rest new |
| kenya1-4, arctic1-4, usa3, welsh2 | none | <= 0.5 any transform | 0.00 | **PC-only stages** |

* Shared stages: the PS2 maps are larger road networks, the PC stage is one route through the
  same terrain, often moved to another rally (Welsh/Scottish PS2 maps became PC Manx, Welsh, USA).
  On the shared area the **PC mesh is denser** (1.0-3.0x vertices: manx1 1.56, manx2 3.04,
  scottish2 1.01, usa2 2.55, welsh1 3.03) and its textures are DXT/BGRA up to 512.
* **PS2-only stages:** all Kenya (Tsavo, Rift Valley, Mount Longonot, Turkana River), all Arctic
  (Kaihuavaara, Rovaniemi, Kemijärvi, Ristilampi), Twiglees, Laxey, Nevada, Bullhead, Glenmooar
  and Pen-y-Coed (only small sections re-used on PC), the 8 specials and cut MAP29.
* **PC-only stages:** Fire Rock, Twin Bridges, Vertigo Rift, Dark Safari (night), Frozen Falls,
  Glacier Run, Lowland Village, Snowy Mountain (night), The Abyss, Lake Llyn Brenig, plus the
  mostly-new Sunset Stones, Canyon Ridge, Lakeside Storm Clouds.
* Unique total across both games: 24 PC + 23 PS2-only (4 Kenya, 4 Arctic, 6 UK/USA, 8 specials,
  MAP29) = **47 stages** (9 snow, 3 night).

## 3. Weather and snow (for the later stages phase)

* PS2 `CSnowAnimator` (500 flakes with ground positions) and `CRainAnimator` (700 drops with
  splash/sound), per-stage flags (`0x02` snowfall, `0x10` rain), fog per stage.
  PC weather is per-stage text plus `config.cfg` environment values (not decoded).
* MR has no snow stages: snow needs (a) a ground/wheel spray particle for snow surfaces and
  (b) falling snow / rain in the renderer (d3d8 proxy, like the grime and rigid-prop layers).
  Course Studio already carries Evo 2 surface classes incl. Snow/Ice (`EVO2_TRACKS.md`).

## 4. Port path (no global MR reverse needed)

* **Cars:** PC full RCX -> `rcx_scene_adapter.py` (Astra) generalised to all 27 -> shared MR
  Classic pilot (`txr3_classic_pilot.create_pilot`) -> Vehicle Manager roster chain from
  `ROSTER_EVO_01.md` (`roster_rebase.py`) -> frontend class(es) via `tools/frontend_classes.py`
  (up to 5 extra classes; "4X4 EVO" uses one). The Impreza "sun" livery becomes a PAINT variant
  (`feature/vehicle-options`), not a car.
* **Stages:** PS2 `MAPnn.DAT` (flat face/vertex arrays, decoded with `wh_emulate.py`) and/or
  PC `.map` -> Course Studio, packaged like the Evo 2 tracks (`course_pack.py`, Quick Race
  category).
* **Targeted checks still required** (not a global reverse): roster capacity beyond 38 records
  (save / progress keys, AI pools, UI banks) for +27 cars; Vehicle Select carousel size per
  frontend class; MR surface -> particle table for snow spray.
