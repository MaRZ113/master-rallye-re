# PS2 content fixes: CREW-FACE1 package (Navara face, Tata and Kamaz right windows)

Status: **prepared, not applied.** Nothing is built, committed or registered, and no asset is written yet.
These are defects that also exist in the original PS2 game. The fixes are meant to sit behind an
opt-in INI key, `PS2ContentFixes=1`. The default `0` keeps the original PS2 content.

Files:
- `prepare_ps2_content_fixes.py`: one generator for every fix. It checks each source pin, builds the
  corrected asset in memory, re-checks it against the renderer's PS2MDL02 decode rules and writes
  `evidence/<FIX>.json` and `evidence/package.json`. Assets are written only with `--write`, always
  under a NEW filename. Originals are never opened for writing. `--write` skips the CANDIDATE fix
  unless you add `--include-candidates`.
- `evidence/`: per-fix evidence (triangles, vertices, texel statistics, coincidence distances, PS2
  source switch tables, reference families), plus `package.json` with every original/fixed pin.

```bash
python -I docs/vehicle-fleet-port3/crew-face1/prepare_ps2_content_fixes.py
```
```bash
python -I docs/vehicle-fleet-port3/crew-face1/prepare_ps2_content_fixes.py --write
```

Repeated runs give the same bytes. No fix changes a vertex record (xyz, normal, colour, UV), a
texture, or a header count (meshes, vertices, indices, textures). The set of referenced vertices also
stays the same, so the per-vertex damage contracts stay valid.

## Per-fix status

| fix | status | role / registry line | original → fixed (sha256, bytes) |
|---|---|---|---|
| NAVARA-CREWFACE1 | user-reported, prepared | race CAR, `renderer/race_fleet_registry.hpp:677` | `NAVARA-CAR-FLEET.ps2model` `336318a5…caee0e` 372926 → `NAVARA-CAR-FLEET-CREWFACE1.ps2model` `586fd3d717007e407e0ffe8894b37e3ae78377c35cb4abe43617f54a96fd194e` 373616 |
| TATA-WINDOW1 | user-reported, prepared | race CAR, `renderer/race_fleet_registry.hpp:684` | `TATA-CAR-FLEET.ps2model` `20262ea1…d18660` 420088 → `TATA-CAR-FLEET-WINDOW1.ps2model` `8a03e06623a849335e8568b5b613a352cebeb4b9c56a617e9a6320d69f0b0252` 420814 |
| KAMAZ-COMPLETE-WINDOW1 | user-reported, prepared | frontend COMPLETE, `renderer/frontend_fleet_registry.hpp:689` | `KAMAZ-COMPLETE-FLEET.ps2model` `df3d5833…3826c` 827015 → `KAMAZ-COMPLETE-FLEET-WINDOW1.ps2model` `9351c7a6cb39cd9ce49695b94c5b3b6f7bb70646870d0e1615d86f26f4c005e5` 827756 |
| KAMAZ-CAR-WINDOW1 | **candidate, not user-observed** (same defect found by scan) | race CAR, `renderer/race_fleet_registry.hpp:671` | `KAMAZ-CAR-FLEET.ps2model` `1807d3e6…6d401fa` 463264 → `KAMAZ-CAR-FLEET-WINDOW1.ps2model` `763c3a892378faaf8685cd2b09d89e4f376338e81d4164835b2a4b7937adccf1` 463996 |

The only size change in each case is the added `deliberate_deviations` metadata record.

Side convention: model **-x is the vehicle's right**. These are left-hand-drive models: the Navara
driver sits at x=+0.31 and the co-driver at x=-0.34.

## 1. NAVARA-CREWFACE1: co-driver white face (wrong material slot)

- `mhelmet32` (root.18) holds no face. Both helmets sample identical visor texels. root.18 has 16
  side triangles whose UVs differ between the two seats, but NewRav root.3 has the same asymmetry and
  shows both faces, so those are not the cause.
- The faces are drawn from `underdash2-tga`, which holds two face images. The driver face is root.0
  (carflat) triangles 519–551, 568 and 569. The **co-driver face is root.15 triangles 0–26**
  (vertices 3482–3518). Its UVs land exactly on the second face image. root.15 is the lamp material
  (`mlamp32` + glass, carshiny, mixed reflection), so the face samples a near-white lamp disc
  (mean RGB ≈ 216/226/230). With underdash2 the same UVs give about 74/39/33.
