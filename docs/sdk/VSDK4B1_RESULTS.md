# V-SDK4B.1 — qualified Classic conversion pilot

26 October 2026; `research/vehicles`. This phase adds a reproducible conversion,
not another empty appearance snapshot. The owner approved the final Previewer
appearance and its exact report before the Classic game-candidate build.
**Actual D3D8 gameplay acceptance remains pending.**

## Read-only references

`tools/measure_classic_references.py` measures seven ordinary retail families per
class (IDs 0–20), plus frozen Subaru V-MESH4.13. Special registry variants are
not counted as extra independent models. These are observed ranges, not limits:

| Class | Race triangles | Frontend triangles | Wheel triangles | Race draws | Referenced textures | Native cache bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T1 | 2022–2323 | 2470–2725 | 252 | 32–39 | 29–50 | 374784–565248 |
| T2 | 1838–2366 | 2165–2761 | 252 | 27–37 | 26–39 | 360448–553984 |
| T3 | 1872–2165 | 2248–2571 | 252 | 21–33 | 25–35 | 351232–456704 |

Frozen Subaru: race 3301 triangles /37 draws, frontend 6693 /26, wheel 1008 /4;
39 referenced textures /404736 cache bytes. Its successful principles are more
useful than treating its polygon count as a universal target: separate opaque
face/shelf UVs, no tyre bleed, an explicit stock-derived recess, restrained local
material decisions and separately qualified source-specific corrections.

Stock Pajero wheel face/shelf have 18/72 triangles and three measured relative
radii 1.0 /0.89286 /0.80992. Stock Navara, Pajero and Megane opaque painted draws
demonstrate existing environment passes and independent diffuse/reflection alpha
roles. Stock measurements and reference GPU views remain private local evidence;
no reference artwork is bundled.

## Lancer mapping and actual conversion

Input is the immutable, qualified V-LANCER6 compiled import, not a prior Classic
output. `research/vehicles/vsdk4b1/lancer-classic-profile.json` pins its three model
hashes and the paint/reference inputs. No numeric GT4 `MatN` classifier is used.

- **Body geometry:** approved foglamp protective dust covers: race draws 15/16,
  frontend 17/18, each 48→16 triangles. Exact outer contour, original centre,
  their UVs, normals and colours survive. Dropping the intermediate convex ring
  is an explicit MR approximation (source relief about 19/18 mm); the actual
  headlights and native light controls are untouched. Quantized contour/UV
  tolerances are recorded. There is no automatic global decimator.
- **Livery:** the hash-pinned body atlas is split by native opaque versus cutout
  ownership. Qualified fields are regenerated, including explicit UV-space
  polygons for the characteristic red/charcoal diagonal and red belt/pillar.
  Ordinary exterior sponsor overlays are omitted: race 65–71 and77; frontend
  67–73 and81. These include the dense Michelin/Ohlins/PIAA/RalliArt fender/bumper
  atlas, small side sponsorship and Pringle/Eurotex/plate overlays. Number1,
  Mitsubishi badges, window markings and roof rally plaque remain. Other small
  or ambiguous content is deliberately retained; this is not automatic logo
  recognition. The omitted source art remains in Source Fidelity.
- **Wheels:** the unchanged Subaru shelf implementation now lives in SDK Core;
  its old tools module is a compatibility shim. The optional Classic construction
  uses an opaque 18-segment recessed textured insert, guarded metal lip/shelf UVs,
  dark inner barrel and a two-sided opaque inner cap. Original tyre attributes
  and radius are exact. Rim triangles 537→162; no hub translation. Four frontend
  instances are accepted only after every original template part matches its
  supplied transform, UVs, normals, colours and indices. Existing fixed rim draw
  slots remain (16 total wheel draws); they are not claimed to match stock draw
  counts. This is a documented fixed-grammar boundary, not fake transparency.
