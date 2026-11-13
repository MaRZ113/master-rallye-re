# RCX Astra: gates A–D, 31 October 2026

Status: **SDK STRUCTURAL BUILD PASS; GAMEPLAY NOT TESTED; NOT RUNTIME INSTALLABLE**. This is a private diagnostic SDK build, not a qualified playable roster. All created files are under `exclusive_research`; external source, retail corpus and SDK checkout are read-only.

## Gate A — parser and texture orientation: PARTIAL

`rcx_extract.py` bounds archive reads, decoded size, payload ranges and names. `qto_inspect.py` retains each complete 57-byte raw draw record, exposes raw material flags and the candidate texture-table index (second u32), validates index and disjoint draw coverage, and rejects bad or non-finite geometry. `tex_decode.py` independently handles observed TEX v1 A8R8G8B8, X8R8G8B8, DXT1, DXT3 and all declared mip levels, rejecting malformed sizes/unknown formats. These semantics are bounded to inspected assets; raw flags are not labelled as known rendering behavior.

`python -B test_rcx.py` runs 7 portable synthetic tests and skips one optional real-corpus test; setting `RCX_ASTRA_PATH` enables it. Eight pass with that variable set. All 62 Astra QTO and 22 TEX members pass current structural checks. The current stricter archive parser and decoder were checked against all 56 archives / 3032 entries without errors; this is structural validation, not native-runtime byte comparison.

The prior mirrored-text image came from reflecting one axis, making the geometry transformation negative-determinant. Current static transform `(-X,-Y,+Z)` has determinant +1. Correctly placed body atlas regions, readable labels and front/rear lights can be inspected from four directions in `astra_four_views.png`. UV export uses `(u,1-v)` for OBJ; source scene retains original UV. This establishes an internally consistent offline orientation, **not source-engine rendering parity**. No source runtime capture or loader/texture address-mode verification has yet proved native texture orientation/material behavior. The four rendered file names indicate camera location, not recovered source left/right identity.

## Gate B — minimum scene: PARTIAL

`astra_scene_v2/scene.json` is a canonical `universal-vehicle-scene/1` with 16 selected nodes (body, bonnet, bumpers, lamps, mirrors, wing, windows and four separately instanced wheels), 20 draw meshes and 2638 serialized triangles. Per-group texture association, raw material flags and source UVs are retained. No cabin, animation or damage was added. The OBJ/Blender render is approximate; it uses two opaque diffuse materials and does not reproduce RCX alpha, reflection, animation or lighting. Inspectable candidate physical axes and units are an inference, not game-traced facts.

Measured source MSH wheel translations after the offline basis: front Z -1.30365, rear Z +1.29036; front hub separation 1.38803, rear 1.53751, wheelbase 2.59401 source units. Metres are plausible but unverified. Across all selected draw triangles, face cross-product versus supplied normal sums was positive for 2626, negative for 12, near-zero for 0; this statistic does not by itself establish native winding or that the 12 faces are wrong. Each selected MSH matrix reproduced its recorded mesh bounds within 0.02 source units. The `astra_four_views.png` SHA-256 is `d775a4cd4ccce5c3215ba90dec6e64aa92ff6ad994940f7d605faad228ee5fb4`.

## Gate C — existing SDK contract: STRUCTURAL PASS

`rcx_scene_adapter.py` uses the actual SDK at HEAD `bfd13741da01dfe71755add6b8c56f7a0a8c2d7f` and `universal_vehicle_scene.save_scene`, preserving distinct draw materials, UV arrays, source matrices, raw flags and four wheel anchors. SDK validation/reopen succeeded. Two independent outputs have identical canonical scene SHA-256 `3eafadb91b62fee14e811ea63448e718b6dbda2fc6b3416e12aac32d7d884d45`. `rcx_sdk_candidate.py` calls the existing `universal_scene_bridge.compile_scene` and `scene_dx_writer`; there is no second DX compiler. This passes a structural contract, not source-shader parity.

## Gate D — first retail SDK output: PARTIAL

`astra_author_diagnostic_v4/sdk_build` was built with Newrav donor and exact stock retail SMA SHA-256 `03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f`. Existing SDK `validate_project` and `build_project` both report PASS, 15 manifest artifacts / 11 resources, `runtime_installable: false`; all 15 recorded artifact hashes were independently rechecked. `car.dx`, `complete.dx` and `wheel.dx` pass native structural parsing; donor collision bytes are preserved. Donor physics family is copied without tuning. This is a validated **authoring build**, not the requested fully qualified compatible retail candidate.

Newrav was selected after comparing available original hull envelopes: its X approximately [-0.93,0.93], Y [0,1.37], Z [-2.11,1.94], closer to Astra than the initially tried Megane hull. Newrav XML states wheelbase 2.45 and tracks 1.60, while Astra anchors measure 2.594, 1.388 front and 1.538 rear. These values may reflect different origins/semantics; the differences mean compatible physical wheel placement has NOT been demonstrated. Donor hull Y reaches 1.37 while Astra body vertices extend approximately to 1.46 after the proposed basis. Collision fit and game behavior require further qualification. The source contains four different wheel instances while the ordinary built `wheel.dx` uses one canonical wheel: the compiler reports `runtime_single_wheel_safe: false`. The generic SDK's structural PASS does not waive these gates.

Materials in this build explicitly flatten alpha to opaque, and the SDK preview uses approximated diffuse light. Texture and geometry visual checks in the original RCX runtime and a separate D3D8/runtime qualification are outstanding. No game was launched, no installed files were changed, and there is no runtime PASS.

## Files and reproducibility

* `test_rcx.py`, `rcx_extract.py`, `qto_inspect.py`, `tex_decode.py`, `rcx_scene_adapter.py`: research tools.
* `astra_scene_v2/scene.json` and `manifest.json`: original source scene plus hashed RGBA sidecars; `astra_scene_repro2` independently reproduces the same hashes.
* `astra_sdk_diagnostic_v3`: bridge report, three compiled DX files and DXT textures before SDK project build.
* `astra_author_diagnostic_v4/validation.json`, `build-report.json`, `sdk_build/build-manifest.json`: actual SDK validation/build evidence.
* `astra_four_views.png`: current diagnostic, not native/gameplay evidence.

Old `astra_scene_v1`, Megane builds and older renders are superseded diagnostics. No older report or hash qualifies the current output. Archive `astra-gates-stage-20261031.zip` contains changed code, tests and this report, without extracted proprietary model/texture payloads.
