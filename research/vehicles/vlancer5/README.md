# V-LANCER5 — glass, source-qualified reflections and native brakes

2026-10-23 · `research/vehicles` · private candidate, **offline qualified**.

## Candidate and boundaries

Run `.research-output/vehicles/vlancer5/candidate-01/Launch-V-LANCER5.cmd`.
The candidate uses the existing qualified independent Lancer registration
(CarID 27 / T2, with the existing Mercedes T1 package). It does not replace
the frozen Subaru or SCALE1 directories or expand capacity. V4 gameplay and
SCALE1 29/30 gameplay are confirmed by the user; **V5 is not gameplay confirmed**.

Original EXE SHA256 remains
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`;
existing graphics DLL remains
`eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4`.
Neither file was written. No commits, pushes, physics tuning, wheel moves,
capacity work or Randomizer changes were made.

## A. Windows and stickers

The GT4 rear side-window sticker is menu shape 26 / race shape 37. Its source
passes use source-alpha blending, disabled ZWrite and FBMSK `FF000000`
(destination-alpha preservation). The underlying glass (menu 24 / race 35)
has its own blended passes, ZWrite and alpha 105/128. Source RGB, UVs,
normals and vertex colours remain intact.

MR's instance constructor `00583940` sets A8/A9 to one; submission
`00576970` overrides shader ZEnable/ZWrite from those fields **after** shader
setup. Thus alpha-zero sticker texels can own depth and reject later glass.
The old Previewer shader-only ZWrite concealed this failure. This is an
evidence-based explanation consistent with the supplied runtime screenshot;
the exact original-game queue sequence is not captured here.

The editable profile selects these no-ZWrite overlays for a **depth-safe
cutout fallback**, source threshold 32/128. Invisible texels are discarded
before depth writes. Original sticker content remains; glass stays blended.
Soft sticker edges become harder: this is an explicit MR approximation, not
exact destination-alpha emulation. Shape selection is data, not a MatN rule.
Invalid thresholds, duplicate selectors and ambiguous option types fail closed.

## B. Reflections

The old whole-draw/global-atlas pairing admitted only seven painted body
regions. GT4 splits environment primitives across packet boundaries and uses
atlas alpha independently for coverage and DATE reflection gating.

The new opt-in shared interpreter matches **oriented source triangles** across
packets, requires complete base-draw correspondence, validates actual GS
environment state and separately proves coverage. It checks the full bilinear
UV footprint with a bounded triangle/texel-support intersection, respecting
wrapping. It rejects ambiguous, reversed, unmatched or inactive passes.
Geometry is not split or invented, and colours/material numbers do not decide
paint classification.

Both menu and race now have **31 reflective body draws**: 7 legacy exact pairs,
18 newly proven opaque UV footprints and 6 exactly representable GREATER128
cutouts. Wheels keep their existing mapping. Reflection weight still follows
source alpha and DATE; stickers, rubber, glass and lights do not receive a
blanket environment flag. The user-supplied stock MR helper and source RGB
gain approximate PS2 runtime environment generation.

**Damage limitation:** six reflective cutout regions share coverage and
reflection weight in one MR alpha channel. The existing V4 ownership bridge
preserves their coverage, so reflection fading there is approximate. Opaque
paint retains native damage reflection fading. Full PS2 lighting, framebuffer
alpha composition and texgen parity are not claimed.

## C. Native brake lights

The editable profile selects actual GT4 callback 0, source case 0/1; callback
7 controls the front lights and is not used. Source command/shape/packet
identity isolates the original branches rather than ordinal draw positions.
The source ON branch supplies two textured draws: centre stop bar (4 tris)
and both upper red rear lenses (8 tris).

The shared native writer emits stock `blight` tag7/tag8 grammar:
case 1 contains two original OFF materials; case 2 contains two ON cores and
one glow material. The normal native controller selects case 2 only above
brake 0.1. No executable/controller patch or permanently lit diffuse is used.
Original code `004CA1D0` plus setter `004D3C50` was executed in isolated x86
emulation; brake 0, .099 and .1 select 1, .101 and 1 select 2. Only two exact
resource getters are mocked. This does not prove live named-switch binding.

ON cores preserve actual source lens geometry, RGB and UVs, with explicit
cutout coverage. Like stock lit materials they bypass damaged diffuse colour.
Glow uses stock falloff intersected with source lens alpha, packed into one
new texture. It follows the same source triangles with a 1 mm normal offset,
without enlarged billboards. Zero glow texels lie outside the source mask.
Core edge quantization and reduced bloom are intentional confined fallbacks.

## D. Previewer and diagnostics

The standalone viewer now defaults to the qualified constructor's instance
ZWrite behavior. `Z` or `--depth-write shader` exposes the old shader-only
diagnostic; neither mode claims every native caller uses the same override.
The environment matrix now uses native M41/M42 translations .5 rather than
normal-dependent M31/M32. CLI azimuth/elevation/zoom support repeatable views.
Native multi-material brake cases are decoded by their counted envelopes.

Comparisons, all rendered from real resources with the same updated viewer:

- `.research-output/vehicles/vlancer5/preview-01/glass-comparison.png`
- `.research-output/vehicles/vlancer5/preview-01/reflection-comparison.png`
- `.research-output/vehicles/vlancer5/preview-01/rear-brake-comparison.png`
- `.research-output/vehicles/vlancer5/preview-damage/`: actual original-CPU
  damage replay buffers, reflections ON/OFF and brakes ON/OFF. These body-only
  diagnostic scenes intentionally do not assemble separate race wheels.

The viewer remains a fixed-function diagnostic approximation: world lighting,
fog, exact native queue sorting, inherited per-instance flags and suspension
are not fully reproduced. Its neutral background is not a gameplay capture.

## Validation

Evidence is private under `.research-output/vehicles/vlancer5/`.

| Check | Result / evidence |
| --- | --- |
| Deterministic original-source rebuild and DX/DXT references | `offline-final.json`: PASS |
| V4 reproducibility after shared changes | `v4-repro-final.json`: PASS |
| No baseline triangle/UV/normal/vertex-colour omissions | `material-validation.json`: PASS |
| Frontend geometry / wheel | 0 added triangles / wheel byte identical |
| Race additions | Exactly 12 lit + 12 glow source-conforming triangles |
| Collision, physics, wheel instances, UI PNG/artwork | Unchanged |
| Original CPU damage plus V4 bridge, 36 synthetic impacts | `damage-01.json`: PASS; native XYZ/RGB unchanged, coverage alpha losses 115 -> 0 |
| Original native brake controller CPU replay | `native-brake-controller.json`: PASS |
| Stock Navara/Pajero GPU reflection and brake toggles | `stock-*-gpu/validation.json`: PASS |
| GPU asymmetric UV and front/back culling fixtures | PASS |
| Synthetic transparent-depth stress | Cutout preserves 35,413 glass pixels; old blending with instance ZWrite leaves only 147 edge pixels |
| Full synthetic suite | 637 tests, no failures/errors; one old private-fixture skip |
| Actual installed EXE / graphics / allocation preflight | `installed-preflight.json`: PASS, game not launched |
| Missing / truncated / modified native extension | `negative-extension.json`: all rejected |
| Frozen Subaru and SCALE1 29/30 manifests | `frozen-candidates.json`: PASS |
| Shared immutable non-Lancer runtime resources | 148 byte-identical; mutable saves/options excluded |

The final resources are reproducible from `build-final`; `candidate-01`
contains identical resource bytes. Texture cache charge is 10,969,088 bytes,
65 referenced textures, only 64 KiB above V4 and within the 16 MiB authoring
budget. No claim about unchanged live frame timing follows from this budget.
The sealed runtime has 217 resources. Native patch operations and reconstructed
reference image equal V4; the existing source-bound damage ownership payload
has revised data, 62,101 bytes within its existing 64 KiB allocation.

## Reproduce / use with another user-supplied GT4 car

Use `tools/build_gt4_vehicle.py` with local `--source-root`, explicit editable
`--profile`, user-owned stock `--donor`, and a **new** `--output` directory.
The V5 profile is `research/vehicles/vlancer5/lancer-source-profile.json`.
Keep the source hashes/model/LOD/rig settings for the actual input. Opt in to
`qualified_environment` per menu/race; select window overlays only after source
state inspection. Select an evidence-backed brake callback and OFF/ON cases;
do not copy Lancer shape IDs or callback numbers to another car.

Run `tools/validate_gt4_vehicle.py` against the same source/profile/donor and
new candidate. `tools/validate_vehicle_materials.py` compares a material
revision with its own baseline. `tools/preview_vehicle.py` supports `--brake`,
`--no-reflections`, `--depth-write`, camera presets and isolated layer inspection.
Source support never depends on bundled GT assets.

For this local candidate the build command is:

```powershell
python tools/build_gt4_vehicle.py --source-root D:/Game/GT_Model-Tools/VOL/GT4-Beta_Extracted/extracted --profile research/vehicles/vlancer5/lancer-source-profile.json --donor ../corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Navara --output .research-output/vehicles/vlancer5/my-new-build
python tools/prepare_gt4_addon.py --candidate .research-output/vehicles/vlancer5/my-new-build --donor ../corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Navara --profile research/vehicles/vlancer5/lancer-source-profile.json --ui-from .research-output/vehicles/vlancer4/candidate/project --output .research-output/vehicles/vlancer5/my-new-project
```

Then project-build using the existing `mrtool addon project-build` workflow and
seal with `prepare_vehicle_damage_runtime.py`, as in V4. The UI reuse option
copies qualified artwork byte-exactly; it does not regenerate unrelated assets.

## Human test gate

Check both sticker windows against scenery and the opposite side, rotate the
frontend, compare reflections ON/OFF, press/release the brake at the rear and
oblique angles, then repeat after side/rear impacts. Confirm no transparent
rectangle, lost stickers, body glow, permanently lit lamps, new holes or wheel
regression. Finish and re-enter a race. V5 is ready for these checks, not a
substitute for them. Do not overwrite the frozen candidates with this directory.

## Collision investigation

See [collision.md](collision.md). Existing SDK collision translation and scale
code is byte-identical to `master-rallye-re-blend`; no collision adjustment is
applied to this candidate.
