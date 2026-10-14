# Visual coverage follow-up — 2026-10-14

Status: **RESET_FIX_IMPLEMENTED_PENDING_RUNTIME / REMAINING_BODY_COVERAGE_PARTIAL**.
Starting HEAD:22c0ccad5c849f949e7275e9b4afb09da6e75b93, branch master.
Ending source commit: handoff release-provenance.json.
Frozen renderer tree:e33386bcf682db6983380c499e4928726c758fe0.
Staging source commit:0bddf7c7bc5e95831f98714ff6231da05ab073ea.
No original renderer, game assets or Course SDK changes; no deployment/push.
Physics/HUD implementation remain paused.

## Actual implementation: retain valid Reset-surviving upload evidence

The original successful Reset wrapper poisons **every** CPU mirror. Model
vertex/index resources created in D3DPOOL_MANAGED remain valid and need not
receive another CPU upload. The strict PS2 identity then lacks its original
bytes. This is a source-proved defect consistent with the user's disappearance
after window reset. Pre-fix logs include managed buffers and successful native
resets; the exact first failing post-reset identity gate was not logged. No
post-fix game run is claimed.

The updated staged-only integration patch retains an existing CPU mirror when:

* A PS2 feature actually requires mirroring; Stock keeps previous behavior.
* The invalidation reason is exactly `device_reset`.
* The mirror is available and unpoisoned, in MANAGED or SYSTEMMEM pool.
* Its nonzero generation agrees with both current resource registry and the
  still-registered proxy generation.

No data is revalidated or manufactured. DEFAULT buffers, unknown generations,
raw escapes, failed uploads and already-poisoned mirrors remain invalid. The
existing memory limits, Lock/Unlock, resource destruction and raw-QI rules are
unchanged. Buffer bindings are still cleared; successful native Reset removes
non-survivors from the existing resource registry, invalidates native state and
advances the PS2 reset generation. Exact signatures/current native state and
race certificates are still required after Reset.

Internal window-commit reset echoes retain their existing early return and do
not enter this lifecycle. Failed native Reset still suspends reflections until
real successful Reset; an echo cannot resume it. Private reflection render
targets are released/recreated using the existing lifecycle. The capped
identity log is rearmed on real successful Reset, so post-reset admission can
be observed. One optional `ps2_buffer_mirror_reset` event records retained/revoked
counts at each wrapper Reset, not each frame.

