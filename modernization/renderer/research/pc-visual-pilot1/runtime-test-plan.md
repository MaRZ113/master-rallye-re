# Required first runtime capture

**This checkpoint changes no foliage appearance. Mode1 is blocked; do not treat it as the enabled visual A/B build.** Existing R-GFX5 human acceptance also remains separate.

1. User keeps a recoverable copy of the existing game proxy and INI, and manually selects the diagnostic build at `modernization/renderer/.build-msvc/Release/d3d8.dll`. Codex did not deploy it. Verify the build hash against validation.json.
2. Keep current renderer settings unchanged. Add the following to the existing INI,restart,and launch France1 explicitly:

```ini
[Renderer]
ConfigVersion=1
[PS2FoliagePilot]
Mode=0
Diagnostics=1
[Trace]
Enabled=1
FrameSummaries=1
```

3. Record selected course and recognizable view; pressF10 once near the selected bush region. Capture a second view nearby and a separate frame on another course, and retain session+frame JSONL files. Record failures/unchanged appearance. Diagnostics are independently opt-in; settingMode1 will also remain effectivelyStock.
4. Send the new frame/session files and course/view identification. In the inspected installation the log directory is `D:/Game/Master Rallye Pristine/MRRRenderer/logs`; the supplied `D:/Games/.../MRRenderer` spelling did not resolve locally. Use the directory actually created alongside the chosen DLL.
5. Analyse one new frame:

```powershell
python modernization/renderer/tools/foliage_identity.py audit --source-manifest modernization/renderer/research/pc-visual-pilot1/source-signatures.json --capture <frame.jsonl> --observed-course FRANCE1 --output modernization/renderer/.analysis/pilot1-frame-audit.json
```

6. Content matches still require ownership/upload/lifecycle review. `buffer_not_safe_for_readonly_probe` needs a targeted CPU upload-owner investigation; do not enable alternate readbacks or broaden matching. `capture_budget_or_disabled`/truncation requires another bounded capture. Unlock failure requires stopping/restarting the diagnostic run.
7. Return Diagnostics=0 and restart for ordinary usage. No source assets were replaced.

After a separately verified state-override build exists,user stages are PCMode0 baseline,PCMode1 enabled,same-region PCSX2 France1 reference,and silhouette/edge/alpha/tint/front-back/depth/distance/order comparison. Those stages are **pending**, not performed here. Source48records are not a known live submission count; no existing F10 ordinal is assumed to be source54.
