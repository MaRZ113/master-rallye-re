# V-LANCER2 — partial GT4 source qualification

Branch `research/vehicles`. Private result directory:
`.research-output/vehicles/vlancer2/`. **Partial source candidate and three
component DX/DXT probes, not a complete assembled car or runtime candidate.**
No capacity changes, CarID assignment, physics tuning or installation occurred.

## Evidence and extractor defect

Original GT4 Beta `mits0015` inputs retain the hashes recorded in V-LANCER1.
The local PDTools sources inspected are under
`D:/Game/GT_Model-Tools/GTPS2ModelTool-master - Copy/PDTools/PDTools.Files/Models/PS2/`:

- `ModelSet/ModelSet2.cs`, `ModelSet2Model.cs`, `ModelSetPS2Base.cs`;
- `PGLUshape.cs`, `VIFDescriptor.cs`, `VIFPacket.cs`, `VIFCommand.cs`, `GIFTag.cs`;
- `RenderCommands/ModelSetupOpcode.cs`, `Cmd_pgluTexTableFromExternalTexSetByte.cs`;
- `RenderCommandContext.cs`, plus the companion tool's `Dumper.cs`.

The header offsets, shape tables, descriptor material/texture indices and
packet layouts in the adapter were checked against the original bytes.
This is asset-format/source-reader evidence, not analysis of the original
GT4 executable or proof of native PS2 rendering semantics.

The source decoder's opcode **80 / 0x50** selects an external texture set.
Its `Read` incorrectly calls `WriteByte(ExternalTexSetIndex)`; its `Write`
incorrectly calls `Read1Byte`. Therefore consuming operand `02` can write `00`
back to an input opened writable. The V-LANCER1 private input copies exhibit
exactly that mutation at body offset 5897 and twelve wheel command offsets.
Those bytes are texture-binding command operands, not geometry repair flags.
Original corpus files were never passed to this executable for modification.
The new adapter reads immutable byte buffers and does not invoke it.

The stock export also processes only a subset of model commands and texture
bindings. Fixing the swapped reader methods alone would not prove a complete
GT4 exporter. Current generated command YAML is used as an explicit snapshot,
not represented as a complete original command interpreter.

## Direct geometry recovery

`addon_sdk/gt4_source.py` now bounds-checks CAR4→MDLS, shape/texture tables,
VIF packets, and packet-local strips. Every decoded shape's triangle count
must agree with the original shape header. Position/UV arrays are kept per
packet, preventing mixed attribute arrays from creating cross-shape UV links.

| Input | Shapes decoded | Triangles recovered | Qualification |
| --- | ---: | ---: | --- |
| Menu body | 30 / 30 | 5350 | Includes stored effects, shadows and uninvoked shapes; not 5350 visible body triangles |
| Race body, all stored LODs | 89 / 93 | 6538 | Four packed-byte cases remain unsupported; not one combined LOD |
| Menu wheel | 2 / 2 | 1074 | Local geometry valid; source draw/effect layers remain distinct |
| Race wheel | 9 / 10 | 196 | Original file contains geometry despite empty legacy OBJ export |

Untranslated VIF attributes and failed shapes remain in the intermediate;
they are not silently replaced. Float source normals and UVs are preserved.
Absent normals remain absent; byte-encoded attributes are retained without
inventing an unverified normal/position scaling. No synthetic UV is inserted
into source geometry. The previous aggregate OBJ forward-index issue is
avoided by reading the original packets rather than trusting aggregate OBJ.

The intermediate retains non-textured surfaces and shadow/effect shapes.
Preview eligibility is separately gated by command state and active model:
`model0` for menu, `model0.lod0` for race. LODs are not superimposed.

## Command-driven material translation

There is **no MatN-prefix classification**. The adapter consumes explicit
per-shape command snapshots, source flags, packet bindings and GS registers.