- **Materials:** only the explicit opaque paint owners use the local stock
  `whitepaint` environment. Existing qualified shader families are retained;
  rubber, glass, lamp, cockpit and unknown families are unchanged. No global
  alpha override or modern shader is introduced. Native Binding v2 validates
  every changed reference. Cutout alpha is byte-exact; its original environment
  and vertex alpha remain unchanged.
- **Brightness correction:** the rejected draft regenerated white fields at
  RGB232 and substituted a brighter environment. Original neutral pixels in
  x10–279/y170–229 have median RGB168. The source paint environment has median
  RGB2/3/4 versus stock whitepaint46/50/50. Final base RGB168 plus an explicit
  opaque reflection-strength factor0.06 prevents the observed whitening. This
  is a measured pilot energy adaptation, not physical/angular renderer parity.
- **Textures:** opaque paint becomes 512×128, cutout remains 1024×256 to protect
  coverage. Retained decal textures are not resized. Four unused sponsor atlases and the replaced source paint
  atlas leave the converted closure; separate generated paint and a
  stock environment enter it. No incompatible glass/damage/lamp atlases merge.

## Measured difference

| Resource | Source triangles / draws | Classic triangles / draws |
| --- | ---: | ---: |
| Import car.dx before unchanged mechanical extraction | 2649 /119 | 2379 /111 |
| Actual packaged race car.dx | 2625 /107 | 2355 /99 |
| complete.dx | 6333 /186 | 4563 /178 |
| wheel.dx | 745 /16 | 370 /16 |

The same 24 mechanical triangles are extracted into four independently attached
resources in both variants. Those four resources are byte-identical.
Referenced texture count: **77→75**. FEED disk bytes: **12201476→12021212**;
native RGBA cache estimate: **12199936→12019712** (about 1.48% smaller).
This modest reduction is deliberate: mixed glass/cutout and retained lettering
are protected rather than indiscriminately reduced. FEED contains stored BGRA;
the estimate is original width×height×4, not a DXT1 compression ratio or FPS claim.

## Shared Core, Studio and CLI

`classic_style`, `classic_geometry`, `classic_wheels` and `wheel_layers` perform
the conversion; `workshop.classic` owns versioning, reports, manual-layer conflicts
and the explicit approval gate. Studio and CLI call this same stage.

1. Paint / Style → **Rebuild as Classic…** → choose exact-hash recipe, local
   read-only `DataGx/Vehicles` and a fresh output directory.
2. Inspect the generated Classic preview, matched Source Fidelity comparison and
   report. Nothing is installed. Builds are blocked until **Review / approve
   Classic report…** accepts that exact report SHA256.
3. The style selector navigates independent Source Fidelity /Classic projects.
   Custom edits are local versioned layers. Before-current-edits view means the
   current version baseline; matched comparison uses the original source import.
4. Rebuilding a Classic follows its immutable source link, never decimating the
   previous Classic. Compatible active texture/surface layers reapply only with
   exact ownership proof. Changed baselines/selectors become explicit conflicts;
   all original snapshots and recipes remain in `source-manual-layers.json` and
   the untouched parent. Crew selectors need requalification after topology
   changes; existing crew geometry itself is preserved.

Initialization, before a first candidate:

```powershell
python tools/classic_vehicle.py init --project C:\Private\LancerAuthor --style "Classic MR Style" --recipe research/vehicles/vsdk4b1/lancer-classic-profile.json --stock-root C:\Private\Retail\DataGx\Vehicles --output C:\Private\ClassicVersion
```

Existing Workshop project: replace `init` with `rebuild`. Source-only initialization
supports `--style "Source Fidelity"`. To approve an inspected report:

```powershell
python tools/classic_vehicle.py approve --project C:\Private\ClassicVersion\classic --report-sha256 EXACT_REVIEWED_SHA256
```

Then use ordinary Workshop Validate /Build. Keep output names short on Windows:
the first long path hit MSVC FileTracker FTK1011; the same builder passed with
`sf` /`cl`. No launcher integrity check or compiler test was bypassed.

