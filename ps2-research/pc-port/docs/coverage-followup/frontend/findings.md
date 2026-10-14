# PS2 frontend vehicle models: bounded transfer feasibility

Status: SOURCE_FEASIBILITY_PARTIAL; no model replacement implemented.
Evidence: CONFIRMED_BY_BYTES. Runtime/menu ownership: NOT_PERFORMED.

This pass reuses the existing PackFS extractor, REFL1 vehicle wrapper readers,
WATER1 visual strip decoder and protected-retail Course SDK DX reader. It never
exports a full mesh, changes an original asset, changes renderer code or builds
another proxy. SHA-256 and strip/material/node offsets are in
`source-evidence.json`; source geometry stays private.

## Actual resources

The canonical archive contains **29** vehicle `COMPLETE.PSM` resources, while the
examined protected PC retail vehicle corpus contains **26** `complete.dx` files.
This is a resource inventory, not a verified 29-to-26 family pairing. The resources
live under `\TNG\DATAPSM\VEHICLES\<family>\COMPLETE.PSM`, rather than under the
frontend screen artwork directory.

The current strict vehicle grammar decodes COMPLETE resources for KAMAZ,
WOOLDAND and XTRAIL (terminal 101). UFO uses the already-supported standalone
`ffffffff` sentinel at exact EOF and also decodes without extending the grammar.
The remaining **25** resources reach a different exact terminal/trailer boundary:

```text
66 00 00 00 cd cc cc 3e cd cc 4c 3e ff ff ff ff
u32=102       f32=.4     f32=.2     u32=ffffffff
```

Those numerical values are original bytes, **not proved LOD or material meanings**.
The parser continues to fail closed: no decoded triangle totals are published
for those 25 files. Tata reaches this boundary at **352800** in its 352816-byte
COMPLETE resource. Its SHA-256 is
`fa4b83e8b7144ad1e3ae9e84531ca32fd23f07c0f95d4f53d3e3bf8d1dc3b0a3`.
A small future grammar extension must independently establish the original
terminal-102 consumer and trailer semantics; changing 101 to 102 blindly would
erase an actual format distinction.

## Two independent compiled-source controls

All matching uses source/model coordinates, unsigned vertex permutations and
maximum corner error <= 0.001. No fitted scale, rotation or translation is applied.
Complete and race CAR models remain separate sources.

| Source comparison | PC source faces | PC faces matching PS2 source |
|---|---:|---:|
| Forester complete.dx -> WOOLDAND COMPLETE.PSM | 2271 | 978 |
| Forester car.dx -> WOOLDAND CAR.PSM | 1845 | 1814 |
| Forester complete.dx -> WOOLDAND CAR.PSM | 2271 | 0 |
| Forester car.dx -> WOOLDAND COMPLETE.PSM | 1845 | 0 |
| Tata car.dx -> TATA CAR.PSM | 2022 | 1442 |
| Tata complete.dx -> TATA CAR.PSM | 2470 | 0 |
| Tata complete.dx -> TATA COMPLETE.PSM | 2470 | UNKNOWN: terminal-102 blocker |

WOOLDAND COMPLETE has 4261 nondegenerate, nonsuppressed authored source faces in
17 root material meshes. Its bounds are approximately
X[-1.1083,1.1191], Y[.00349,1.82675], Z[-2.18256,2.14200].
PC Forester complete bounds are X[-1.09477,1.09775], Y[-.00226,1.82674],
Z[-2.18256,2.14200]. The bounds are compatible; the unpaired faces remain
**unresolved**, not automatically new PS2 geometry. Source totals are not live
menu triangle budgets.

WOOLDAND COMPLETE materially differs from CAR: 12 root materials explicitly use
`carshiny`; two use `carflat`; one uses `carglass`; one contains the original token
`crashiny`, and one is untagged. **`crashiny` is retained as authored and UNKNOWN**,
not silently corrected to `carshiny`. There is no evidence here establishing
the unknown/default handler behavior. Current PS2 source resource SHA-256:
`5407780253d3c96817a3062f5f863c3dd935e68ed843d882fa2e145794299eec`.
PC Forester complete SHA-256:
`a38566e0d653c586fc53594de2276e8c3f50d882126f26ee5792d74794cd3ca1`.

The zero cross-model matches mean race CAR signatures cannot serve as menu
COMPLETE identity. They do **not** prove unrelated vehicle shapes. Menu models
can have different geometry, placement of individual parts, UVs and partitioning;
no world transform or per-part placement has been inferred from screenshot bounds.

## Smallest defensible future implementation

**Feasible first source:** WOOLDAND COMPLETE -> PC Forester complete, since both
original sources parse safely and have independently matching triangles. Menu
replacement should be a separately disabled experiment in the existing overlay.

Before drawing replacements, establish a same-session native frontend model
owner, current COMPLETE VB/IB generations, exact draw ranges and world/view/
projection inputs. A texture name or menu draw ordinal is insufficient. The
current race-only reflection admission must not be broadened to all frontend
compiled draws; unrelated UI and trophy geometry also use generic emitters.

Then prove the complete current menu vehicle source-draw set and whether wheels,
glass, lamps or conditional variants share those buffers. Only that verified set
may be suppressed and replaced. A partial replacement without this proof could
duplicate wheels or body panels. Preserve menu model rotation, clipping, reset
and device-loss handling. Converted private meshes/textures must remain local and
hash-verified; no original complete.dx writing is required for an overlay pilot.

PS2 geometry cannot be copied into a retail DX file unchanged. The 52-byte PSM
source vertex and source strip/ADC representation need the already-known visual
conversion, with original normals, UVs, colors and material ownership retained.
Exact material defaults, `crashiny`, pixel alpha conventions and menu reflection
source/camera path remain independent questions. Neither source transfer nor
this comparison proves PS2 visual parity.

**Decision:** GO for bounded frontend native identity capture and WOOLDAND source
preparation; NO-GO for an immediate global complete-model replacement. Tata and
24 other models additionally require the precise terminal-102 reader contract.
No runtime mutation or integration is performed by this audit.

## Reproduction and validation

Executed from re-general on master, starting HEAD
`22c0ccad5c849f949e7275e9b4afb09da6e75b93`:

```powershell
python ps2-research/pc-port/docs/coverage-followup/frontend/audit.py
python -m unittest discover -s ps2-research/pc-port/docs/coverage-followup/frontend -p test_audit.py -v
```

Audit verifies the canonical PS2 inputs before decoding. Requires private
`D:/Game/Master Rallye PS2/{SLES_509.06,SYSTEM.CNF,TNG.PAK,TNG.000}`, protected
`D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Vehicles`, and the
read-only SDK at `D:/Game/Master Rallye/master-rallye-re-course/src`.
The four metadata tests need only the committed JSON; three synthetic format
tests import the existing helper and require the external SDK module, but no game
corpus. **7/7 tests PASS**. Synthetic tests verify exact-EOF sentinel handling,
terminal-102 rejection and ambiguous resource rejection. Runtime tests were not
performed. No build or renderer change is part of this workstream.
