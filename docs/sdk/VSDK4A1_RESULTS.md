# V-SDK4A.1 — display resampling and application identity

25 October 2026. V-SDK4A was revalidated (799 tests, one skipped) and committed as
`f4df4f4`; the actual combined V-SDK3.1/V-SDK4A state was preserved, without
inventing unavailable intermediate historical snapshots.

## Display fix

The old Tk integer `-zoom/-subsample` combination did not provide a proper
fractional filter. Texture Studio now uses Pillow on the **display viewport only**:
LANCZOS reduction, bicubic fractional enlargement and premultiplied `RGBa`
filtering before returning to RGBA. Invisible RGB cannot contaminate alpha edges.
Exact 1:1 uses the original upright display texels directly. Optional Pixel-sharp
uses nearest sampling. Canvas wheel zoom preserves the cursor's image coordinate;
scroll/drag pan and fit/actual controls remain available.

Output is bounded to 4M pixels per view, source inspection to 16M pixels. No
whole-image enlargement or persistent display duplicates are produced. Original/
current, RGB/RGBA/Alpha, checkerboard, embedded/detached windows are retained.
Native FEED rows, dimensions, alpha, PNG conversion and replacement/build recipes
are unchanged. Pillow is an explicit `workshop` optional dependency; install it
with `pip install -e ".[workshop]"` on a new authoring machine.

## Original artwork

`assets/workshop/rally-workshop.svg` is original geometric rally-prototype
silhouette artwork, graphite/amber with wheel cutouts, cabin and roof highlight.
It uses no extracted models, screenshots, sponsor logos or proprietary textures.
The icon artwork is dedicated under CC0; see its adjacent license. The generator
records every shape. Multi-resolution ICO contains16/24/32/48/64/128/256 sizes.

The icon applies to the Tk root and child windows and the compiled native
Previewer resource. Tk receives the explicit Windows AppUserModelID
`MasterRallye.VehicleSDK.RallyWorkshop`. If an existing Previewer holds its binary
open, Build retains that process and writes a versioned new executable. The
launcher/default GUI reads the new path from `application-build.json`.

## Evidence

Private root `.research-output/vehicles/vsdk4a1/`:

- `tests-final.txt`: **805 tests, one skipped**, full qualified Windows checkout.
- `zoom-windows/validation.json`: real64²/128²/1024×256 project textures and a
  clearly identified original generated2048² gradient/alpha/lettering/atlas fixture;
  25/50/75/100/125/200/400 percent, two actual Tk windows and56 screenshots.
- Same test exercises RGB/RGBA/Alpha, Original/current, Pixel-sharp, pan and
  cursor anchoring. Original BGRA and encoded PNG bytes remain identical.
- `ui-controls-final.json`: real four-vehicle GUI controls, inspection, variants,
  detached channels and pan. No claim of MR gameplay qualification.
- `build.txt`: rebuilt Windows Previewer with original icon; no original game
  executable, retail resource or graphics proxy is modified.

Reproduce: `python tools/validate_texture_viewer.py --library <private-library.json>
--output <fresh-evidence-folder>`. Run `Rally-Workshop.cmd` normally afterwards.
Source-only archives include the original icon artwork but no private test images.

Owner must inspect smooth zoom on their display, small/taskbar icon readability
and normal editing/build workflows. V-SDK4C follows by the owner's explicit
ordering; Paint Studio remains deferred.
