# Retail model cache cooker — static evidence

## Executable and analysis provenance

- Retail executable: `corpora/retail/MRallye.exe`, 3,121,214 bytes,
  SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Retail archive: `corpora/retail/Data.sma`, 282,396,172 bytes,
  SHA-256 `03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f`.
- Ghidra: the newest installed local build, 12.1.4 PUBLIC, with the existing
  Ghidra Bridge. Analysis project, JSON exports, and raw ASM/xrefs are under
  ignored `research-output/r5v_f_2a/`; no Ghidra database is committed.
- Evidence class: `RAW_GHIDRA_SUPPORTED` for instructions, direct calls and
  constants; decompiler output was cross-checked against assembly/P-code.
  These results are static. No retail runtime output is claimed.

## Narrow loader/cooker path

| Address | Observed role | Evidence / limit |
|---|---|---|
| `0x0053BE70` | Parent model loading path | Direct call to `0x0053C3F0`; xrefs and disassembly in ignored Bridge exports. |
| `0x0053C3F0` | `.gxm` / `.dx` cache select and rebuild | Constructs both extensions from a model base. On cache miss calls `0x00609190`, then `0x0054D6E0` and `0x00551260`. Logs `Reading GXM`, `Making dx model`, and `Saved cached model`. |
| `0x00609190` | GXM parse entry | Calls recursive loader `0x00609E90`; direct xref from `0x0053C3F0`. |
| `0x00609E90` | Recursive GXM object/tree loading | Supports nested source structures; full GXM semantics are outside this bounded audit. |
| `0x0054D6E0` | Cooked-model postprocessing path | Called between GXM build and serialization; no attempt to rename every opaque helper. |
| `0x00551260` | DX cache writer | Direct caller `0x0053C3F0`. Raw ASM at `0x005512AF` pushes `0xD00D`; at `0x005512BD` pushes `0x87` (135). |
| `0x0064D530` | File open / archive-aware access helper | Calls `CreateFileA` first; archive fallback depends on additional context and matching a recognized `DataGx/`-style prefix. |

The cache gate in `0x0053C3F0` compares the metric returned for source GXM
against the metric for cached DX using a `+0x14` tolerance, requires caching to
be enabled, and calls `0x00551970` to accept the cache header. The meaning of
`0x0064D1C0`'s metric is not proven here; do not describe it as a timestamp or
file size. On the miss branch the retail loader logs the source/build stages,
parses GXM, then reaches the writer. This proves an available static source
path and its intended DX revision, not that the chosen Mercedes GXM succeeds.

## Output revision

The retail writer entry contains the raw immediate values `0xD00D` and `0x87`
passed to the output stream. `0x87` is decimal 135. The writer call is a direct
xref from `0x0053C3F0`, after model construction. Thus the expected cache output
is retail DX revision 135. No generated file exists in this phase, so output
header/footer correctness, parser acceptance, semantic content, and runtime
loading remain untested.

## Reproduction artifacts

Focused Bridge exports and disassembly are in:

```text
research-output/r5v_f_2a/ghidra-exports-12.1.4/0053be70.json
research-output/r5v_f_2a/ghidra-exports-12.1.4/0053c3f0.json
research-output/r5v_f_2a/ghidra-exports-12.1.4/00551260.json
research-output/r5v_f_2a/ghidra-exports-12.1.4/00609190.json
research-output/r5v_f_2a/raw/retail-0053c3f0.asm.txt
research-output/r5v_f_2a/raw/retail-00551260.asm.txt
```

Only the retail executable above was analyzed in the clean 12.1.4 project for
this phase. No demo address was transferred to retail.
