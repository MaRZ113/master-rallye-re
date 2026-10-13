# Full coverage — manual game A/B

Use the PS2-enabled DLL from `dist/current/ps2-enabled/`. No deployment was performed.
Preserve the currently installed DLL and INIs before manually replacing anything.
Keep the existing MRRRenderer.ini, Free Camera bookmarks and game settings.

Copy `PS2Port.ini` from this directory beside MRRRenderer.ini. Supply the original
local `PS2EnvSource64x64.gxi` and `Turkey3Puddles.ps2obj` as before. Copy all 72
files from the ignored `pc-port/.assets/grass/` directory into the configured
`PS2Grass/` directory beside the INI. These contain private original-content
derivatives and are intentionally omitted from the handoff. Exact names and
SHA-256 values are in `courses/coverage-registry.json`.

## Reflections

1. Start with Tata/Kia to check the accepted fallback. Then test a new family,
   preferably Jump or Terrano, whose genuine body regions use chrome/perspex.
2. Same car, course, lighting and camera bookmark: compare ReflectionMode=0
   against4. Use ReflectionCoverage=1; Coverage=0 intentionally retains the
   historical Tata record19-only pilot.
3. Compare ReflectionTargetPrecision=0 and1 separately. Do not change camera,
   texture, filtering and reflection settings at the same time.
4. In the existing renderer AA settings, test effective NONE,2x and4x separately.
   The port never changes AA configuration. Restart to change device settings.
5. For one diagnostic run set ReflectionDiagnostics=1. Confirm the correct vehicle,
   geometry SHA, override_applied=true, applied_mask=3, successful native draw
   and restore HRESULTs, capture_source_multisample=0/2/4, and target_format21/25.
   precision_fallback=true means16-bit allocation fell back explicitly to32-bit.
6. Unsupported count, padded copy dimensions or driver copy failure means Stock
   reflection, with the exact capture_reason/HRESULT. Do not interpret it as AA
   being disabled. Forester/Forklift remain excluded for documented source gates.

Diagnostic identity/application messages are capped per vehicle; full native
state failures remain reported. Mode4 still captures once per frame before the
first accepted body, not a PS2-timing or pixel-parity claim.

## Courses and performance

Compare GrassMode=0/ShrubsMode=0 with2/2 on the same camera bookmark. Mode1
remains Turkey3-only. Mode2 admits all 36 exact course certificates but only the
verified .001-matching eligible source faces. Do not copy one course's positions
into another resource file. Missing/corrupt/wrong-course files fail closed.

First check Turkey3, France1 and ItalyS1 for regressions. Then sample FranceWFlip
(largest category), ItalyM2, Spain and Greece stages, and complete the 36-row
coverage checklist as time permits. Exact certificates/filenames are in the table.
Check restart, exit to menu, switch to another course, and HUD hide/show. Record
menu/race FPS before and after, using the same AA/settings. A native resource
test is not a game FPS measurement.

Loading all 72 assets is one opt-in startup operation (about108.5MiB of derived
files), then memory-cached. There are no per-frame file reads or full-course
placement scans. Expect a bounded initial load; report any continuing menu
stutter or growth across restarts. Grass/shrub diagnostics can be enabled for a
single run; logs show source course, category, hash, draw and restore HRESULT.

FoliageMode=0 and PixelProbe=0 remain the recommended settings. Physics and HUD
replacement stay paused. No PS2 pixel-level parity or new-car runtime result is
claimed from the standalone driver test.
