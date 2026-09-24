# Build-specific model and texture cache evolution

| Path | Demo 8.4.1 | Demo 9.3.1 | Retail |
|---|---|---|---|
| Vehicle GXM | Trooper car/complete/wheel are live sources; Debug window reports `Caching disabled. Reading GXM` and model-cooker stages on observed path (**CONFIRMED_BY_RUNTIME**, human). | Present GXM can generate a persistent DX (**CONFIRMED_BY_RUNTIME**, human). | No equivalent live-source behavior established here. |
| Vehicle DX | Removing same-stem DX with GXM present did not visibly change tested Trooper resources; DX-only did not restore tested visuals. File access remains unknown. | Existing/generated DX can load without GXM. Observed on complete and wheel; other roles should be tested separately. | DX is the established compiled vehicle authoring target in R4G. |
| Texture GXI/DXT | Clean Trooper Black GXI regenerates a DXT byte-identical to shipped and offline-converted bytes. | Existing static GXI/DXT correspondence and texture-cache EXE strings; clean live cache order has not been traced. | Existing DXT parser/writer work remains separate. |
| Debug output | Visible window and compiler-stage messages; Win32 `WM_GETTEXT` helper failed to locate/read it in user testing. | No visible Debug window in user test. | No claim. |

The 8.4.1→9.3.1 change is a **runtime-confirmed behavior difference** for the named resources. Whether it is controlled by a flag, configuration, timestamp rule or build constant remains **UNKNOWN**. DebugView and ProcMon traces are needed before asserting lookup/probe order. This is a targeted model; it does not imply all DX files are unused in 8.4.1 or that retail retains a live GXM cooker.

Targeted EXE xrefs show near-parallel GXM status/reading paths and null-result fallback calls in both builds, but not the reason the observed runtime cache policy differs. See `targeted-cache-xrefs.md`.

A subsequent two-run 9.3.1 Trooper car DX regeneration produced identical bytes in rebuild-A and rebuild-B. This supports run-to-run cooker repeatability for the fixed source; it does not identify cache invalidation policy or explain the shipped original difference. See `rebuild-determinism.md`.

The user also confirmed that the custom car DX generated from a visible GXM position edit loads with GXM absent and shows the edit in 9.3.1 (**CONFIRMED_BY_RUNTIME**). This extends the tested DX-only fallback beyond the reported complete/wheel cases, but file-probe order is still untraced.