- All 10 other crewed families carry the identical 27-triangle co-driver face in their underdash2
  carflat mesh: NewRav, Kia, Land Cruiser, Frontera, Chevy Blazer, Kamaz, Kangoo, Jump, Bruno and Astero.
- Fix: an index reorder moves the 27 triangles to the end of root.0. root.0 becomes (0, 1848).
  root.1–root.14 shift their first index by +81. root.15 becomes (5754, 12), keeping its 4 lamp
  triangles. root.16 and later are unchanged.
- Expected result: the co-driver face is drawn like the driver face (carflat, no reflection layer,
  opaque) and shows the second face image.

## 2. TATA-WINDOW1: right side window cracked from the start

- The original PS2 `CAR.PSM` has named glass switches. `screenleft` (root.26) and `screenfront`
  (root.28) choose selector 1 = `windscreen32` (intact) or selector 2 = `windscreenc32` (cracked).
  **`screenright` (root.25) and `screenrear` (root.27) have no child meshes.** The right window pair
  was authored as plain, always-drawn root children instead:
  - root.21 (`windscreen32`, carglass mode 20) triangles 0–3: the intact right window, x -0.78…-0.64;
  - root.22 (`windscreenc32`, carglass mode 20), 4 triangles, vertices 3150–3157: the cracked copy,
    at the same position (distance 0.0), with its own UVs onto the crack texture.
  Both draw every frame, so the crack is visible at race start. This explains what you saw in the
  original game.
- Fix: root.22's 4 triangles become zero-area triangles (u,u,v) over the same 8 vertices, so they
  draw no pixels. The mesh row, its mode, its textures and the index count stay the same, and the
  intact root.21 glass is untouched.
- Expected result: the right side window looks intact (single windscreen32 glass layer, like the
  other intact panes), at race start and for the rest of the race.
- Deviation: the fleet asset never shows this window cracked. On PS2 it was always cracked, because
  the right window had no switch. This asset does not include the conditional `screenleft` and
  `screenfront` paths (`excluded_source_conditional_paths`); whatever handles those today is unchanged.

## 3. KAMAZ-COMPLETE-WINDOW1: right side window broken in the menu model

- `KAMAZ-COMPLETE-FLEET.ps2model` (frontend, 22 meshes). The COMPLETE source has no switch nodes,
  so every mesh is drawn.
  - root.19 (`windscreen32`, mode 20, 36 triangles) holds the intact glass: right window triangles
    0–3 (x -0.944…-0.921), **left window triangles 4–7 (mirror, x +0.92…+0.94, no cracked copy)**,
    the windscreen and the lamp glass.
  - root.20 (`windscreenc32`, 4 triangles, vertices 8832–8839) sits exactly on top of root.19
    triangles 0–3 (distance 0.0).
- Fix: as for Tata, root.20's 4 triangles become zero-area. Every row is unchanged, including the
  Kamaz tread U-wrap mask, which is keyed by mesh number.
- Expected result: the right window matches the left (intact).

## 4. KAMAZ-CAR-WINDOW1: candidate, same defect in the race CAR

A scan of every fleet asset for cracked glass on top of intact glass found exactly three cases:
Tata CAR, Kamaz COMPLETE and **Kamaz CAR** (root.18 on top of root.17 triangles 0–3; two corners
differ by 1.24 cm). Its source shows the same empty `screenright`. You have not reported or checked
it, so `--write` skips it unless you pass `--include-candidates`. Confirm in a Kamaz race first.
Tata COMPLETE (`TATA-COMPLETE-FLEET-FIX1`) has no cracked glass. Chevy Blazer, Kia and Seat Buggy
COMPLETE use `windscreenc32` in meshes that don't sit on top of intact glass, so they are not part
of this package.

## Deliberate deviations (all opt-in, default off)

Each fix departs from original PS2 content on purpose, only for one family and role and one defect.
It changes topology or material binding only. Nothing is relit or recoloured globally, and no other
mesh's content changes. The details are listed per fix above and in each asset's
`deliberate_deviations` metadata record. I make no claim of pixel parity, and none of these has been
seen in game yet.

## Renderer design: choosing original vs corrected asset

