# Claim ledger

| Subsystem | Original claim | Original evidence | Independent REA evidence | Raw executable / asset evidence | Runtime evidence | Agreement / confidence | Correction | Residual unknowns | Next observation |
|---|---|---|---|---|---|---|---|---|---|
| PC material selector | Flags select base, alpha, or alphatest variant | Prior PC source/runtime research | REA decompiles `FUN_00580360` and registration `FUN_00565DA0` | Verified retail PE hash; object field flow | No raw France1 state trace | Agrees; high static | None | Final live course state | Capture selected target state if needed |
| PS2 tree/treeblend | Tree cutout vs treeblend blend/depth-mask modes | Prior canonical ELF analysis | R5900 unsupported by configured REA backend | Prior `instruction-evidence.json` / `render-contract.json`; not freshly decoded | No live PS2 GS capture | No contradiction; high prior static, provider-limited audit | None | Inherited GS state, runtime alpha, VU residency | Compatible runtime capture/provider |
| PS2 queue order | bucket0 before bucket1 within one drain | Prior ELF chain at `0x0031cd98` | No PS2 REA analysis | Prior original ELF evidence | No global order trace | Valid only per drain; medium prior static | None | Global sort/cross-queue order | None selected now |
| France1 geometry | 24 PS2 faces correspond to 24 unique PC faces | TREEBLEND1/GEOM1 | Not a REA asset claim | Canonical PSM/DX hashes, focused parser test; strict source match | Live classifier raw trace absent | Agrees at source level; high | None | Runtime buffer generation and active LOD | Keep raw trace next capture |
| Texture alpha | PS2 64²/89 alpha values vs PC 128²/15 | Prior texture decode | Not applicable | Original GXI/DXT hashes and focused test rerun | Bound-stage samples unknown | Agrees; stored bytes high | None | TEXA, diffuse alpha, filtering/orientation | Capture texture stage and diffuse |
| PC state family | alpha vs alphatest state branches differ | Prior PC static research | REA address mapping only at `0x5867a0`; no Ghidra function | GNU objdump over same PE bytes confirms branch writes | No raw target state trace | Agrees with provenance qualification | No source claim disproved | Later/inherited state | None for this audit |
| PILOT1.3 draw identity | 5,364 events and target args/state restore | User-supplied report | Not applicable | Source geometry match supports candidate, not live identity | Raw trace absent | Not independently rechecked; user-reported | None | Capture provenance/current generations | Attach raw trace/screenshots |
| PILOT1.3 mode outcomes | 0 visible, 1 almost gone, 2 white cards, 3 almost gone | User observation | Not applicable | State masks known from existing overlay; no image data | User-reported only | Directional low-to-medium | None | Alpha-vs-blend, depth overlap, repeatability | Alpha-test-only PILOT1.4 mode |

Machine-readable detail and evidence IDs: [claim-ledger.json](claim-ledger.json).

Labels follow the project vocabulary. “The REA provider did not inspect this
target” is not treated as contrary evidence against previously confirmed
canonical bytes. A historical runtime report without its raw file remains a
user/runtime observation, not an independently reproduced capture.
