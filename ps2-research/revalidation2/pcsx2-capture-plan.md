# Bounded PCSX2 capture plan

Use the existing PCSX2 Nightly installation (`2.9.117.0`) and original canonical ELF/disc. Do not patch the ELF. The official [debugger documentation](https://pcsx2.net/docs/advanced/debugger/) describes the R5900 disassembly/register views; the [command-line documentation](https://pcsx2.net/docs/advanced/cli/) documents `-debugger` startup.

## Capture objective

Determine whether the static treeblend contract is exercised by the France1 `bush01` surface and, if possible, inspect its actual texture/state and the ordering around one visible region. The capture must tie a frame to France1 and a recognizable bush; a generic debugger screenshot is not enough.

## Procedure

1. Record ELF/disc identity, PCSX2 executable hash/version, renderer/backend, resolution, and the exact France1 course load.
2. Use a visible France1 `bush01` and capture the frame plus R5900 call/breakpoint context for the material handler `0x003ae618` or common producer `0x00312610`. Prefer a breakpoint or trace at the producer rather than modifying game memory.
3. Record selected mode, relevant GS `PRIM`, `TEST`, `ALPHA`, `ZBUF`, `TEX0`, `TEX1`, `CLAMP`, `TEXA`, `FRAME`, and texture/CLUT memory identity where the debugger exposes them.
4. Capture microprogram selector and VU micro-RAM around the relevant `MSCAL` if supported. Compare bytes with the static embedded program hash; do not infer residency from a matching embedded image alone.
5. If investigating the disappearance/ordering hypothesis, select one bush pixel and record color/depth after its draw and after subsequent overlapping candidates, or perform an equivalent non-invasive per-draw frame inspection. Record draw order and actual coverage.
6. Save unmodified screenshots and debugger logs under ignored `ps2-research/data/revalidation2/`. Add only compact hashes, addresses, state words and conclusions to tracked reports.

## Interpretation limits

A static GS template still does not prove it was selected for the captured draw. A matching VU image does not prove it was resident. A screenshot alone does not identify a material or packet. A global render-order observation must not be generalized from one local queue drain.
