# Frontend COMPLETE source and live identity

Decision: **GO for bounded current-upload geometry diagnostic; NO-GO for blanket
COMPLETE suppression until the current frontend resource owner is joined.**
No renderer edits, game-memory reads/writes, builds or private mesh exports were
performed by this workstream.

## Source inventory and independent negative controls

`source-and-live-evidence.json` inventories all **26 original PC complete.dx**
resources, with source SHA-256, record paths/offsets, vertex/index ranges, flags,
ordered texture slots and unsigned float32 position hashes. All **78 vehicle DX**
resources (COMPLETE, CAR and WHEEL) decode through the existing read-only SDK.
Every **Forester COMPLETE record is unique to Forester/complete.dx** among those
78 resources, including all wheel groups. Forester CAR/WHEEL and other vehicle
families do not share those 17 complete-record geometry digests. This is a bounded
vehicle-corpus negative search; UI and all scene resources were not exhaustively
decoded. Full current upload digest, caller/context and generation checks remain
necessary before any replacement.

Forester complete SHA:
`a38566e0d653c586fc53594de2276e8c3f50d882126f26ee5792d74794cd3ca1`.
It contains **17 compiled records, 2,713 source vertices, 2,271 triangles**.
These records include wheels, chair/interior, lamps and transparent glass;
COMPLETE is not a race CAR body plus independently posed wheels.
PS2 WOOLDAND COMPLETE SHA:
`5407780253d3c96817a3062f5f863c3dd935e68ed843d882fa2e145794299eec`.
PS2 FORESTER remains a separate source family.

## Same-session frontend rotation control

Actual captures: session **23804**, `frame-23804-d1-00001235.jsonl` and
`frame-23804-d1-00002726.jsonl`. Original EXE:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`;
proxy: `0013ed2de827c959e6745e73212f4e0e17118dba424287ddfb825a1cf891c848`.
Both report requested/committed `FrontendScreens/VehicleSelect`, no current race
certificate, successful Reset epoch 0 and all **17 indexed model submissions**
from original generic compiled-model emitter return RVA **0x17707e**.

All source records have a unique one-to-one layout join in each captured frame:
native primitive/vertex counts equal their source record, and every native index
start equals source index start plus **30,042**. Native order differs because flat
materials precede environment materials. Three draws use **FVF 0x142 / stride 24**;
14 use **FVF 0x152 / stride 36**. Current captured VB creation generation is 624,
IB generation 625; both are unchanged between the two observations. These numbers
and pointers are observations only and cannot be implementation constants.

All 17 draws in each frame share one exact world matrix with translation
**[8,-2,189]**. World rotation differs between frames; view/projection matrices are
bit-identical. That translation independently agrees with original VehicleSelect
XML CarModel Egg Row3. Native rotation should therefore be inherited from the
current verified draw world matrix. The exact matrices/bits are in the evidence.
This proves the recorded model uses a common draw transform; it does not prove
all possible frontend models lack per-part transforms.

The F10 files do **not** contain the selected draw's CPU vertex/index bytes or
position SHA-256. Layout correlation and the human selection of Forester establish
a strong candidate, not a current immutable render-resource certificate.

## Native owner contract and the precise outstanding gate

REA uses original x86 EXE and Ghidra 12.1.4. Compact evidence and independently
mapped original bytes are in `native-owner-evidence.json` and
`native-byte-validation.json`. Relevant original contracts:

| Native source | Proven bounded behavior |
|---|---|
| `0x480a20`, vtable `0x690b08` | Constructs `gaFEScreenVehicleSelectAI` |
| `0x4819b0` | Publishes selected ID or -1 to `Frontend/VehicleSelect/CarModel` |
| `0x481e20` | Computes selected vehicle index from class and per-class cursor |
| `0x44c2a0`, vtable `0x69020c` | Constructs `gaFrontendCarMoverAI` |
| vtable `0x69020c+0x10 -> 0x44c4c0` | Callback resolves authored Model ID* via Broker, compares selected ID, constructs vehicle resource path plus `/complete`, then sets the Egg's en3d model |
| `0x4f5b70` | Stores en3d state's model-name string ID at +0xc; destroys and clears cached owned object at +0x74 on a name change |

Ghidra does not currently define a function at `0x44c4c0`; no bounds were invented.
Its entry is independently grounded in the original vtable, and 31 compact
instruction windows were decoded individually by REA and checked against the
canonical original PE. The en3d cached object's compiled-model type and buffer
relationship remain unproved in this bounded chain.

**Missing join:** current frontend CarModel Egg -> its en3d state -> current
model-name string/path and cached resource lifetime -> current mirrored VB/IB
draw set, inside a stable same-frame vehicle-selection context. Broker's selected
ID alone is insufficient: it changes before the name setter completes, and the
setter clears the cached loaded object. A retained previous-frame manifest could
incorrectly suppress newly selected geometry without this current join.

## One-mesh candidates: source relationship is not assumed

`mesh-joins.json` independently evaluates original model-local surfaces without
fitting a transform. The relaxed .005 threshold is reported separately from .001.

| Candidate | PC -> PS2 matched at .001 / .005 | Duplicate/overlap boundary |
|---|---:|---|
| PC COMPLETE record 5, 400 faces -> WOOLDAND COMPLETE root.4, 484 carshiny faces | 357 / 364 | Full PS2 root overlaps other PC groups 0/2/3/4/9; 120 PS2 faces lack a selected-record triangle counterpart, and one overlaps PC sticker group 9 |
| PC COMPLETE record 1 grille, 4 faces -> WOOLDAND COMPLETE root.2, 19 carshiny faces | 0 / 0 | Different extent/depth; no .005 coplanar overlap with other PC groups found, but replacement correspondence is not proved |

Thus record5 is a defensible **partial material/shape correspondence**, not a
safe whole484-face replacement. A smallest source-backed alternative partitions
only independently matched corners/faces, excludes overlaps with retained PC
groups, and preserves unmatched PC faces. The complete source model can be
prepared privately, but whole-model replacement must wait for the native owner
gate. No grille assignment is accepted merely from its name or position.

## Commands and validation

Actually executed from re-general master, HEAD
`a6daf3b17d32043c948e3ed9a843b1a5b3258f16`:

```powershell
python ps2-research/pc-port/docs/vehicle-model-port1/frontend-identity/audit.py
python ps2-research/pc-port/docs/vehicle-model-port1/frontend-identity/mesh_join.py
python ps2-research/pc-port/docs/vehicle-model-port1/frontend-identity/verify_native_bytes.py
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-model-port1/frontend-identity -p test_audit.py -v
```

Metadata and synthetic tests run without original game assets or external SDK.
The focused metadata/synthetic suite reports **12/12 PASS**. Original PC executable
SHA, **31 instruction windows**, and the original CarMover vtable callback pass
independent file-offset validation. Compileall and diff-check pass for these files.
Full source inventory needs protected PC DX corpus and read-only Course SDK.
PS2 mesh joins need original PackFS corpus and existing PSM helpers. Live evidence
reanalysis requires the two exact F10 files. Native-byte validation requires the
canonical PC EXE. Larger original assets stay private and unchanged.
