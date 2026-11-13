# R-SURFACE1 — Vehicle Grime (dust, mud, water) — research and design

Status: **G0 probe built** (2026-11-12, see [G0.md](G0.md)); visual layer not implemented. Base for code references:
`integration/base` 80bc0c1 (renderer union branch). Owner idea: roadmap entry R-SURFACE1 (2026-11-12).

## 1. Goal and hard constraints

Cars collect dust, mud and water during a stage, so long rally-raid stages read like rally-raid stages.

Constraints, all from the owner:

1. Lives **only in the D3D8 Renderer (`d3d8.dll`)**. Works with or without Extra Options (`dinput8.dll`),
   with or without Atmosphere, and with retail cars, PS2 fleet bodies, SDK, Demo and add-on cars. No
   CarID, roster or EXE dependency.
2. Must look like it belongs to the game: matte, low-frequency, regional colour, readable liveries. It is not a
   modern PBR look.
3. Cheap: measured budget below (section 8). It needs a full OFF fallback that is byte-identical to the current
   look, and quality presets.
4. Each car has its own state (the player and every AI car). Shared DXT liveries are never written.

## 2. Evidence (what the game already gives us)

| Signal | Evidence | Confidence |
|---|---|---|
| Per-surface **drive particles**, one texture per family | `DataGame/GameParticles.xml`: `particle/dirt_drive`, `dirt_drive_persist` → `particles\dirtdust2`; `mud_drive` → `particles\newmud`; `water_drive_front/rear` → `particles\watersplash3`; `grass_drive` → `particles\grassdirt`; `stones_drive` → `particles\brownstone`; `tarmac_skid` → `particles\smokey` | CONFIRMED (data) |
| Particle draw sites | billboards DrawPrimitive return RVA `0x164ed0`, trails `0x1722ee`; FVF 0x142 stride 24, **world-space** vertices, one dynamic VB, batched by texture (`modernization/renderer-recon/particles.md`, `renderer/atmosphere_native.hpp` 6.2 night particles) | CONFIRMED (runtime, ATMOSPHERE6.2) |
| Tyre tracks prove **contact only** | `Surface.xml` names `misc\tracks\{tarmac,harddirt,grass,gravel,mud,water}`, but the six files are byte-identical (black 16×16, SHA 9503245a…), so the texture cannot tell the surface; `gaSFXTyreTracks` PC `0x6e73b4` ← `0x4ca62b` | CONFIRMED (G0 hashing) |
| Car pose and identity per draw | body `general()` → `observe_car(instance, world)`; PS2 fleet `fleet_observe`; Broker `gaVehicleOutputData` vehicle+0xb0 world position, +4 gear (ATMOSPHERE6.10) | CONFIRMED |
| Material roles | Atmosphere body roles `Paint, OpaqueTrim, OpaquePanel, OpaqueCover, OpaqueHelmet, OpaqueFlat, Interior, Pilot, WheelRubber, WheelMetal, OpaqueGlazing` (`atmosphere_body_materials.hpp`) | CONFIRMED |
| Fixed-function projection works on this device | headlights use `D3DTSS_TCI_CAMERASPACEPOSITION` + texture transform (`atmosphere_native.hpp` ~264) | CONFIRMED (runtime) |
| Post-draw pass pattern | `headlight_candidate` recorded after an accepted body draw and re-issued later (`atmosphere_body_general.hpp` end of `general()`) | CONFIRMED |
| Instance pointers are reused between races | ATMOSPHERE6.15.1 (Forester inherited Megane rig) → state must reset on `race_generation` | CONFIRMED |
| Renderer is fixed-function only | no `CreatePixelShader`/`CreateVertexShader` in `ps2-research/pc-port/renderer` | CONFIRMED |
| Particle dynamic VB is CPU-readable | `buffer_provenance.cpp` tracks DISCARD/NOOVERWRITE locks; mirror availability for the particle VB **not verified** | UNKNOWN → G0 probe |
| Weather/rain | no rain system in MR PC or in the renderer | ABSENT (future hook only) |

Consequence: we do not need to reverse a wheel-surface field. The game already tells us the surface it emits for
each car, and where it emits it, because it draws drive particles with a surface-specific texture in world space
next to the wheel that produced them. That also covers **dust from the car in front**: if you drive through
its dust cloud, your car's front gets dusty.

## 3. Art direction (the "does not look out of place" rules)

* The grime is a **matte layer over the existing look**. It covers the env reflection and does not add a new
  shading model. Wet surfaces are the only thing that adds gloss.
* **Low frequency, large shapes**: spray fans behind the wheel arches, a dirt band on the lower third, a
  dust plate on the rear, light dust on the bonnet and roof. Noise tiles are about 0.8–1.2 m, never fine "PBR" grain.
* **Growth, not fade**: dirt appears first in the noise peaks and spreads (threshold growth), so a half-dirty car
  shows clean and dirty patches, not a uniformly brown tint.
* **Regional colour**: the tint comes from the course itself. By default it is the mean colour of the course's
  dirt/gravel ground textures. Presets per country are the fallback (Spain red-ochre, Turkey pale khaki, France and
  UK dark brown, Italy grey-beige). Mud is darker and more saturated than dust of the same course.
