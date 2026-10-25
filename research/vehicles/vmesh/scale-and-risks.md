# V-MESH2 scale, omitted geometry and renderer-risk analysis

Evidence labels: **MEASURED** (from the validated bundle files), **CODE** (from existing SDK source/docs),
**UNKNOWN** (needs the human runtime test). Numbers come from `reports/validation-report.json`.

## 1. Oversized proportions (accepted for the first test)

| | Real/GT Impreza | In game (x1.1634) |
|---|---|---|
| Wheelbase (MEASURED, LOD0 arches) | 2.54 m | 2.96 m (= Navara's rendered hub spacing) |
| Length / width | 4.39 m / 1.82 m | 5.11 m / 2.12 m |
| Roof (p99, excl. antennas) | 1.27 m | 1.48 m |

Cause: wheel positions come from the donor. Navara hubs (x +-0.855, y 0.401, z +1.495/-1.463) are fixed by the donor
physics family and the donor `wheel.dx`/embedded wheels. J.3-A only **clones donor physics rows** (`j3/physics.md`), so the body is
scaled to fit the donor wheels instead of the reverse. Consequences: the car is ~16 % too large; the wheels (r 0.383) look
small for the body; Navara handling, mass and dimensions apply.

**Future native-scale solution (not implemented):**
1. Author a physics family with Impreza `Dimensions` (wheelbase 2.54, track ~1.5, wheel radius ~0.33). Needs physics authoring
   support beyond J.3-A's cloning. **UNKNOWN:** how XML dimensions map to the visual wheel anchors - Navara's XML wheelbase is 2.80
   but the rendered hubs are 2.958 apart, so a runtime capture/analysis is required before editing.
2. Scale `wheel.dx` and the four wheel draws in `complete.dx` by r/0.383 (existing wheel topology edit is human-confirmed).
3. Re-fit the collision hull with scale ~1.0 and rebuild with `--scale 1.0` plus new hub constants (converter already takes `--scale`).
4. Re-measure arch relief and the camera/driver positions.

## 2. Omitted GT geometry (MEASURED, LOD1: 2,263 tris)

| Category | Tris | Why omitted | Effect |
|---|---|---|---|
| `*_reflection` env shells | 928 | duplicate of the body drawn with an env map in GT | none expected; the Master Rallye body draw has its own env helper (`silverpaint-tga`, only with Reflections on) |
| lit tail-lamp overlay | 36 | duplicate of the unlit lamp | no GT-style lit state |
| untextured `Mat-1` shell | 38 | duplicate | none |
| GT cabin shell (`shape28`) | 178 | `car.dx`: donor interior kept; `complete.dx`: used as draw 0 | car.dx shows Navara dash/seat through the windows |
| model1/model5/model6 (shadow, underbody) | n/a | not body geometry | none |

Not available at all: GT wheels (separate dump failed in the tool; donor wheels are kept), GT livery/decals (UVs discarded).

## 3. Hidden filler draws (MEASURED)

Master Rallye draws cannot be empty, so unused Navara draws become one 2 cm triangle (area 2e-4 m2, valid normal, donor vertex colour,
UV centre) at (0, 0.45, 0): **24 draws in car.dx, 16 in complete.dx**. They sit inside the cabin volume.

| Risk | Rating | Notes |
|---|---|---|
| Degenerate/invalid geometry (NaN, zero area) | LOW | all positions finite; every filler has area 2e-4 m2 and a unit normal (MEASURED) |
| Draw-record corruption | LOW | writer reparses; 37/37 and 26/26 draw tags, control words, texture strings, flags identical to donor; same diagnostics |
| Alpha-blended fillers | LOW-MED | car.dx draws 26,27,30-34,36 (windscreen groups and brake glow) are alpha draws; one invisible-sized triangle each. **UNKNOWN** if the sorter/state change per draw costs frame time (it adds a few state changes only) |
| Glass/damage state machine (tag-7 parents 26,28,31,33,35 and tag-8 children) | MED | hierarchy is byte-identical to donor, but only draw 35 carries real glass and its cracked child 36 is a filler: on windscreen damage the visible glass may disappear or show nothing. Side/rear windows have no breakable variant. **UNKNOWN** until a damaged-glass run |
| Brake lights | MED | brake-light/glow draws (28-30) are fillers: no brake glow. Tail lamp (draw 24) is a static red mesh |
| Fillers visible from some camera | LOW | at the cabin centre, below the roof; inside the GT body in all measured views |
| Procedural damage deformation | LOW-MED | R4F/R4G topology edits kept damage working in human tests; this edit is much larger (draw 3 now 926 vertices vs donor body) - **UNKNOWN** deformation look |

## 4. Other renderer/loader risks

| Item | Rating | Notes |
|---|---|---|
| Vertex/index limits | LOW | max 926 vertices in one draw (limit 65,536); total 2,758/3,031 verts < donor 3,248/3,397 |
| DXT/texture format | LOW | only `colour-tga.dxt` changed, same 16x16 header/size (R4E, human-confirmed path) |
| Texel sampling with all UVs on one texel | LOW | pixel-centre UVs, uniform textures; mip/filter harmless. Glass centre texel is grey alpha 133, lens light grey, tail lamp red (stored raster orientation unknown, red in either) |
| Paint darkness | MED | donor vertex colours are ~0.4 grey (102/255); a flat (35,95,230) texture may look dark. Adjust `PAINT_RGBA` after seeing it |
| Environment/chrome shading on body | UNKNOWN | draw 3 keeps `silverpaint` helper (env pass with Reflections on); GT normals are smooth per vertex |
| Normal vs winding agreement | LOW | 99.5 % of 3,249 corners agree (15 disagree, mostly relieved arch vertices) |
| Bounds footer | LOW | recomputed by the writer; validated; hull sits inside it |
| Wheel/arch clearance | LOW-MED | arch relief applied (margin 0.03 m) so no body vertex lies inside a donor wheel cylinder; lips may be locally deformed |
| Navara interior in car.dx | LOW-MED | draws 0,1,2,16-20 kept; 20 points lie outside the GT body bbox (underbody 7.7 cm below the floor); interior is Navara-shaped |
| Hull is still a Navara-shaped convex hull | MED | scaled per axis (1.026, 0.952, 0.975) and moved (0, -0.037, +0.225) to the GT extents (roof excl. antennas); front/rear shape and wing are approximated by a box-like hull |
| Menu icon | MED | Vehicle Select/SmallCarSheet art use stock frames (manifest policy); thumbnails will not show the Subaru |
| Slot qualification | HIGH | ID27/T2 with a custom family has no human-qualified GlacierSprint baseline yet |

## 5. Not covered (explicit)

Livery/texture fidelity, native proportions, lit tail lamps, glass-break authoring, driver/crew fit to the new cabin, wheel replacement,
physics retuning, other modes (AI selection, Master Rallye saves, Invitation) - all inherited from the J.3-B qualification boundary.
