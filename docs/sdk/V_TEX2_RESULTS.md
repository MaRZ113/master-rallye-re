# V-TEX2: integrated native texture and livery authoring

Implemented in the current `research/vehicles` worktree, on top of `f2f8e47`.
No game installation, ID allocation, registry edit, Extra Options dependency or
Course SDK change is involved. Existing uncommitted work was retained separately.

## Entry point and workflow

Run `tools/Launch-RallyWorkshop2.cmd`, select **TEXTURES**, then **Open Vehicle**.
The main legacy Workshop's Texture Studio also provides **Live 3D Texture Studio
(Qt)**, opening this same editor with the current vehicle preselected.
Choose a native family containing `complete.dx` and `car.dx`, or an existing
Workshop project directory. Opening a Workshop project snapshots its current
geometry/material state and retains its original texture baseline; it never
edits the source project. Geometry/Materials remains the established Qt editor.
The legacy Tk Workshop and its other editors remain supported.

1. Select a model/draw/stage/texture in the left tree. Inspect the owners before
   changing a shared atlas. The atlas, real UV0 islands and related 3D parts are shown.
2. **Export PNG / Image** exports PNG by default. Edit it in Photoshop/GIMP/Krita.
3. **Import PNG / Image** or **Reload from File** updates the existing GPU texture
   immediately. Import switches to Modified; camera, model and selection remain.
4. Use **Original**, **Undo**, **Redo** and **Restore Original** for comparison.
   Restore targets the selected resource, including all its shared owners.
5. **New from Stock** confirms unsaved changes (Save / Discard / Cancel); **Duplicate Current Livery** retains the current paint/artwork under a new stable UUID and parent link. New from Stock creates an independent stable UUID without a new Vehicle ID.
   Fill in name, number, crew, source and provenance. These are catalog metadata;
   paint the actual numbers/decals in the exported atlas.
6. **Save Livery** writes a fresh portable package. **Open Livery** verifies its
   hashes and reopens it offline, including Original comparison.

The private session journal also remains under the selected workspace's
`texture-sessions` directory. Every save uses a new package directory; previous
packages and originals stay immutable. Unsaved livery state is marked explicitly.

## Formats and texture safety

Import: PNG, JPEG, BMP, static WebP/GIF, TGA and TIFF through Pillow, normalized
to RGBA8 before the existing codec. Animated GIF/WebP uses frame 0 with a visible
warning. EXIF orientation is applied to image pixels. Dimensions must match the
selected native resource; UVs and other resources are never resized or remapped.

Export: PNG, JPEG, BMP and lossless WebP. JPEG/BMP composites alpha on white and
warns. Use PNG/WebP to retain alpha. RGB/Alpha/RGBA inspection is available.
**Preserve Original Alpha** defaults on; **Use Imported Alpha** is explicit.

PC `.dxt` remains a FEED/BGRA32 container, not DDS/BC compression. The existing
`WorkshopProject.replace_png` / `_apply` APIs retain the original header except
the established CRC32 word at 0x08. Legacy callers retain their previous alpha
behavior. Identical imported pixels produce no edit, including recompressed PNGs.
Only the exact selected resource is changed: no material, TEX0/1/2 binding,
glass, glow, brake-light, geometry, normal or physical configuration is authored.
Replacing a shared resource intentionally affects every listed owner.

**Export All** writes `textures.json` with relative PNG paths, source hashes,
dimensions, model family/variant and owner stages. **Import Manifest** validates
all entries before applying a single undoable batch; incompatible identity,
duplicate targets, paths escaping the package and wrong dimensions are rejected.

## Live preview and UVs

The existing native D3D9 previewer is an actual child HWND inside Qt. Controls are a persistent Qt label; embedded mode does not paint GDI text over Present. Technical warnings are hidden by default under Preview details and displayed as a readable list. It consumes
the established MRPV staging format and real DX geometry/UVs/materials, not a
generated vehicle proxy or PNG billboard. No game process or proxy DLL is needed.
LMB orbits/picks, MMB pans, wheel zooms. Reset and six presets are available.
Switch `complete.dx` / `car.dx` / `wheel.dx` independently of livery identity.