| Source feature | Result |
| --- | --- |
| AlphaFunction(GREATER, ref) | Explicit test/ref retained; preview ref converted from PS2 alpha range |
| Normal `(Cs-Cd)*As+Cd` blend | Source-alpha/alpha-test route; blending remains explicit |
| Depth write disabled or destination-alpha test | Unsupported special pass, not flattened into paint |
| RGB channels masked, alpha writable | Separate alpha-only effect record |
| Destination-alpha blend `(Cs-0)*Ad+Cd` | Unsupported blend/effect record |
| Shadow flag, external environment texture | Separate unsupported shadow/environment route |
| Unknown command or alpha function | Explicit unsupported record |
| TEX0 TCC/TFX and CLAMP S/T | Registers retained; repeat/clamp preview supported for admitted full-raster regions |

Region-repeat, nonzero region origins and non-modulate texture functions are
not silently approximated. RGB-only TCC does not turn texture control alpha
into surface transparency in the preview. Tail on/off invocation names remain
separate in source records; runtime brake control is not implemented here.

Decal/mask layers are retained rather than dismissed because they contain
transparent pixels. Destination-alpha decal composition is **not yet faithfully
reproduced**. The partial RGB previews consequently lack some decals/glass/effect
details; they are not proof of missing source geometry or visual parity.

Defaults are explicitly derived from the inspected PDTools command context.
Unexported state, VM-controlled commands and complete command execution remain
a qualification boundary; this adapter is conservative and partial.

## Shared conversion connection and offline artifacts

`tools/qualify_gt4_source.py` produces:

- `final-menu/source-intermediate.json`: decoded geometry, source normals/UVs,
  raw attributes, pass decisions, texture registers and unresolved anchors;
- `final-race/`, `final-wheel-recovery/`, `final-menu-wheel/`: equivalent
  qualification results without guessing model instances;
- `final-menu/probe-0..2/component.dx` and matching `colour-tga.dxt`:
  three packet-local probes using existing **rebuild_topology**, **r4e_writer**,
  DX parser and DXT parser. UV and Z conventions are explicit; original texture
  dimensions/RGBA are retained for these source samples. Other donor draws are
  fillers and donor collision is retained for format validity only;
- front, rear, side and three-quarter previews of admitted source RGB passes.

These probes establish the shared native-file-writing path, not a complete
`car.dx` / `complete.dx` family. The MR alpha-test threshold is not asserted
identical to the GT4 GS threshold. Re-atlasing, exact MR material equivalence,
complete decal composition and assembled wheels have not been qualified.
Existing Subaru builders and repair masks are not imported or copied.

## Wheel anchors and safe menu-wheel use

Original menu-wheel geometry can be used as a **local-space source component**:
its two shapes decode and match their declared counts. Source geometry already
has depth; automatic rim reshaping is not applied without a fit qualification.

ModelSet2 model origins are read from the documented model records. All four
menu-wheel model origins equal approximately `(0.04495, 0, 0)`; race-wheel
origins equal `(0.08239, 0, 0)`. These are not four car wheel anchors. CAR4's
remaining metadata / instance and VM transform bindings are not fully decoded.
No anchors are inferred from body arches, specDB wheelbase or donor placement.
Therefore shared wheel embedding/layering is gated, not forced through.

## Validation and remaining blockers

- 205 tests run: **204 passed, one old private fixture unavailable**.
- Three native DX probes structurally validated; DXT dimensions and CRC32 pass.
- All 190 immutable Subaru V4.13 resources match their frozen manifest.
- Original MR executable and graphics DLL retain exact prior hashes.
- All four GT4 corpus inputs retain their V-LANCER1 hashes. No runtime launch,
  fresh Subaru rebuild, slot expansion, publication or push is claimed.

Remaining blockers: complete original command/VM interpreter and external
texture bindings; four race-body / one race-wheel packed attribute cases;
full masks/decal/destination-alpha composition; original wheel-instance
transforms; complete MR material/atlas equivalence. This stage stops with the
partial offline candidate and evidence. Runtime capacity stays out of scope.

The private intermediate, textures and images must not be redistributed.
The review archive contains own source, tests, documentation and compact
non-geometry evidence only.
