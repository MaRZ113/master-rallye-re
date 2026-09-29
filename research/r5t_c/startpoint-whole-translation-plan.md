# France1 whole-startpoint translation candidate

Status: **staged; cooker and runtime results pending**.

## Question

Does translating the eight-point France1 startpoint candidate as one rigid
volume produce a repeatable compiled tag100 change and an observable race/start
behavior change?

The candidate is deliberately limited to +3.0 source X units. It preserves the
10-unit box and retains substantial overlap with its original location. The
first-eight-point association with the literal `startpoint` node is still a
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

The current result is `PASS_STAGED`. It does not mean the course has been
cooked or runtime-tested.

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

The variance-aware report is expected at
`.research-output/r5t_b1/experiments/france1-startpoint-whole-x3/variance-aware-report.md`.
It will compare render geometry, tag100, and captured non-DX course resources.
No compiled effect is asserted before that report exists and validates.

## Runtime observations

Use the first baseline and first modified run to enter the same France1 race
state. Observe and record:

1. player initial position and heading;
2. AI starting positions and formation;
3. countdown and whether the race begins normally;
4. start-line or trigger behavior that is directly visible.

The per-experiment `RUNTIME_TEST_INSTRUCTIONS.txt` contains the same protocol.
The extra second run per cohort verifies cooker repeatability; gameplay need
not be repeated unless the first observation is inconsistent or ambiguous.

Keep the baseline and modified runs on this matching Demo 9.10 build. Record
what happens, including an unchanged result; do not infer spawn, trigger,
collision or start semantics from a successful course load alone. The course
box and RaceTest Marker 0 are close in the measured source/DX frame, but their
relationship remains spatial correlation rather than a parsed reference.