Texture upload uses bounded WM_COPYDATA messages and acknowledges one GPU update;
it does not reload geometry. Geometry picking synchronizes the texture inspection.
Wireframe, selected texture-owner highlighting, 2D UV opacity and all-owner UV
overlay are available. UV islands require a shared continuous edge and matching native vertex identity. Corner-only contact and overlapping UVs on independent geometry stay separate. Islands are selectable. Identical/shared
triangles and signed UV winding are reported; winding is only a mirror indicator.

UV export is a transparent image at atlas resolution. It uses the original UVs:
image x = u * width, y = (1 - v) * height, matching upright PNG export from native
bottom-up storage. There is no UV fitting, normalization, mirroring or atlas swap.
Repeating/out-of-atlas coordinates are reported and clipped by the image canvas.
Generated environment/secondary coordinates have no invented UV layout.

## CarSheet / SIDE HUD

Use the **CarSheet / SIDE** panel within TEXTURES. Presets are independent for
CarSheet (128x128) and SIDE HUD (32x16). Configure camera angle, scale/distance,
placement, key/ambient lighting, background and orthographic projection. Stock presentation v3 uses CarSheet azimuth 42 degrees, elevation 10 degrees, vertical FOV 24 degrees; SIDE uses azimuth -90 degrees, elevation 0, orthographic. The camera fits all visible vertices before rasterization. Frame scale and position act only on the final native image, with a one-pixel guard. The old zoom is never applied twice. Older built-in defaults migrate; custom presets retain their camera intent. Reset to stock presentation restores the common profile. Generate
explicitly after texture changes; stale generated artwork is rejected on save.
Model role and variant are recorded independently from the livery UUID.

Generation renders the same live scene geometry and textures, with diffuse studio light and the current live viewport environment reflections, into supersampled D3D9 targets
(512x320 or 512x256). Black/white passes recover composited alpha, without a color
key. The existing `ui_preview.compose_preview` v1 produces native role composition (stock p90 medians 166.109 / 202.787);
explicit owner scale/placement is then retained. High resolution sources stay in
the package. The live camera is restored even when capture fails.

Generated entries are **Reconstruction**, never historical originals. The panel explicitly distinguishes Active artwork from Generated candidate. Generating does not change the active image. Use reconstruction as active adopts the candidate and archives the previous active image, including historical source pixels; the archive survives save/reopen. Livery provenance independently supports Original / Historical / Custom / Reconstructed.
Manual import supports historical artwork: exact-size pixels retain placement and
tone; different sizes require explicit scaling approval and retain source pixels
separately. Original external images are never overwritten.

Export PNG at target size, or **Export native frame** with an existing qualified
same-size FEED template. This uses the existing codec and CRC policy. It creates a
new standalone DXT and provenance sidecar, without editing native banks. Packages
also include `ui-assets.json` using the existing `source-pixels-v1` contract. Bank
allocation/runtime application remains owned by the established SDK compiler.

## Architecture and manifest

- `workshop/livery.py`: identity, catalog, PNG/image roundtrip, atomic batch and package lifecycle.
- `workshop/texture_images.py`: optional Pillow import/export boundary.
- `workshop/qt_textures.py`: TEXTURES, UV inspection and embedded viewer ownership.
- `workshop/qt_artwork.py`, `livery_artwork.py`: live capture UI and SDK artwork composition.
- `qt_editor.py`: a second workspace tab in the existing editor, with routed shortcuts.
- `gui.py`: a main-Workshop entry into that same Qt TEXTURES workspace.
- `service.py`: backward-compatible optional alpha preservation; codec reused.
- `preview_scene.py`: one resource resolver per scene instead of rescanning per draw.
- `vehicle_previewer/src/main.cpp`: child mode, bounded texture/artwork IPC, offscreen
  render targets, resize correction and scoped embedded timer resolution.
- Launcher, focused tests and `tools/validate_vtex2_windows.py` provide entry and evidence.