* **Caps**: lower body ≤ 85 % coverage, upper body ≤ 35 %, roof ≤ 20 %. A sponsor livery must stay readable at
  full grime. Lamps, glass, the crew and emissive layers are never painted brown.
* Mud life cycle: wet mud is dark with a slight sheen, and as it dries it turns lighter and matte (dried crust tile).
  Water rinses lower zones first and leaves streaks; it never resets the car in one frame.

## 4. Rendering technique (D3D8 fixed function)

### 4.1 One overlay pass per accepted body draw

Immediately after an owned car body draw (native PC/SDK/add-on draw or PS2 fleet replacement draw), and before
the Atmosphere headlight pass, so headlights also light the grime:

```
stream 0 : GrimeVB  (cached per geometry: pos, normal, diffuse, uv0 = grime projection, uv1 = side-view state coords)
indices  : the original index buffer and range (unchanged)
stage 0  : grime atlas      color SELECT texture     alpha SELECT texture (coverage noise)
stage 1  : car state tex    color MODULATE2X tint    alpha ADDSIGNED2X (noise + level - .5)*2  -> threshold growth
stage 2  : -                color MODULATE diffuse   alpha MODULATE diffuse.a (static zone weight x role cap)
           (+ TFACTOR = Atmosphere scene energy when Atmosphere is on, otherwise white)
blend    : SRCALPHA / INVSRCALPHA, ZWRITE off, ZFUNC LESSEQUAL, small ZBIAS, fog = the body's fog state
target   : back buffer only (never the env-capture or headlight-map targets)
```

* **GrimeVB** is built **once per geometry** (stream + range + content revision) from the CPU mirror the
  renderer already keeps. uv0 is a per-vertex dominant-axis planar projection in car-local space (tri-planar
  approximation; the noise atlas hides axis seams). uv1 maps car-local (length, height) into the state texture.
  diffuse.a holds the static zone weight: height ramp, wheel-arch proximity, rear-face bias, upward normals get
  less dust, plus the role cap. diffuse.rgb copies the source's (Atmosphere-shaded, when present) vertex colour,
  so the grime is lit exactly like the paint under it.
* It is shared by all cars with the same model. Damage creates a private clone with a new VB, so the revision
  changes and the cache rebuilds (rare event, as with `BodyShadeCache`).
* **The per-car part** is only a 32×16 A8R8G8B8 **state texture** (rgb = local tint dust↔mud↔wet-dark,
  a = level) plus TFACTOR. Updating it costs 2 KB and only happens when the quantised state changes (≤ 4 Hz).
* No CPU mirror → a fallback uses `TCI_CAMERASPACEPOSITION` × (World·View)⁻¹ × side projection with the same
  stages (no per-vertex zone weight; the static weight is baked into the state texture instead).
* Two-stage hardware (no third blend stage) → Low preset: the zone weight is baked into the state texture alpha.

### 4.2 Wet sheen (only while wet > 0)

An extra additive pass reuses the env texture that the body draw bound to stage 1
(`TCI_CAMERASPACENORMAL`, same transform flags), ONE/ONE, scaled by wet level × a separate 32×16 A8 wet mask. Clean
wet paint reflects more and wet mud reflects a little. Dry dust has no sheen pass at all, and the overlay itself already
covers the native env term where it is opaque.

### 4.3 Wheels and glass (later phases)

* Wheels: the same overlay on `vehicles/<f>/wheel` draws (rubber and rim roles) with uniform mud/dust level, no
  spray pattern.
* Glass: light dust on side/rear glass, and a **wiper arc** on the windscreen, which stays clean inside the arc. The
  arc comes from a planar mask in the windscreen's local frame. The windscreen is identified by the existing glass
  role, never by a texture-name guess alone.

## 5. Per-car state and signal pipeline

```
CarGrime { instance, race_generation, pose, local bounds, wheel centres (from wheel draws),
           dust[z], mud[z], wet[z], mud_age[z]  for zones z = front-low, front-arch, side-low-L/R,
           rear-arch, rear, bonnet, roof }
```

* **Exposure sampling** (every 4th frame): for each particle DrawPrimitive whose texture level-0 SHA belongs to
  one of the six families, read the triangle centroids (≤ a few hundred). Attribute each centroid to the nearest car
  whose inflated bounds (+2.5 m) contain it, and map it to a zone by its car-local side (front/rear/left/right/height).
* **Rates** (INI, defaults to tune in G2): `dirtdust2` → dust; `newmud` → mud (+wet); `brownstone`/`grassdirt` →
  light mud+dust; `watersplash3` → wet + wash (lower zones first); `smokey` (tarmac) → nothing (optional slow dust
  loss). Exposure is scaled by speed from the pose delta, so idling does not paint the car.
* **Tyre tracks** can only confirm contact (all track textures are identical); low-speed wading relies on the water
  particles.