The corrected assets keep every count, mesh order, mode and texture binding of their original. So
every per-mesh table keyed by the *original* profile stays valid unchanged: `mixed[]`, `wrapU[]`,
`mixedReflection[]`, `kFleetSources*`, `complete_tread_u_mask(sha)`, fleet damage (per vertex),
brake, lamp and probe registries. My recommendation is to leave the profiles as they are and add a
separate variant table:

```cpp
struct PS2ContentFix { const char* id; unsigned role; /*0 frontend COMPLETE, 3 race CAR*/ const char* originalSha;
                       const char* filename; const char* sha; size_t size; };
inline constexpr PS2ContentFix kPS2ContentFixes[]={
 {"NAVARA-CREWFACE1",3,"336318a5cc30f0cd7bf3c6f9addcf7e10848a1d762f5e7e88abee7f2f8caee0e","NAVARA-CAR-FLEET-CREWFACE1.ps2model","586fd3d717007e407e0ffe8894b37e3ae78377c35cb4abe43617f54a96fd194e",373616},
 {"TATA-WINDOW1",3,"20262ea17be8ef15e0faea7b70dc1ae2cff47df9aec2410fe3538587a5d18660","TATA-CAR-FLEET-WINDOW1.ps2model","8a03e06623a849335e8568b5b613a352cebeb4b9c56a617e9a6320d69f0b0252",420814},
 {"KAMAZ-COMPLETE-WINDOW1",0,"df3d58336f6596cc4915b055820c5d0008b116b33091cca6915abdf971d3826c","KAMAZ-COMPLETE-FLEET-WINDOW1.ps2model","9351c7a6cb39cd9ce49695b94c5b3b6f7bb70646870d0e1615d86f26f4c005e5",827756},
 // only after in-game confirmation:
 // {"KAMAZ-CAR-WINDOW1",3,"1807d3e68bf080ad6c793ee548cad86d0846706bac8418b38495705196d401fa","KAMAZ-CAR-FLEET-WINDOW1.ps2model","763c3a892378faaf8685cd2b09d89e4f376338e81d4164835b2a4b7937adccf1",463996},
};
```

How loading should work (in the `FrontendModel` profile constructor, `renderer/frontend_model.cpp`,
for both role 3 race-car children and role 0 frontend fleet profiles):
1. Read `PS2ContentFixes` from `[PS2Port]`. It defaults to `0`. Add it to `PS2Port.ini.example` next
   to `FrontendModelMode` and `RacePS2FleetMode`.
2. With the key at `0`, or with no table row whose `role` and `originalSha` match the profile, load
   exactly as today.
3. With the key at `1` and a matching row, load `filename` from the same asset directory. Pass it
   through `decode_frontend_asset` with **that row's `size` and `sha`**, and with the profile's
   unchanged vertices, indices, textures and `ps2Meshes` counts. `decode_frontend_asset` should take
   an (expected size, sha) override rather than a copied profile, so that `profile->sha` keeps meaning
   "family identity" for all the keyed tables.
4. If the corrected file is missing or fails its pin, fall back to the original pinned asset and
   report `content_fix_unavailable` in diagnostics. Never accept bytes that are not pinned. Never
   change the original pins.
5. Probes and diagnostics that print `asset_sha256` should report the sha that was actually loaded,
   plus the fix id. Today they print `profile.sha`. Without this change, a corrected run would be
   logged as the original.

Registry and pin changes needed:
- New `kPS2ContentFixes` table (above), new INI key, and a size/sha override parameter for the decoder.
- **No edits** to the existing `kRaceFleetProfiles` (lines 671, 677, 684) or the frontend Kamaz line
  689, and no edits to the mixed, wrapU, tread, damage, brake or lamp registries. The originals stay
  the default and stay pinned.
- Ship the three (or four) new private assets next to the originals in the PS2Vehicles asset directory.
- Optional checks once adopted: a test that each fixed asset decodes with the original profile counts
  and that its rows match the original except where the evidence lists changes (NAVARA root.0–15
  ranges; none for the window fixes). Also a runtime A/B with `PS2ContentFixes` at 0 and 1.

## Not verified here

- No build, no renderer or test run, no in-game capture of any corrected asset.
- How the race path draws the left window and windscreen (the excluded conditional paths) is outside
  this package. Tata's left window was not inspected in game.
- Channel order (stored B,G,R,A, uploaded as `D3DFMT_A8R8G8B8`) is inferred. Colour statistics are
  reported as RGBA.
