# R-CAM1-A3h.1 runtime handoff

Use the built diagnostic DLL at:

```text
modernization/renderer/.build-msvc/Release/d3d8.dll
SHA256 09178fd974602614c294bd01a9c79d31c452112a75e18c54762ab1db90b1b272
```

Run it only with the pristine retail executable; the session must report EXE SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and the DLL hash above. Use the existing local game/wrapper setup and keep its accepted Freecam configuration unchanged. In `MRRRenderer.ini`, set `[Trace] Enabled=1`; restart the game after changing it. Do not enable or configure a HUD suppression feature; none exists in this build.

1. Start one France1 normal race with the regular HUD visible. Press F10 once, wait for that capture to finish, and label its frame file `frame-normal-*.jsonl`.
2. Open the native pause menu, leave the race HUD and pause overlay visible, and press F10 once more. Wait for that capture to finish and label its frame file `frame-paused-*.jsonl`.
3. Exit normally. Keep the one `session-*.jsonl` with both frame files. Do not restart the race or change the EXE/DLL between captures.
4. If `Race/PauseMenu/Enabled` was unavailable in either frame, keep the normal/paused filename labels as the operator ground truth; do not infer state from pointer or texture changes.

Run the analyzer from the repository root:

```powershell
python modernization/renderer/tools/analyze_ui_ownership.py `
  --session "<logs>\session-....jsonl" `
  --normal-frame "<logs>\frame-normal-....jsonl" `
  --paused-frame "<logs>\frame-paused-....jsonl" `
  --output "modernization/renderer/data/a3h1-ownership-report.json"
```

The report should show both complete captures, no overflow, matching EXE/DLL hashes, the same device/process session, capture-end records for both F10s, and nonempty verified UI draw records. Compare shared and state-specific packet tuples, capture-local IDs, identity rejection reasons, and the read-only pause bool when available. A typed `false -> true` pair corroborates the labeled pause transition, but it does not name any draw owner. The current build always reports owner mapping as unmapped; paused-only rows are not PauseMenu classifications.

**Probe PASS:** the exact build and DLL match, both F10 frame files and session records are complete, the probe is enabled, UI draw/entity/packet scope records are present, overflow is zero, and the read-only pause signal is either validated or clearly unavailable with manual labels retained.

**Probe FAIL / recapture needed:** build mismatch, missing F10 file or capture-end event, disabled probe, truncated frame, overflow, changed device/session/hash between captures, or no usable entity/packet-scope records despite the live UI being drawn. Do not proceed to suppression on the basis of paused-only rows. Semantic HUD/pause ownership remains blocked until the native Egg/owner relationship is separately validated.
