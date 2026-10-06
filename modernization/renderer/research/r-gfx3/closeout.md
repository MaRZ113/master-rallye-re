# R-GFX3 final fix and closeout gate

**READY_FOR_SHORT_RETEST.** Repository D:/Game/Master Rallye/master-rallye-re-general, branch research/general-re, starting HEAD2e6eaea (clean). No new branch/worktree or push. Final candidate SHA25644a76a3a3e96573393b7ee1e492734b62d9c2ef8baae369711ce7c419615efef, 1016320 bytes, PE32/I386.

Only two behavior changes: AF rewrites stage0 LINEAR MIN with native caps; MAG/MIP/stage1 and POINT remain requested. GameplayFOV adds source_angle = decoded VFOV * max(1,aspect), accepting90 +/-0.01 degrees after the existing exact-build/module/callsite/symmetric-LH gates. Preview45 and unknown families forward original pointer/values. All14 non-X/Y projection floats, VIEW and camera ownership remain unchanged. MAX anisotropy and getter virtualization retain existing contracts.

44 Python tests,2 native suites, compileall, PE/export/import validation and diff-check pass. Pre-fix A–F observations and trace totals are separately recorded in runtime-summary.md; camera evidence is in camera-findings.md. R-GFX1/R-GFX2 and prior wheel/state evidence remain preserved. Shadow Stock/Off is unchanged; Opacity DEFERRED.

Remaining gate is the two short human checks in runtime-handoff.md, not a full A–F rerun. No new lighting, reflections, shadows, weather, postFX or freecam. R-GFX4 may follow only after human PASS and separate authorization.