The frozen resource registry already marks MANAGED/SYSTEMMEM/SCRATCH as reset
survivors. This correction conservatively retains only owned buffer mirrors in
MANAGED/SYSTEMMEM. The original Microsoft DirectX8.1 documentation independently
describes the managed-resource guarantee:
[Managing Resources](https://library.thedatadungeon.com/directx81-c/directx_cpp/Graphics/ProgrammersGuide/UsingDirect3D/AboutDevices/Resources/ManagingResources.content.htm).

Implementation files: renderer/buffer_reset_policy.hpp,
renderer/reflection_pilot.cpp, tests/reflection_pilot_tests.cpp,
tests/test_coverage_followup.py, overlay/patches/0001-renderer-integration.patch
and the corresponding exact patch hash in overlay/baseline-lock.json.
Generated interfaces, generator patch and renderer source/tree are unchanged.

## Remaining six vehicle families

The user confirms the preceding fix worked on other listed cars and improved
most WOOLDAND body coverage. This is USER_RUNTIME_OBSERVATION, kept separate
from source joins or synthetic tests.

New all-material comparisons show the remaining PC draws cannot all be
classified as uniform dynamic carshiny:

| PC source record | Remaining source relationship |
|---|---|
| SeatBuggy7 |4/169 faces remain unjoined |
| Bruno4 |3/232 remain unjoined |
| LandCruiser8/9 |25/240 and104/477 remain unjoined |
| ChevyBlazer7 |60 carshiny faces plus10 carglass |
| Xtrail1 |195 carshiny plus14 carflat |
| Forester8/9 (PS2 WOOLDAND) |Shiny faces mixed with generic mode3 retaining original perspex/whitepaint |

These are compiled source records, not live draw ordinals. The .005 diagnostic
does not loosen the exact runtime digest. New signatures/material policies
were **not** activated for these mixed/unproved draws. Grille Forester2 is a
small complete source join, but current normal/environment input remains a
live gate; Xtrail21/22 are alpha-carshiny groups outside the current opaque
transaction. Driver helmets and authored rubber remain separate.

The narrow safe continuation is a material-subset/visual-body replacement with
explicit glass, lamps and current pose ownership, rather than a blanket whole
draw override. The existing212-entry registry and working Mode4 compositing
are preserved. No claim that these six visual defects are now repaired.

## Stop lights are not one body-reflection material

Fresh read-only Ghidra12.1.4 Emotion Engine Reloaded
(`r5900:LE:32:default`) and Rabbitizer InstrCategory.R5900 verification checked
1308 original instruction words.92 short probes/function evidence remain
compact; full exports are ignored.

Canonical function391690 applies primary-name rules **after** shader dispatch:
`breaklightson-` selects final mode1; `breaklightsonglow-` selects final mode14.
29 CAR.PSM source families contain60 selected light-related mesh records:
28 final mode1,28 final mode14,4 mode3 off-light records. They are not counts
of simultaneously visible lights. Generic/default mode3 also differs from
carshiny: it retains authored secondary textures and has no carshiny auxiliary
initialization. Literal `crashiny` is not silently normalized.

Therefore adding the framebuffer/environment body override to all stop-light
draws would not reproduce the original PS2 contract and could break brake-on/
glow behavior. Off-light surfaces, on-light replacement and glow must be mapped
separately. The mode14 GS producer, live conditional child selection and exact
light texture sampling remain the bounded missing contracts. No lamp effect
was implemented speculatively. See body-lights/findings.md and byte evidence.

## Vegetation: missing deployed files, no loader defect

All72 private local source-derived assets hash-match the original registry.
The game has only6: Turkey3/France1/ItalyS1. The other66 for33 course pairs are
absent. Its INI already selects Mode2 and the correct PS2Grass directory.
Missing files fail closed at construction, explaining the reported coverage.

Copy all72 existing .assets/grass/*.ps2grass files manually into the configured
game PS2Grass directory and start a new process. No positions, density, culling,
loader, source texture or course admission change is needed. This task copies
nothing into the game. Original texture-bearing assets are excluded from Git
and handoff. Full course appearance/FPS after installation remains pending.
See vegetation/deployment-inventory.json and runtime-ab.md.

## Frontend models: bounded source feasibility

Canonical inventory:29 PS2 COMPLETE.PSM and26 PC complete.dx resources.
The strict existing parser supports four selected COMPLETE families;25 have
terminal102 plus12-byte trailer whose consumer contract remains unresolved.
WOOLDAND COMPLETE decodes4261 source faces;978/2271 PC Forester complete faces
match at .001. Source totals are not runtime polygon budgets. Cross CAR/COMPLETE
signature controls match zero, so race model signatures cannot identify menu
models. The partial comparison does not label unmatched faces platform-specific.

One WOOLDAND frontend pilot is feasible after a bounded current menu owner +
COMPLETE VB/IB/draw-set/transform observation. Immediate replacement is NO-GO
until that identity and suppression/lifetime contract are proved. No PS2 model
conversion/export/replacement or original complete.dx write was performed.
See frontend/findings.md for hashes, material partitions and format limits.

## Validation and release

Both independent Win32 Release builds PASS, serial/incremental in canonical
.build/baseline and .build/ps2-enabled, with matching stable .staging roots.
Baseline CTest24/24; PS2 CTest30/30; port unittest118/118; pytest118 with470
subtests. New audit fixtures: vegetation2/2, frontend7/7, body/light4/4.
Compileall, diff-check, exact renderer/patch verification, repeated interface
generators and both proxy export checks PASS. Original source hashes were
verified by read-only audits. No broad unrelated regression repairs.

Baseline DLL SHA-256:
011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138.
PS2-enabled DLL SHA-256:
0013ed2de827c959e6745e73212f4e0e17118dba424287ddfb825a1cf891c848.

The initial build correctly refused an authoring-modified staged wrappers.cpp.
Only that known temporary edit was restored to its approved previous bytes;
the builder then applied the new exact patch from the immutable Git baseline.
No staging ownership check was weakened or arbitrary build folder introduced.
Final build input hashes are in build-report.json; handoff verifies committed
source content and actual compiled byte hashes (including explicit LF/CRLF
conversion). Pre-existing unrelated documentation/INI edits remain untouched.

Next bounded action: user Reset A/B plus manual vegetation resource installation.
Then a dedicated PS2 vehicle material-partition/body pilot, beginning with
WOOLDAND/Forester, offers a safer route to the remaining six reflection gaps.
Physics, HUD, water and other subsystem work do not begin here.
