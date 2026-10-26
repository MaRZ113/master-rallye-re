# Paint and Classic MR Style

## Qualified Classic conversion (V-SDK4B.1)

Rebuild as Classic creates independent Source Fidelity and Classic projects from
the immutable qualified source import. Select an exact-hash recipe, your local
read-only stock DataGx/Vehicles folder and a fresh output folder. The current
pilot supports the qualified GT4 Lancer Evo IV only; a different model hash is
rejected, not silently approximated.

Inspect the regenerated livery, approved cover reduction, opaque recessed wheel
and material report in the Previewer. Review / approve Classic report requires
explicit confirmation before that exact report can become a build input. No
game files are installed by generation or approval. A changed report blocks builds.

The style dropdown navigates separate source/Classic projects. Rebuild always
follows the original import link; it never simplifies an already simplified
output. Compatible active manual edits can reapply with exact ownership proof.
Conflicts preserve their recipes and all inactive snapshots in
source-manual-layers.json and the unchanged parent; they are not guessed away.
Existing crew geometry remains, while old vertex-based crew selectors may need
requalification. New edits use normal Save, Undo, Redo, Restore and Build.

Before current edits shows this version's immutable baseline. Matched Original /
Modified /Difference compares the original source import with the current Classic
result. Texture Studio Original similarly means before manual edits to this
version; open Source Fidelity to inspect its original source atlas.

Older manually authored appearance snapshots remain compatible, but switching
their label is not a Classic conversion. The inspector states that distinction.
Use Rebuild as Classic to generate a qualified version. Source Fidelity remains
available, and no universal material/logo classifier is claimed.

CLI initialization before the first candidate uses tools/classic_vehicle.py init
with --style "Source Fidelity" or --style "Classic MR Style". Existing projects
use rebuild; approve requires the inspected report SHA256. See the phase results
for the complete command and owner gameplay checklist.

## Qualified paint

Select the source texture in Texture Studio. Export/inspect its PNG orientation,
then import an exact-size opaque greyscale mask: white means paint, black protects
content, grey is fractional coverage. Enter the qualification evidence. No logo
recognition or semantic segmentation is implied. Check all entries in the texture
usage list, including race/frontend differences. Masks and source hashes are pinned.

Choose a region, type RGB bytes or a named colour, then Paint qualified region.
The algorithm preserves source luminance/detail and alpha; a dark blue source
will produce a darker result than a white one. It is not a physically based paint
shader. Multiple explicit regions on one texture form a reproducible ordered
stack; overlapping masks compound their luminance. Protect edges with generous
black margins. Existing PNG replacement/multiplication must be restored first.

Native selected-surface RGB remains available in Inspect. It is appropriate only
when the entire draw is qualified paint: it also modulates baked lettering.
Do not use it as selective paint on a mixed livery atlas.

## Local stock references

Browse a stock vehicle family from your own unpacked MR installation. The browser
shows exact model hashes, draw IDs, slots, dimensions, alpha ranges and native
semantics. Select a target draw in the main inspector. Applying a reference copies
pixels into its private existing owned image; an impact dialog lists EVERY affected
slot. Shared image ownership is retained. This is not a per-draw private texture
clone. Use an already independent image or decline when another owner must remain
unchanged. Texture Binding v2 checks every affected native slot before committing.

Diffuse transfers require matching dimensions and compatible alpha classes.
Opaque environment maps may explicitly opt into premultiplied LANCZOS resizing
to the existing target size. UVs, reflection enablement and native draw states
stay unchanged; no arbitrary diffuse UV adaptation is offered. Reflection weights
are edited separately through qualified Inspect controls. Unknown fields remain
read-only. No stock assets are bundled or installed over the originals.

Matched Original / Modified renders use the same fixed capture camera and wheel
assembly. The difference view amplifies pixel differences threefold. This is a
D3D9 diagnostic, not gameplay or an exact renderer parity claim. Interactive
camera controls and bookmarks remain in the native Previewer.