Install the existing Workshop extra with `pip install -e ".[workshop]"`: Pillow
handles texture generation and NumPy performs bounded cover plane/UV qualification.
NumPy is imported only by that conversion helper, not by the standalone native
Previewer or ordinary DX parsing/rendering. Both are available in the validated
Windows environment.

For another car, provide its user-owned qualified import and an independently
qualified recipe. This pilot intentionally rejects a different model hash;
universal automatic semantic classification and a visual recipe editor are
deferred. The original import/converter remains the source of truth.

## Evidence and preservation

Private evidence root: `.research-output/vehicles/vsdk4b1/`.

- `qualification-final/validation.json`: deterministic output and report, all
  unaffected geometry/material groups, tyre attributes, collision, native light
  cases, exact cutout alpha and real Windows fixed-camera views. Native damage
  CPU replay: zero split position groups, zero protected alpha losses with the
  adapter (41 without it); original deformation/RGB and ABI preserved. This is
  original-instruction offline evidence, not a race.
- `manual-rebuild-validation.json`, `strict-rebuild-validation.json`: compatible manual edit replay, explicit changed-atlas/cover conflicts, reopen and rebuilding from Classic preserve exact output; existing strict shadow guard reused.
- `windows-classic-final2/`: real Rebuild button, workers, two versions, report
  dialog/build rejection, matched GPU comparison, dropdown restoration/reopen.
- `w/`, `paint-win/`, `reference-gui02/`, `zoom-windows/`, `references/`: actual
  stock/addon editing/build/zero-edit, Paint/Crew/history, stock browser/impact,
  seven-scale texture display and native controls/reference captures.
- `preservation.json`, `roster-sf-validation.json`, `roster-cl-validation.json`:
  sealed qualified 30-entry composition, existing UI records and frozen base,
  identical stock/other-addon resources. Only 12 paths inside Lancer's resource
  family differ between the two variants. Physics/audio files, addon identity
  plan, UI XML and retained resource hashes match; shadow parameters are unchanged,
  with only its model pin renewed. No runtime capacity or physics patch added.
- Lancer has its original glass surfaces/materials and native blight switch;
  this phase does not invent new Lancer broken-glass controllers. Existing Subaru
  glass and accepted Pajero source/candidates stay untouched and regressions cover
  those established paths. No claim of a newly merged Subaru-glass roster is made.
- Original MRallye.exe/DLL remain respectively
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` /
  `eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4`.

## Owner test and boundaries

Final approved author version: `version-04/classic`, report
`95d662ca5ca566f5a0c31a9572b8f390ce7e7562beb36e1b398a39fc99201b55`.

1. Launch **sf/candidate/Launch-SDK-Roster.cmd** for Source Fidelity and
   **cl/candidate/Launch-SDK-Roster.cmd** for the approved Classic, one at a time.
   Both use Lancer CarID28, frozen Subaru27 and accepted Pajero29 composition;
   they are alternate candidates, not two Lancers in one roster.
2. Compare menu framing and every body side. Check red/charcoal livery and white
   paint brightness, reflections enabled/disabled, lamp covers and wheel inside/
   outside views. UI assets are intentionally identical between variants.
3. In a race inspect tyre/arch/hub fitment, crew, glass/decal visibility, rear
   brake illumination/halo and damage. Verify no material ownership changes after
   a collision. Handling, cameras and four audio layers should remain as before.
4. Re-enter races, include stock/Subaru/Pajero AI, finish and view Results. Confirm
   menu loading remains acceptable; no new live PERF2 timing claim is made.
5. In Studio switch to Source Fidelity, reopen both versions, edit a qualified
   Classic surface, Undo/Redo/Restore and rebuild into a fresh directory.

Previewer is a D3D9 fixed-function diagnostic with the previously documented
lighting/queue/environment approximations. No screenshot alone proves D3D8
material parity. No Blender Bridge, Audio Studio, broader vehicle generalization,
stock editing refactor, runtime deletion, remote push or publication occurs here.
