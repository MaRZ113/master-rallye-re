# PS2-REFL1 standalone handoff

Start with ps2-research/refl1/final-report.md and validation.md. Research only;
this contains no PC effect, extracted mesh, texture, original binary or emulator dump.
MANIFEST.json records the source commit and SHA256/size of every payload. The
external ZIP_SHA256.json receipt also covers the archive and manifest itself.

Python3.10+ is required; existing visual utilities additionally use Pillow.
pytest is optional. Ghidra12.1.4/ghidra-bridge are needed only for fresh ELF queries,
not the Python evaluator/tests.

```powershell
python -m unittest discover -s ps2-research/tests -v
python -m pytest ps2-research/tests -q -p no:cacheprovider
python -m compileall ps2-research/tools ps2-research/tests
```

For a genuine bundle-only test, leave proprietary input variables unset. External
class/per-test SKIP is expected and explicitly reported, not a runtime PASS.
Windows hard-link/symlink protections require host permissions; sandbox denial
must not be “fixed” by weakening these tests.

For full integration supply externally:

| Variable | Corpus |
|---|---|
|MASTER_RALLYE_PS2_INPUT|D:/Game/Master Rallye PS2; canonical SLES_509.06,CNF,PAK,000|
|MASTER_RALLYE_PC_INPUT|D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked|
|MASTER_RALLYE_COURSE_SDK|Read-only D:/Game/Master Rallye/master-rallye-re-course|
|PS2_UI_CORPUS|External ignored original HUD extraction|

Historical UI2 original ITALYS1.XML is an optional ignored local dependency and
is not bundled. All four small UI2 JSON fixtures and the required WATER1 compact
contract/function metadata are included. REFL1's own resource/vehicle evidence,
original instruction probes, synthetic matrix input, tools and focused tests
are self-contained. See command-log.md for exact fresh commands and result scopes.

Full current suite:196 unittest PASS,196 pytest plus259 subtests PASS,0skip.
Isolated bundle: unittest184run,16skip; pytest171 PASS plus160 subtests PASS,25skip.
The skip counts differ because unittest reports unavailable integration classes
as class skips, while pytest collects their individual methods. See validation.md
and the local package-checks receipt. Source inputs and complete geometry remain private.
