# Astra RCX pilot: progress and handoff

Status: **INCOMPLETE — NOT GAME READY**. No Master Rallye candidate, launcher or gameplay validation has been produced. Keep source game, donor and vehicle checkout read-only.

## Verified findings

* Source `Astra.rcx` SHA-256 `aea5e1478a943ce935fde3709aacfd83c03226679c7e0fd192f55774363ff2ed`; source `Rally.exe` SHA-256 `efc94948966ffe14b5dcfef6ea2b712db6f1e817b044dd0823c7425fa231a355`.
* Static x86 disassembly: archive open path calls decoder at VA `0x4829c0`, notably `0x45d437–0x45d471`. Decoder was implemented with bounds checks in `rcx_extract.py`. Archive index layout and counts are structurally checked, not declared universally valid.
* On the 56 supplied vehicle archives the implementation decoded 3032 file entries and exactly matched each declared decoded length with no bounds/termination failures. This is structural evidence; no byte-for-byte comparison to native runtime output has been performed.
* Astra has 90 extracted file entries; 62 QTO files passed checks for their v7.2 header, fixed vertex stream, index bounds, draw ranges and complete file accounting. Position, normal and UV offsets are candidate interpretations supported by numeric content and the diagnostic image; the auxiliary u16 array and many material fields remain unknown.
* MSH records: 62 fixed 136-byte records after the 8-byte header; candidate affine matrices for 16 selected parts reproduce their recorded bounding boxes within 0.02 source units. This is static evidence, not proof of animated transforms or native behavior.
* Exterior texture header is consistent with 512x512 BGRA and mip chain; top mip produced the saved atlas. DXT3 top mip was decoded through Pillow for the wheel image. Native color/alpha and texture orientation behavior are not yet qualified.
* 5 local tests pass: decoder literals/backreferences, rejected malformed streams, real Astra metadata and body structure, truncated QTO. Test output does not establish gameplay.

## Diagnostic outputs

`astra_static_diagnostic.obj` / `.mtl`, texture PNGs and `astra_static_diagnostic.png` are a Blender approximation built from 16 source parts. The image is missing correct materials, cabin, animated effects and source lighting. **The visible livery text is mirrored** and texture/UV coordinate conventions require investigation. It is not an original-render capture or a vehicle package. `astra_static_diagnostic.json` records the selection and matrix/bounds checks.

`astra_extracted/manifest.json` records the extracted bytes and hashes. `qto_inspect.py` produces source-coordinate diagnostic OBJ for an individual QTO. `astra_preview.py` assembles selected geometry and `render_diagnostic.py` renders it; both assume the local extracted Astra is present. `rcx_extract.py` refuses an existing output and restricts output to a fresh subdirectory next to itself. The prior broad ASCII inventory is superseded for Astra by the actual decoded index.

## Work remaining to meet the request

1. Trace native texture and mesh loading, qualify channel/order, UV orientation and handedness; correct mirrored text and rerender after each change. Check original source game only through an isolated writable copy under this folder, if needed.
2. Validate source scene and four wheel instances, texture-to-draw associations, material states, bounds, source normals and non-identical wheel variants. Document visible approximations and unsupported states.
3. Adapt to `universal-vehicle-scene/1` and the existing Master Rallye scene compiler, select a compatible donor and fit its collision/physics, construct complete/car/wheel assets, textures and a separate SDK roster/staging tree entirely here. Any donor physics or damage approximations must be explicit.
4. Run actual project validator, compiler, roster and isolated launch preflight. Package a self-contained test candidate only after successful checks. A human in-game test is still needed to establish runtime behavior.

The archive contains source code, report and diagnostic metadata, not proprietary extracted model/texture payloads. Existing source trees were read only.