* **Drying**: wet decays over about 45 s (faster at high sun energy). Mud moves wet-dark → dry-light over about 90 s.
* **Lifecycle**: reset on a `race_generation` change. Quick Race starts clean or at `StartLevel`. Paused and replay
  time never accumulates. **Master Rallye mode** keeps the grime per saved checkpoint, so leaving and loading a stage
  again shows the same dirt (`MasterRallye/*` campaign + checkpoint key, renderer-side store; see G0.md). Service
  Park wash: `CarGrime::wash()` entry point is in place, and the UI trigger comes with the Service Park.
* **Rain** is a reserved input (`WeatherWet`), for a future WEATHER line: wet roof and bonnet, wash streaks.

## 6. Compatibility

| Area | Rule |
|---|---|
| Add-on/SDK/Demo cars | identified by resource `vehicles/<folder>/car` and by draw ownership, never by CarID. Zones come from the car's own bounds and wheel draws. Optional sidecar `grime.ini` in the car folder (exclusions, caps, wiper arc). With no sidecar, defaults apply. |
| PS2 fleet bodies | hook in `draw_car_fleet` (`race_car_fleet_native.hpp`) next to `fleet_observe`, using the same GrimeVB builder from the PS2 vertex arrays. |
| Material safety | Atmosphere `BodyCapabilities` roles when loaded. Without them, a conservative fallback: opaque, non-blended, non-additive, non-emissive draws whose texture is not in the exclusion list (glass, light, lamp, glow, blight, tyre, rubber, rim, pilot, driver, interior). Unknown → **skip** (fail closed visually). |
| Atmosphere | optional: TFACTOR = scene energy (same formula family as `particle_night_factor`), shaded diffuse is reused, and the pass runs before the headlight pass. Atmosphere off → static white factor, native prelit colours. |
| Extra Options / Menu Builder | not involved in the particle/surface path. Settings live in their own `VehicleGrime.ini`. A menu may later edit that file; the renderer never requires dinput8. |
| Reflections | grime is never drawn into the env capture or the headlight map. Car-exclusion hulls are unaffected. |
| Damage | private damaged trees get a new VB → GrimeVB rebuild. Grime state is per instance, not per geometry, so it survives damage. |

## 7. Configuration (own file `VehicleGrime.ini`, opt-in)

```ini
[VehicleGrime]
Enabled=0            ; 0 = byte-identical current look
Quality=2            ; 0 off, 1 low (2 stages, no sheen), 2 medium, 3 high (wheels+glass+sheen)
StartLevel=0.0       ; Quick Race start state
Rate=1.0             ; global accumulation multiplier
DryTime=45
TintSource=auto      ; auto (course ground) | preset | rgb
MaxDistance=80       ; metres; farther cars skip the pass
Families=MRRRenderer\grime\families.ini
```

## 8. Performance budget

| Item | Budget |
|---|---|
| Extra draws | 1 per owned body draw (about 3–6 per car); +1 sheen only while wet; cars beyond `MaxDistance` skipped |
| CPU per frame, 8 cars | ≤ 0.3 ms (sampling every 4th frame; state texture upload ≤ 4 Hz per car; GrimeVB cached) |
| VRAM | atlas 256² DXT5 (≈ 64 KB) + 8 × 2 KB state + GrimeVB cache ≤ 2 MB |
| Measurement | own `PerfTiming` category `grime`, F-key A/B (same mechanism as PERF-ATMO1 F8) |

## 9. Phases and acceptance

| Phase | Content | Acceptance |
|---|---|---|
| **G0 probe** (diag only, no visuals) | log particle draws by texture SHA, attribution to car poses, tyre-track textures; verify particle VB mirror | owner run on a dry course, a mud course and a water crossing: per-car exposure timeline in the race ledger matches what was driven |
| **G1 static look** | offline tool: procedural grime atlas (no third-party art) + preview renders on `car.dx` for 3 cars (like `atmosphere_lamp_rig.py`); in game a fixed `StartLevel` | owner approves the look on retail PC, PS2 fleet and one add-on car; OFF = identical frame |
| **G2 dynamics** | accumulation, wash, drying from signals; all AI cars | clean → dust → mud → water → dry → clean sequence in one race; FPS within budget |
| **G3 extras** | wheels, glass with wiper arc, wet sheen | no brown lamps/glass; night and Atmosphere OK |
| **G4 persistence** | championship carry-over, Service Park "Wash Vehicle" through EO/Menu Builder | only after the lifecycle/save sidecar is qualified |

## 10. Rejected alternatives

* **Per-instance livery texture copies** (CPU/GPU compositing into private DXT copies): 8 cars × 256–512² ×
  several textures per body, recompression and re-upload on every change, and it breaks when liveries or texture
  identities change. It also fights the identity contracts that the fleet/reflection modules use. Rejected.
* **Render-to-texture dirt masks in UV space**: car UV atlases are not unique on many retail and add-on cars
  (mirrored and shared islands), so the dirt would mirror left↔right. Rejected for the default path.
* **Pixel shaders**: the renderer is fixed-function everywhere, and introducing a shader path only for this would
  break the "same pipeline as the rest" rule and the Classic fallback. Not needed for this look.
