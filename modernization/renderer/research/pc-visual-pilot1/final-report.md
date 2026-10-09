Phase: PC-VISUAL-PILOT1
Repository: D:/Game/Master Rallye/master-rallye-re-general
Branch: master
Starting HEAD: 53b9e28eda597f851265812718a823ffbe9ee96a
Ending HEAD: local diagnostic commit;exact identity in final response and handoff MANIFEST.source_commit
Preflight status: 6pre-existingObservatory paths;renderer trackedclean;preserved/excluded
Selected course: FRANCE1
Selected source group: bush01
PS2 PSM node: 3509209
PS2 material: bush $alphatest() $clamp(uv) $shader(treeblend)
PS2 triangle count: 24visualsourcefaces
PC compiled record: 54/course.batch.1.21/core3261170/base4299/start9792/count144
PC unique triangle count: 24
PC winding duplication: 48records,eachunsignedfaceinbothwindings
Live PC draw identity: TARGET_IDENTITY_AMBIGUOUS
Identity evidence: sourceconfirmed;livecourse/resource/upload UNKNOWN
False-positive tests: 995France1groups/25bush01groups;Turkey3zero targetfaces;livepending
Original PC alpha state: static_alphatestGREATER128 prediction;selectedliveUNKNOWN
PS2 alpha contract: mode2,ATE0,ABE1,(Cs-Cd)*As/128+Cd
Pilot state override: NOT_IMPLEMENTED;identityhardgate
Depth behavior: unchanged;PS2ZMSK1 isresearchcontract
Render ordering: unchanged;PS2queuebucket1notported
Texture source: stockPC
Alpha conversion limitations: PS2As/128versusD3DAs/255;sampledalphaunknown
Feature config: [PS2FoliagePilot]Mode0/1request;Diagnostics0/1
Stock default: Mode0,Diagnostics0
Fallback behavior: effectiveMode0always;invalid/version/buildfailclosed
Native draw count: exactlyoneoriginaldraw in productionmock wrapper
State restoration: zero materialsetters;readonlyresourcecleanup tested;futureoverrideunimplemented
Resource lifecycle: freshdiagnosticreads;creationserialisnotimmutabilityproof
Other renderer features: existingregressionsretained
Build: PASS,MSVCWin32Release
Native tests: 9/9PASS
Renderer regressions: 114 unittest PASS;114 pytest +15 subtests PASS
Proxy verification: PASS,PE32/I386;hashinvalidation.json
Diff-check: PASS
PC runtime: NOT_PERFORMED
PCSX2 capture: NOT_PERFORMED
Visual parity status: PS2_PARITY_NOT_YET_ESTABLISHED
Files changed: renderer source/config/tests/tools/phase docs only
Original game assets changed: NONE
Course SDK changed: NONE;clean4244fa0c
Commit: localdiagnosticcommit;exacthashinfinal/archive
Push: NOT_PERFORMED
Overall status: PC-VISUAL-PILOT1: BLOCKED_ON_DRAW_IDENTITY

# A. Completed work

The existing proxy now has an opt-in F10 probe for native geometry and state, PC source fingerprints, a deterministic auditor, source and synthetic negative controls, and a source/test handoff. No foliage material override is activated. See [implementation](implementation.md), [identity](target-identity.md) and [validation](validation.md).

# B. Source correspondence and the missing live link

Fresh source checks reproduced France1 compiled record54 and the strict24/24 PS2 correspondence. Maximum corner error is0.00002288818359375 at tolerance0.001. The selected faces do not have bit-identical PS2/PC coordinates; native fingerprints use the canonical PC float32 data.

The PC DX SHA256 is `a6bfcef97684f41154596f91fdfaa9522a8fdf6b65d181f4d1ac327b9caf07d5`; TXT is `fbb4153afa20acab9230d33f258384bea1ade94231e4267239b10682f4df0958`. The target multiset fingerprint is `2b60b1f044601052bb5eaeca074615abe3947fdc1b0769c17d300a0b3b3e6f7d`.

25 France1 groups share the texture, but none of the994 other compiled groups contains the target faces. Turkey3's939 draw groups also contain none. These are source checks. The60 historical game captures have10077 indexed calls, including81 calls with48 triangles, but lack course and content ownership. France1 coverage is uncertain. No call is promoted to compiled record54.

Missing live links are the API partition, course/resource owner, transform and upload revisions, and negative controls. See [source metadata](source-signatures.json) and [historical audit](historical-trace-audit.json).

# C. Original PC versus PS2

PS2 treeblend mode2 selects alpha blending, disables alpha testing and masks depth writes. PC flags predict the tree/_alphatest cutout variant; the selected native PC state is UNKNOWN. Conventional D3D8 SRCALPHA/INVSRCALPHA would approximate the PS2 GSAs/128 equation. No alpha amplification, forced GEQUAL or queue sorting is implemented. See [the separate contracts](original-vs-pilot-state.md).

# D. Native policy and Stock compatibility

Requested Mode1 reports `blocked_on_draw_identity` and stays effectively Mode0. Diagnostics are separately opt-in and run only during F10 on the supported build. Native getters do not change logical/effective shadows. The original draw runs once and returns its original HRESULT. Readable-buffer locks are bounded and cleaned up; unlock failure disables the probe and remains visible. See [safety](state-restoration.md).

# E. Texture and ordering

The game retains its stock texture. No replacement, replay, second pass, transparent queue or sorting is added. PS2's 64x64 image with 89 stored alpha levels and PC's 128x128 image with 15 levels remain a separate source difference. See [texture status](texture-status.md).

# F. Tests and reproducibility

The baseline passed8 native suites and100 Python tests under normal permissions. The final checkpoint passed9 native suites and114 Python tests, proxy verification, compileall, diff-check and11 renderer-recon tests. Restricted baseline temp-cleanup errors and development failures remain in ignored logs. The production F10 serializer test uses a synthetic backend and supplies no game-runtime evidence. Repeated source JSON is identical. Pytest passed 114 tests and 15 subtests. The extracted source-only handoff independently built all 9 native suites, passed all 114 Python tests and proxy verification without game data. Details are in [validation.json](validation.json).

# G. Required in-game capture

First obtain a diagnostic France1 F10 capture. This build cannot perform a visual Mode1 A/B comparison. The DLL was not installed into the game. Follow [runtime-test-plan.md](runtime-test-plan.md). A content match still needs course/upload ownership and live negative controls before a five-state RAII override can be authorized by the identity gate. PC and PCSX2 visual acceptance remain pending.

# H. Limits and one follow-up

See [known limits](known-limitations.md) for unsupported buffers/API paths, budgets, transformed or split geometry, mutable identity and ordering. Recommend exactly one follow-up: **PC-VISUAL-PILOT1-DRAW-CAPTURE**, described in [next.md](next.md). No other course, material or PS2 feature is started.

## Code-only follow-up recorded 2026-10-09

The new [CPU upload provenance report](cpu-upload-provenance.md) documents bounded vertex/index-buffer Lock/Unlock mirrors and resource-generation/callsite tracking. The supplied two F10 audits remain unchanged and still contain no content evidence. The follow-up is statically tested, but its use in the game is pending; the overall draw identity remains blocked and Mode 1 remains effectively Stock.
