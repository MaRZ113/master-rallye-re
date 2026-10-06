# Human R-GFX3 test — A through F

Use an isolated stock installation with pristine EXE SHA256 bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4. Preserve the historical R-GFX2 DLL and original assets; use the new renderer/.build-msvc/Release/d3d8.dll for this test. Its identity is in data/build.json. No installation/deployment was performed by Codex. Config MRRRenderer.ini goes beside this DLL, logs in MRRRenderer/logs. Completely restart the game between config changes; no hot reload. F10 remains a complete-frame capture with the previously accepted brief hitch.

For each config copy the full MRRRenderer.ini.example, set only the values in the table, and keep Trace.Enabled=true. Keep ConfigVersion=1.

| Run | AnisotropicFiltering / MaxAnisotropy | GameplayFOV / VerticalFOVDegrees | Shadows.Mode | Required observation |
|---|---|---|---|---|
| A Stock | false /16 (or no INI) | false /75 | Stock | boot/menu/Quick Race/results/return frontend; no visible difference from R-GFX2; one active F10 frame |
| B AF | true /16 | false /75 | Stock | oblique road/terrain improvement, caps respected; no significant HUD/menu/vegetation artifacts; session+active F10 |
| C FOV | false /16 | true /80 | Stock | wider gameplay; unchanged HUD/menu640x480, sky placement; session+race F10+menu F10 |
| D Combined | true /16 | true /80 | Stock | several minutes, race/frontend transitions; no filter/projection leaks; session+frame |
| E Shadow | false /16 | false /75 | Off | only projected car shadow disappears; vehicle, trails, particles, world and HUD remain; restore Stock after restart and compare; session+frame |
| F Pristine Reset | true /16 | true /80 | Stock | safe minimize/restore while racing; S_OK Reset and continuing AF/FOV/HUD, session+post-reset F10 |

F is mandatory coverage: if minimize/restore produces no actual Reset, report NOT_OBSERVED; do not treat a resize or recovered window as Reset proof. Earlier R-GFX2 Reset was UNKNOWN_BUILD only.

Return each session/frame pair with labels A..F and brief visible observations (road sharper, artifacts, UI change, FOV/culling, shadow-only disappearance, recovery). Screenshots aid A/B but traces can be checked without them. Check frontend3D preview/replay/split-screen if accessible: the projection setter is shared, and those consumers are not fully covered by existing evidence. Report exposed upstream culling at wider FOV explicitly.

PASS requires trace and human observations: requested/effective AF matches caps, stage1/MIP/POINT remain stock; projection changes only recognized symmetric perspective X/Y and preserves Z, UI ortho remains unchanged; Off suppresses only exact shadow call and Stock restores it; default-off has no visible regression; pristine Reset is actually observed and preserves features. Any unexpected draw disappearance, projection/filter leakage, crash, broken alpha/UI or failed recovery is FAIL. Do not close R-GFX3 or start R-GFX4 until the human acceptance set is evaluated.

Offline check from repository root:
```powershell
python modernization/renderer/tools/summarize_visual_trace.py <frame.jsonl> --output modernization/renderer/.analysis/<label>-summary.json
```
Raw captures/screenshots/DLLs stay external or ignored; commit compact hashes and derived findings only.
