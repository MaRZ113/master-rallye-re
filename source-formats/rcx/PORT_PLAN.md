# RCX / Rally Championship -> Master Rallye: port plan

Status: plan, 2026-11-16. Base host for every candidate: `host-evo-tracks-01`
(`master-rallye-re-base/.research-output/hosts/`). Facts: `INVENTORY_PC_PS2.md`.
Cars go through the Vehicle SDK, stages through Course Studio; no global MR reverse is
planned. The targeted checks are listed per phase.

## Decisions

* **Car source = PC full models** (`Data/Cars/*.rcx`: about 62 parts incl. damage, 512 textures).
  PS2 car blobs are reference only.
* **Stage source by geometry:** for the 11 shared stages use the **PC mesh** (denser, better
  textures) and keep the PS2 table data (real name, fog, sun, rain flag) as metadata. PC-only and
  PS2-only stages come from their own version. Coordinates: PS2 = PC with X negated.
* **Classes (pilot for all future games):** three new frontend classes, named by category, not
  by game, so later imports (Michelin, Rally Trophy, CMR, GT) join them:

  | Class | RCX cars |
  |---|---|
  | `WRC` | Impreza 98 / 2000 / 2001, Lancer Evo V / VI, Peugeot 206, Focus, Cordoba, Octavia, Accent (10) |
  | `KIT CAR` | 2.0 kit cars Astra, Golf, Megane, Ibiza, Escort Maxi, Hyundai Coupe; 1600 Saxo, Civic, 106, Proton, Puma SP; road Puma, Felicia, Micra (14) |
  | `CLASSIC` | Audi Quattro, Lancia Stratos, Mini Cooper (3; Michelin Group B and Rally Trophy cars later) |

  With "4X4 EVO" and the planned trucks class this uses all 5 extra frontend classes of
  `tools/frontend_classes.py`. The Impreza 2000 "sun" livery is a PAINT variant.

## Phase order (first -> last)

### 1. Car pilot: one car per class
Impreza 2000 (+ sun paint), Astra (existing pilot), Audi Quattro.
* Generalise `rcx_scene_adapter.py` from Astra to any car (parts, wheels, glass, brake lamps,
  texture/UV conventions incl. the mirrored-livery issue) -> shared MR Classic pilot.
* Physics: map RCX `CarStats/*.cog` and PS2 `TWEAK0.PAR` (`<Car>.twk`) to an MR donor of
  similar layout (4WD / FWD / RWD).
* Roster chain from `ROSTER_EVO_01.md` + three frontend classes. Owner test.
* Check: Vehicle Select carousel size per frontend class (14 cars in KIT CAR).

### 2. Capacity audit (before the full roster)
38 -> 65 records: save / progress unlock keys, byte-sized CarID fields, AI pools, UI banks,
generated-code limits. This is a targeted audit, not a global reverse.

### 3. Remaining 24 cars
Batches by class (WRC, then KIT CAR, then CLASSIC), one roster rebuild per batch. Damage parts
and brake-glow layers follow the Brake Glow Studio work when it lands.

### 4. Stages wave 1: the 11 shared stages, PC geometry
Llandudno/Harbour Mist, Gartheiniog/Plantation, Baldrine/Coastal Edge,
Knocksharry/Curraghs, Glengap/Clashin Darroch, Black Loch/Sunshine Loch, Bennon/Stormy Loch,
Hualapai/Truckers Tunnel, Llanberis/Mountain Descent, Dumfries/Foggy Forest (+ Arizona/Naked
Thunder once night is ready).
* PC `.map`: materials, textures, objects (QTO/MSH, `config.cfg`), surfaces and collision ->
  Course Studio (same chain as `EVO2_TRACKS.md`: build -> `course_pack.py` -> Vehicle Manager).
* The shared pairs let every decoded field be cross-checked against the PS2 data.
* Fog per stage from the PS2 table. Category "RCX" in Quick Race.
* Check: course registry capacity for 30 Evo + 47 RCX courses (Won/BestTime arrays, string pool).

### 5. Stages wave 2: PC-only, no snow
Fire Rock, Twin Bridges, Vertigo Rift (Kenya), Lake Llyn Brenig, Lakeside Storm Clouds,
Sunset Stones, Canyon Ridge (sandstorm), The Abyss.

### 6. Stages wave 3: PS2-only, no snow
`MAPnn.DAT` face/texture/object decode, then Kenya (Tsavo, Rift Valley, Mount Longonot,
Turkana River), Twiglees, Laxey, Glenmooar, Pen-y-Coed, Nevada, Bullhead, the 7 non-snow
specials, cut stage MAP29.

### 7. Weather: rain and night
Renderer (d3d8 proxy) rain module after PS2 `CRainAnimator` (700 drops, splash, sound), wet
look via the existing grime/wet-sheen layer; night stages Dark Safari, Naked Thunder (+ Snowy
Mountain in phase 8) with the Atmosphere lamp/night path.

### 8. Snow (last)
* Ground snow particles for snow/ice surfaces (wheel spray, settled powder): check the MR
  surface -> particle table first; if it is not data-driven, add a proxy-side emitter.
* Falling snow after `CSnowAnimator` (500 flakes).
* Snow/ice grip in MR physics (RCX/PS2 have snow and ice tyre types).
* Stages: Frozen Falls, Glacier Run, Lowland Village, Snowy Mountain (PC), Kaihuavaara,
  Rovaniemi, Kemijärvi, Ristilampi, Hanhikoski (PS2).
