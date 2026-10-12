# PS2-R5900-REVALIDATION2

Independent byte-level audit of the original France1 `treeblend` path, its
source-alpha inputs, PS2 GS state, within-drain ordering and VIF/VU/GIF
contract, correlated with the user's four PC D3D8 PILOT1.3 captures.

**Status: PARTIAL static/runtime revalidation.** The original R5900 words,
material callbacks, GS mode masks and queue order are independently checked.
The four PC modes are now tied to the same France1 draw and their state
changes/restores are visible in complete F10 captures. The exact pixel-level
occluder, live PS2 `As`, live VU residency and PS2 runtime appearance remain
unknown.

Read in this order:

1. [Preflight and inputs](preflight.md)
2. [R5900 byte and function audit](r5900-function-map.md)
3. [Material and GS contract](material-and-gs-contract.md)
4. [Alpha provenance](alpha-source-path.md)
5. [Queue and VIF/VU/GIF path](queue-and-vif-pipeline.md)
6. [PILOT1.3 evidence](pilot13-runtime-analysis.md)
7. [PC and PS2 comparison](pc-vs-ps2.md)
8. [Open questions](unresolved.md)
9. [PCSX2 capture plan](pcsx2-capture-plan.md)
10. [Validation](validation.md) and [next experiment](next.md)

Machine-readable evidence is in [elf-functions.json](elf-functions.json),
[render-contract.json](render-contract.json),
[instruction-probes.json](instruction-probes.json), and
[runtime-correlation.json](runtime-correlation.json). The last two summarize
bytes and capture metadata only; the proprietary executable, assets, raw
screenshots, full F10 streams and Ghidra project stay outside Git.

The independent Ghidra/Rabbitizer tooling does not replace the earlier
TREEBLEND1 analysis. It verifies selected facts against the exact canonical
ELF and adds a separate, reproducible PC runtime comparison.
