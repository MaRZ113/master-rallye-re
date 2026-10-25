# V-MESH4.11 — Subaru CarSheet and UI integration

2026-10-23. Checkout `master-rallye-re-vehicles`, branch `research/vehicles`.
Baseline: V4.10 `v410-exp-002`. Updated private candidate: **`v411-exp-005`**.

## Findings and implementation

| Consumer | Original mapping | Subaru mapping | Asset |
|---|---|---|---|
| Vehicle Select | Navara stock frame23 | T2/local7, `T2_Car8`, frame32 | `Frontend/VehicleSelect/carsheet`: 128×128 |
| Small image / Results | Navara stock frame13 | physical ID27, frame30 | `Frontend/RaceResults/smallcarsheet`: 32×16 |
| In-race progress marker | All `ProgressCar0..7` use shared `hud/hud-template` frame3 | unchanged | Shared 16×8 marker, not a Navara-specific vehicle thumbnail |

The UI banks are DXB frame lists referencing individual DXT files. No bitmap
atlas cells need moving. `carsheet.dxb` grows from 32 to 33 frames;
`smallcarsheet.dxb` grows from 30 to 31. All 62 stock records and textures stay
intact. Only the appended Subaru records use the new images.

DXT is the observed `0xFEED` wrapper around raw BGRA8; it is not block-compressed.
All 62 stock UI files have a payload CRC32 at header word0x08. The new files
recompute it rather than retaining the donor pixel checksum. Dimensions,
header magic/format, row orientation and alpha are validated.

### GT3 source result

The local volume is `D:/Game/GT_Model-Tools/Exe/GT3VOLExtractor/GT3.VOL`.
Selective extraction of `menu/US/arcade_menu.imgs` found the named
`impreza_wrc_prot_01_mini`, index95, Tex1 offset `0x7FD40`, 1200 bytes.
GTPS2ModelTool 1.1.1 decoded a 64×32 orange car. **174 named mini entries share
these exact bytes**, including the other Subaru entries: this is unsuitable
as a genuine Subaru-specific source image. The tool reports
`SHARED_TEXTURE_REVIEW_REQUIRED`; the candidate does not use those pixels.

This establishes the contents of the inspected bank, not absence of every
possible Subaru image in the entire GT3 volume. A broader search of menu PMBs
or reconstruction of GT3's dynamic thumbnail production is deferred.

The candidate's Subaru image is an offline render of the actual V4.10 model,
with silhouette-derived alpha. It is explicitly a model-rendered substitute,
not an extracted original GT3 icon. Users can supply their own RGBA8 PNGs.

### Native evidence and race boundary

REA opened the exact retail x86 executable (SHA256 unchanged). Defined-string
search found `frontend/raceresults/smallcarsheet` at VA `0x006B55FC`; its native
reference at `0x0046AE33` has original bytes `68 FC 55 6B 00` (PUSH the string),
confirmed through PE VA-to-file mapping. Ghidra resolves the containing function
at `0x0046AB50`; decompiler context indicates Network frontend image creation.
This is static evidence, not original source or a live in-race observation.
RaceResults XML directly uses the SmallCarSheet bank and Broker-driven image
indices. The stock HUD XML instead uses the shared marker above. No separate
Navara-specific in-race bitmap was identified. New SmallCarSheet presentation
and any dynamic race consumers remain for the user's runtime test.

## Reusable SDK changes

- Optional `project_frame` manifest policy and hash-pinned `ui-assets.json`.
- Append-only bank builder/parser, alpha-aware contain filtering, correct DXT
  checksum and explicit runtime resource admission.
- Optional selective GT3 RoFS2.2/IMGS adapter with a user-supplied Tex1 decoder
  and duplicate-image reporting. No GT3 inputs are needed by the SDK itself.
- Existing `stock_frame` projects retain their previous outputs. The current
  runtime profile supports one ID27 UI project; multi-project atlas allocation
  is outside scope.

See `research/vehicles/sdk/ui-assets.md` for user-provided icons, extraction and
manifest examples. No UI subsystem refactor or body/material changes.

## Validation

- **181 focused synthetic tests PASS**, including 11 new UI/source-adapter
  tests and existing SDK collection/project/reentry and vehicle regressions.
- Project validation/build, author verification, runtime prepare/verify and
  launcher `--verify` / `--verify-launch-environment` PASS. No game launch.
- Runtime: 191 resources. Four new UI resources; of the 187 baseline resources,
  186 are byte-identical. Only `VehicleSelect.xml` changes, and only two values
  inside `T2_Car8`: normal image and unlocked image become32. Locked frame15
  and every other widget remain exact.
- Every body DX/DXT, wheel/fitment, livery, physics and collision resource is
  byte-identical to V4.10. Mercedes and all stock vehicles retain their assets.
- Native runtime operation count remains246. Only one replacement byte differs
  from V4.10: the ID27 SmallCarSheet `PUSH imm8` changes13→30, at file mapping
  offset2680892. No on-disk executable modification was performed.
- New frame names resolve from the appended records; dimensions, alpha,
  checksum and hashes pass. Candidate ZIP CRC and asset-member parity pass.
- Original EXE, installed `d3d8.dll` and runtime `Data.sma` unchanged. No push
  or publication. All derived proprietary assets remain private and ignored.

Candidate ZIP SHA256:
`99ba9f2aa6907e3e09009291cfe1eb81103d285002be5ee77b676e5916d99c04`.

Private output contains `preview/index.html`, source/converted PNGs and
`reports/final-ui-audit.json`, `reports/validation.json`, `reports/tests-focused.txt`.
REA details and intermediate diagnostics remain in the phase's ignored scratch
directory; the handoff source archive excludes that diagnostic baggage.

## Human runtime checks

Check Subaru versus stock Navara in Vehicle Select, leaving/reentering the
screen and locked/unlocked presentation. Check races, Results and any small
vehicle-image displays, including opponents. Confirm shared HUD marker behaviour
and unrelated vehicles. Extended-bank loading, sprite position/orientation,
brightness and native filtering are still unverified in-game.

## Reproduce

```powershell
C:/Python315/python.exe tools/build_vmesh411_ui_candidate.py --before .research-output/vehicles/vmesh410/v410-exp-002 --output .research-output/vehicles/vmesh411/v411-exp-005
C:/Python315/python.exe tools/validate_vmesh411_ui_candidate.py --stage .research-output/vehicles/vmesh411/v411-exp-005 --before .research-output/vehicles/vmesh410/v410-exp-002
```

Use a fresh output name when rebuilding. Optional `--icon` and `--small-icon`
accept user-provided RGBA8 PNGs instead of the candidate render.