`livery.json` schema `mr-livery/1` contains `metadata` (stable livery UUID, family,
physical ID, variant, name/number/crew/source/origin), pinned `baseline`, per-resource
`textures` with roles/stages and hashes, `artwork`, and separate `art_presets`.
All transferable file paths are relative. Model variant is read-only and tied to model_identity and pinned DX hashes; changing a PC display label cannot qualify a PS2 model. Source-platform ancestry is not inferred from the PC DX/FEED asset profile. Legacy unsupported labels are reclassified with a warning; contradictory new manifests are rejected. Artwork archives are portable too. Baseline DX files are unchanged copies;
texture stages and model variants are not interchangeable. MODEL and LIVERY are
separate catalog concepts; no runtime LIVERY menu is implemented here.

IPC: MRPV v1/v2; texture COPYDATA kind 0x32545856, five little-endian uint32 fields
(version, command, width, height, UTF-8 name size), name, optional stored BGRA.
Artwork kind 0x33415856 v2 carries four uint32 fields and eight finite floats, including vertical FOV; v1 remains accepted. The old zoom/pan fields are reserved in v2 capture: final framing is handled only by the compositor.
Native sender/receiver are Windows x64; packet layouts contain no process pointers.

## Validation and limits

96 focused tests cover codec use, alpha, orientation, metadata/CRC, protected paths,
manifests, undo, relocation, existing Workshop snapshots, optional formats, preview
cache and geometry/material authoring. Native GPU regression covers handedness,
vertical orientation, culling, transparent depth stress, reflections and brake lights.

The Windows acceptance tool opens the real Qt editor, clicks Open/Export/Import,
edits an exported DefRav4 ID31 atlas, verifies changed rendered pixels and exactly
one GPU upload, then compares Original/Modified/Undo/Redo/Restore/Reload and saves
and reopens Stock/Custom packages. Both artwork roles, native frame conversion,
manual preference and generic Forester ID30/TOMCAT ID32 paths are exercised.
The Custom example changes a sticker; it does not claim historical authenticity or
renumber every original number atlas. Its physical ID and geometry remain unchanged.

Measured locally: opening approximately 0.7-0.9 seconds, ordinary texture update
35-55 ms, artwork about 0.65-0.7 seconds per role, embedded viewport about 53-56 FPS.
Exact timings, source/build hashes, preserved dirty-file hashes and source file list
are in the private V-TEX2 delivery manifests. Earlier QTest polling held the GIL;
the validator now releases it while workers run. This was a test-driver delay.

Owner visual confirmation remains pending: orbit/pan on the owner's DPI/monitor,
lettering on mirrored/shared UVs, glass/glow appearance, image framing and external
editor saves. D3D9 retains its documented material approximation: runtime lighting,
sorting/inherited states and dynamic damage are not game-equivalent. TEX2 is not
emulated; unsupported/secondary stages show diagnostics rather than invented UVs.
The native embedded viewport is Windows-only and needs the optional Qt environment.
No game was launched or installation modified for V-TEX2.

Evidence composition images combine the Qt widget capture with the actual child
HWND backbuffer because Qt.grab excludes cross-process child windows. They are
labelled evidence compositions, not full-desktop screenshots or substitutes used
by the application. Separate native render captures and HWND-parent assertions
provide the direct viewport evidence.


## 2026-11-09 presentation corrections and Forester control

Compared all 32 retail CarSheet and 30 SIDE frames read-only from the existing
unpacked game corpus. Also used the pinned, accepted red DefForester ID30 artwork
from V-DEF4.1, not an assumed frame index in a newer extended bank. Its car.dx,
complete.dx and main atlas match the loaded SDK33 family. The older software
camera azimuth 138 converts to native RH azimuth 42; elevation is 10. Its implied
vertical FOV is 23.483 degrees, rounded to a common 24-degree authoring preset.
These are calibrated authoring parameters, not a recovered original game camera.
Camera comparison and reference hashes are retained in the curated validation
folder. Original accepted icons are read-only references and were not replaced.

The directory is curated to delivery, owner-workspace, the retained viewer binary
and a compact validation set. Disposable runs, repeated workspaces, captures and
compiler intermediates are removed after their current evidence is extracted.
User workspace data and any modified previous delivery are retained.

Authoring hash policy and retained ABI/baseline checks are documented in [SDK_HASH_POLICY.md](SDK_HASH_POLICY.md). External compatible package texture edits and retouched native artwork are accepted with current provenance, while edited historical pixels are classified as Custom.
