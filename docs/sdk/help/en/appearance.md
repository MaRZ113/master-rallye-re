# Paint and Classic MR Style

Source Fidelity, Classic MR Style and Custom are independent editable snapshots
of texture and surface recipes. Switching saves the outgoing snapshot. Original
resources always remain immutable; Restore all resets the active edits and crew
corrections, while Undo recovers the previous state. Named snapshots remain local
to the project. Classic starts from source: it does not guess shader semantics.

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
