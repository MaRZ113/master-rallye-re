# Offline diagnostic and validation

`tools/spline_runtime.py` accepts a canonical input directory, exact course
and Egg name, occurrence, step count, explicit observer positions or absence,
and explicit pre-init bank flag 0. It does not accept a guessed incompatible
ELF/corpus or save route coordinates outside ignored `ps2-research/data`.
`tools/build_ambient1_report.py` regenerates the six bounded cases and compact
24-record applicability metadata, reusing CDELTA1's selection and payload SHA.
Neither tool contains another PackFS decoder.

```powershell
python ps2-research/tools/build_ambient1_report.py --input 'D:\Game\Master Rallye PS2'
python ps2-research/tools/spline_runtime.py --input 'D:\Game\Master Rallye PS2' --course ITALY3 --egg barge --steps 360 --observer-absent --initial-bank-flag 0 --output ps2-research/data/ambient1/manual/ITALY3-absent.json
```

For movement provide `--observer X Y Z`, or `--observer-json` containing one
XYZ array/null per invocation. `--initial-time` and `--initial-active` permit
explicit controlled state choices; they do not restore unknown previous pose,
cache and banking history from a savestate. That would require a fuller state
capture. With ordinary initialization, time 0, constructor ring 0 and sample
history zeros are proved; the supplied first bank flag is the stated assumption.

Per-row JSON includes source/provenance, preserved ordered properties/markers,
nominal path times, active status, missing-observer status, XZ distance²,
evaluated/next time, rest counter, ring index, bank mean, XYZ, forward/up and
all world rows. Original authoring and synthetic observer data stay ignored.
`--svg` draws a diagnostic X/Z overlay; the builder's full-domain sweep is
clearly separate from its 360-invocation controller timeline.

Independent constraints:

- Execute original ELF basis words in `1a9c9c..1a9d1c`: 24 input/index probes
  match host float32 bits. Unknown ELF SHA rejects before execution.
- Decode original factory/vtable and effective model-store addresses: owner
  allocation 0x130, real update/init slots and sixteen en3d world words.
- Independently evaluate rational Catmull–Rom polynomials and collinear interior
  positions; check knot interpolation and open/closed endpoints.
- Verify constant/open closing hold, nonconstant equal knots, strict trigger
  equality/hysteresis, missing observer, resume, rest/reset/loop precedence,
  publication-before-advance and independent owner/history state.
- Verify order/duplicates/types/provenance, nonfinite/degenerate rejection,
  floating-point tolerances and deterministic regeneration.

The tool reproduces the **supported finite controller contract**, not every
unsafe malformed-input branch, a dormant unserialized acceleration mode, or
the whole R5900/libm. Host sqrt/sin/cos and rounded IEEE float32 are explicit
platform approximations. Tests do not assert PS2 trajectory bit identity or
turn synthetic movement into a recorded runtime trajectory.

No trustworthy synchronized temporal capture was available for this phase.
The six existing user screenshots are individual JPGs without a controlled
owner/transform/tick trace. They are not a motion oracle. Runtime validation
is **NOT_PERFORMED**; see the concrete single next phase in `next.md`.
