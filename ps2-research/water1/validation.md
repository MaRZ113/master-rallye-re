# WATER1 validation and acceptance

**PS2-WATER1 STATUS: COMPLETE — bounded static content/material/render contract.**
Runtime visual validation: **NOT_PERFORMED**. A closed static phase is not a
claim of independently measured PS2 visual parity.

| Check | Result | Evidence/limit |
|---|---|---|
| Primary repository/branch |PASS|master-rallye-re-general,master; starting clean HEAD309fdfd34becdfca3603e626509a697fcaec2ab6|
| Canonical ELF/CNF/PAK/000 |PASS|Fresh size/SHA verification; exact values in case-evidence.json; repeated by original-corpus tests|
| Five selected named PSM extractions |PASS|Existing PackFS, stored and decoded hashes; original inputs read-only|
| Material and visual-tree binding |PASS|Original bytes plus391d38/391690; separate spatial decoder agrees with boundary|
| France/Italy correspondence |PASS|3586/3586 and1329/1329 all-PC face matches; independent SDK draw coverage|
| Turkey3 PC baseline |PASS|939draws/54589vertices/42237triangles and original DX hash reproduced|
| Turkey3 additional source surfaces |PASS|745faces,0 corner matches; independent centroid projection0 coplanar within.001|
| Function/state word probes |PASS|69 function contracts, original ELF words; direct JAL/vtable data flow|
| Full unittest |PASS|176 tests,0 failures,0 skips with declared external corpora|
| Full pytest |PASS|176 passed and184 subtests passed;0 skips|
| Isolated handoff tests |PASS with declared external SKIP|Bundle-only unittest167reported runs/15skips;pytest154PASS/22skips/153subtests; no missing UI2 JSON failure|
| compileall |PASS|All PS2 tools/tests|
| diff-check |PASS|Final staged and working-tree checks required at closeout|
| Original source / PC SDK hygiene |PASS|Canonical hashes and selected PC hashes stable; SDK HEAD/status unchanged; no PC renderer edits|
| Live PCSX2 correlation |SKIP / NOT_PERFORMED|No trusted running session; no unrelated screenshot promoted to runtime proof|
| Actual VU residency and inherited GS state |BLOCKED evidence boundary|No independent micro-RAM/GS capture; CPU upload address and DMA start are proved|

Tests run with MASTER_RALLYE_PS2_INPUT, MASTER_RALLYE_PC_INPUT,
MASTER_RALLYE_COURSE_SDK and PS2_UI_CORPUS pointing to the validated local roots.
Pytest was loaded from existing ignored data/cdelta1/python. TEMP/TMP remained
in ignored water1 scratch. The test process used host execution because the
existing input-protection hard-link test is not supported by the restricted
Windows sandbox; no tests were weakened or environment errors counted as PASS.

```powershell
$env:MASTER_RALLYE_PS2_INPUT='D:/Game/Master Rallye PS2'
$env:MASTER_RALLYE_PC_INPUT='D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked'
$env:MASTER_RALLYE_COURSE_SDK='D:/Game/Master Rallye/master-rallye-re-course'
$env:PS2_UI_CORPUS='D:/Game/Master Rallye/master-rallye-re-general/ps2-research/data/ui1/extracted/TNG/DATAPSM/HUD'
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/tests -q -p no:cacheprovider
python -m compileall ps2-research/tools ps2-research/tests
git diff --check
```

| Acceptance gate | Status | Proof boundary |
|---|---|---|
|1 Repository discipline|PASS|Correct clean master start; scoped changes and no branch/worktree/push|
|2 Corpus provenance|PASS|All four canonical identities checked|
|3 Water/puddle parser|PASS|390d98/391690/3a6c58 direct string-to-handler chain|
|4 Shader classification|PASS|9puddle,10water,19waterfall/waterall; generic fallback preserved|
|5 Geometry ownership|PASS|Node2 material belongs to authored strip/vertex owner|
|6 Visual render binding|PASS|Mesh/cache/queue producer fields and virtual draw dispatch proved; live visibility separate|
|7 Turkey3 delta|PASS|Extra visual source surfaces within compared compiled landscape; not just metadata|
|8 PC cross-check|PASS|Baseline and all-draw geometric tests reproduced|
|9 Positive controls|PASS|France/Italy independent complete source face correspondence|
|10 Negative/spelling controls|PASS|Turkey1 local negative; both waterfall and waterall recognized|
|11 Texture dependencies|PASS|Two named resources ->mesh handles ->binders; live texture visibility not claimed|
|12 Alpha/depth state|PARTIAL|Blend/ATE/TCC/ZMSK explicit; inherited ZTE/DATE/FRAME/TEXA and actual packet state not captured|
|13 UV/animation|PASS|Recovered actual callbacks and bounded waterfall evaluator; counter units/FCSR remain explicit unknowns|
|14 Render submission|PASS|Source ->CPU records ->mode/texture/state ->frame chain ->VIF1 DMA start; executed VU output conditional|
|15 Reflection boundary|PARTIAL|Static textures and normal UV operations proved; global basis/dynamic reflection ownership UNKNOWN|
|16 Offline evidence|PASS|Deterministic visual/material/matcher/state diagnostics and synthetic-only UV example|
|17 Portability|PASS|Turkey content requirements separated from shared-surface renderer requirements|
|18 Tests/hygiene|PASS|Full configured regression,compileall,diff-check,hashes and reproducibility|
|19 Scope discipline|PASS|No port,SDK modification,water physics,weather,REFL1 or other phase begun|

## Future runtime capture

Use an unpatched canonical ELF and a trusted PCSX2 debugger/GS capture. Record
PCSX2 build/configuration, disc/ELF hashes, exact Turkey3 scene and frame/view.
All RAM, micro-RAM, packets and screenshots must remain ignored.

1. On `3aea50`, record the mesh pointer, material/source identity, mode+28,
   primary/secondary names+34/+38 and strips+74. Correlate to one identified
   source group rather than any nearby water-looking polygon.
2. At `3714e0`/`3bca80`, capture both handles+dc/+e4 and the scene instance
   matrix/cache entry. Confirm the selected LOD and actual source strip range.
3. At `31d7c8`, capture a bounded64-byte vertex stream and its count. Record
   `320c78` UV output for two explicit counters; confirm XYZ stability.
4. At `31cd98`/`31c438`, capture42dec0/42df70 and final TEX0/ALPHA/TEST/ZBUF
   values after texture binding and inherited initialization.
5. Correlate `317208`'s upload stream with VU1 micro-RAM entries00f/36a/37c/377
   and the original MPG hashes. Observe `30ea80` TADR/CHCR and the corresponding
   GIF/GS batch. Do not infer residency from a compatible program alone.
6. Match that batch to the visible puddle in the captured frame. A second frame
   separates UV animation from camera movement or different source groups.

A synthetic footprint or waterfall UV result never becomes CONFIRMED_BY_RUNTIME.
Broader emulator automation and other graphics systems are outside this phase.
