# R5T-F.1 reciprocal tag100 swap — completed runtime handoff

**Status: COMPLETED.** The user ran both hybrids. The visible finish geometry
stayed at its original location in both. Hybrid A (baseline prefix + modified
tag100) had no collision at the old support and collision at the new translated
position. Hybrid B (modified prefix + baseline tag100) had the old collision
and no collision at the new position. `RACE COMPLETE` remained at the original
unchanged FinishArea in both runs. The tested physical state therefore followed
the selected suffix donor beginning at the tag100 marker. F.2 later established
that the swapped suffix also contains a tag1339 record and a tag1400 region;
the runtime test did not isolate the parsed tag100 tree from that later region.
The original instructions below are retained as the handoff record; they are
no longer pending actions.

## Test setup

Two isolated Demo 9.10.0 runtime clones are ready. Both were copied from the same baseline-03 runtime template, so the baseline France1 GXM, TXT, DXT files, RaceTest XML, executable, and all other non-DX files are byte-identical between them. Only `DataGx/Course/France1/france1.dx` differs. The baseline GXM is intentionally held constant in Hybrid B even though its render prefix came from modified-03. Do not launch the original R5T-F.0 runtime folders or Retail install for this comparison. Do not delete DX/DXT caches or select a recook operation.

Close each game completely before starting the other clone. Select France1 in each runtime and use the same car/opponents and comparable driving approach. The hybrids are already in place; no file copy or manual swap is required.

## Hybrid A — baseline prefix + modified tag100

Launch this isolated executable:

```powershell
$exe = 'D:\Game\Master Rallye\master-rallye-re\research-output\r5t_f1\runtime\hybrid-a\runtime\MRallye.exe'
Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe)
```

Record the observations before assigning an interpretation:

1. Does France1 load normally?
2. Does the visible finish banner and right support render normally at the old location?
3. At the OLD physical location, approximately `(-1471.7653, 68.4258, 352.5542)`, is collision present, absent, or unclear?
4. At the NEW location, approximately `(-1451.7653, 68.4258, 352.5542)`, is collision present, absent, or unclear? This location is expected to be empty/non-rendered; the source edit moved X only, so its height may not match the local road.
5. Does `RACE COMPLETE` still trigger in the ordinary original FinishArea?
6. Any rendering, loading, or physics instability?

## Hybrid B — modified prefix + baseline tag100

After fully closing Hybrid A, launch:

```powershell
$exe = 'D:\Game\Master Rallye\master-rallye-re\research-output\r5t_f1\runtime\hybrid-b\runtime\MRallye.exe'
Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe)
```

Record the same six observations at the same locations and FinishArea.

## Interpretation after recording both runs

- If A has collision at NEW and B at OLD, the tested physical state follows the selected tag100-starting suffix donor for these compatible rev135 prefixes. F.2 later showed that the suffix extends through tag1339 and tag1400; this test did not isolate the parsed tree alone.
- If A has collision at OLD and B at NEW, the tested state follows the prefix donor instead.
- If either build fails or the result is neither donor state, report the exact behavior without assigning sufficiency; region coupling may remain.
- If A and B show the same state, stop and verify which executable/course was loaded, that the two runtime folders were distinct, and that no stale files replaced the hybrid DX.

Do not infer from this test that all tag100 content is collision data, that tag100 is a BSP, or that its grammar is decoded. After the game tests, close both runtimes and report the six observations for each hybrid. No further tag100 analysis or course phase should begin before review.

## Identity checks

The manifest is [`swap-manifest.json`](swap-manifest.json). It records the installed course DX hashes and region provenance. After the runtime test, the repository-side check can be rerun:

```powershell
python tools\r5t_f1_tag100_swap.py verify
```

If it fails because a runtime rewrote either DX, preserve the changed file and report its hash; do not silently rebuild or restore the hybrid before review.
