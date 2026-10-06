# R-GFX1 — pristine retail D3D8 reconnaissance

Status: **MORE WORK NEEDED** against the full 28-question success gate. The
startup, state cache, common draw paths, camera/fog seam and resource mechanisms
are mapped, including the application frame owner and per-camera scheduling.
Several semantic draw categories, complete layout usage and capture/offscreen
reachability remain open. No runtime rendering PASS is claimed.

Starting branch: `research/r-ui1`. Starting HEAD:
`bd27cc1c12099b7062d251fa476fe62586ac4444`. After the initial unrelated untracked
files were removed by the user, the repeated status and diff checks were clean.
Research branch: `modernization/renderer-recon`. No push, game patch, DLL, hook,
asset replacement or existing research edit belongs to this phase.

Primary input: external `D:\Game\Master Rallye\MRallye.exe`, 3,121,214 bytes,
SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
PE32 x86, ImageBase `0x00400000`; complete headers/sections/imports in
[build.json](data/build.json) and [imports.json](data/imports.json).
No other build supplies canonical addresses here.

All eight-digit code/data addresses in prose are **VA**. RVA is VA minus
`0x00400000`; JSON call records and the evidence index carry explicit VA/RVA.
Offsets such as `+0x68` are object offsets, not addresses. Stable research names
describe a traced role and retain the original VA; they are not recovered symbols.

Evidence grades: `CONFIRMED_BY_EXE` means exact-image instructions/arguments or
headers; `CONFIRMED_BY_EXISTING_RESEARCH` means an identified read-only project
source; `STATIC_INFERENCE` means a conclusion from those facts with stated limits;
`HYPOTHESIS` includes unresolved proposals. Code presence does not prove runtime
frequency or reachability. Corpus observations identify external input data and
do not establish its runtime use by themselves.

Start with the [concise report](report.md), [findings](findings.md), [device creation](device-creation.md),
[vtable inventory](device-vtable.md), [state cache](state-cache.md),
[frame structure](frame-lifecycle.md), [master map](data/renderer-map.json) and
[runtime handoff](runtime-handoff.md). The other topic files document supporting
paths and explicit unknowns. [validation](validation.md) records reproducibility.

Analysis uses the installed **ghidra-bridge exporter** with Ghidra **12.1.4**, the
newest installation found on D:. The exact retail database at
`research-output/r5t_d1/MasterRallye-clone` was opened read-only; temporary function
queries rolled back. Nothing was saved to that project. Raw exports/settings stay
ignored under `.analysis/`; curated evidence and small instruction bytes are
tracked. Decompiled prototypes are often wrong: COM identities and important
arguments were checked against instructions.

Reproduce from the repository root, using Python with `pefile` and `capstone`:

```powershell
python modernization/renderer-recon/tools/scan_d3d8.py ../MRallye.exe --output modernization/renderer-recon/data
python -m compileall modernization/renderer-recon
python -m unittest discover -s modernization/renderer-recon/tests -v
git diff --check
```

The scanner emits JSON and TSV. `--candidates` can emit a large untyped candidate
list; direct it to `.analysis/`. An offset candidate is never automatically
promoted to a COM call. The human-reviewed bindings are byte-checked on every run.
