# France1 whole-startpoint translation closeout

Status: **2+2 cook PASS; source-to-tag100 effect CONFIRMED; direct grid anchor NOT SUPPORTED**.

> This older plan's proposed Retail `StartArea` movement test is superseded:
> R5T-D.0 has since confirmed that StartArea controls grid translation,
> orientation, spacing, and heading. The optional GXM non-overlap test would
> address only the remaining containment/helper possibility, not grid placement.
> See `research/r5t_d0/findings.md`.

## Question

Does translating the eight-point France1 candidate as one rigid volume produce
a repeatable tag100 change or an observable race/start behavior change?

The experiment translated the candidate by +3.0 source X units. It preserved
the 10-unit box but retained substantial overlap with its original location.
The first-eight-point association with the literal `startpoint` node remains a
`HIGH_CONFIDENCE_INFERENCE`; no runtime meaning is assumed.

## Source edit

The original input is `inputs/8.4.1_France1/France1.gxm` with its paired TXT.
The staging tool copied the source to ignored
`.research-output/r5t_b1/experiments/france1-startpoint-whole-x3/modified-source/`
and changed only the X float of each of the eight box points by +3.0. The source
patch manifest records all eight float preimages, byte offsets, output values,
pool hashes, and the unchanged box dimensions. Twelve byte positions differ in
the GXM; no other source file differs. The original input is untouched.

The original Demo 9.10 runtime corpus was copied into separate ignored
`baseline/runtime/` and `modified/runtime/` directories. Both have the same
runtime executable SHA-256, the same France1 RaceTest XML SHA-256, two
independent runs staged, and no France1 DX/DXT cache before the first cook. The
modified runtime differs only in the staged source GXM. Run the read-only
staging validator from the repository root:

```powershell
python tools\r5t_b1_course_cook.py validate --experiment france1-startpoint-whole-x3
```

The saved pre-cook result is `PASS_STAGED`. The experiment is now cooked and
runtime-tested; see [`whole-x3-closeout.md`](whole-x3-closeout.md) and
[`whole-x3-closeout.json`](whole-x3-closeout.json) for the verified results.

## Cook protocol

The exact launch, snapshot, and reset commands are in:

- `.research-output/r5t_b1/experiments/france1-startpoint-whole-x3/baseline/TEST_INSTRUCTIONS.txt`
- `.research-output/r5t_b1/experiments/france1-startpoint-whole-x3/modified/TEST_INSTRUCTIONS.txt`

Each file names `baseline-01`, `baseline-02` or `modified-01`, `modified-02`.
For every run, launch the staged `MRallye.exe` with its staged runtime directory
as the working directory, select France1, wait for a successful load, snapshot
the output, fully exit, and reset that cohort's generated DX/DXT before its
next independent run. Do not use the original runtime or course directories.

After all four snapshots, run:

```powershell
python tools\r5t_b1_course_cook.py compare --experiment france1-startpoint-whole-x3 --minimum-runs 2
```

The variance-aware report is at
`.research-output/r5t_b1/experiments/france1-startpoint-whole-x3/variance-aware-report.md`.
The compare command completed with two baseline and two modified runs. It
isolates a deterministic 263-byte tag100 change from naturally variable render
prefixes. The generated DX/DXT caches are now present, so the pre-cook staging
validator should not be rerun without resetting a clone.

## Runtime observations

The owner reports that the course loaded and ran normally. Within the Demo
9.10 baseline/modified comparison there was no observed change in player
position/orientation, AI positions/order, countdown, or race start. No obvious
delayed trigger or physical boundary appeared during roughly half a lap. The
+3 boxes still overlap, so a containment or other spatial-helper role remains
possible.

New cross-runtime controls show the player at the front in 8.4.1, second in
9.3.1, and in the normal Retail order in Retail. Both completed outputs derived
from the old 8.4.1 source also produced the normal Retail order when copied
into Retail. Therefore the earlier old-grid observation is not evidence that
participant order is authored by France1 source. Runtime/version-dependent
participant-to-slot assignment is a strong inference; the physical slot
positions or start-region source remain unknown.

The next controlled source probe is a Retail XML-only change in a fixed Retail
runtime. Translate all four Retail France1 `MarkerLists/StartArea` positions by
+3.0 in X while holding the course output, runtime, and opponents fixed. Record
car positions/order separately from green marker visuals. If this does not
clarify physical slots, the GXM +12 non-overlap test remains available for the
separate containment question. Exact Retail marker values and cohort evidence
are in [`whole-x3-closeout.md`](whole-x3-closeout.md).
