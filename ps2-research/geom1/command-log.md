# Executed commands and reproduction recipes

Repository: D:/Game/Master Rallye/master-rallye-re-general on master.
All Git invocations used a per-command safe.directory for the exact checkout;
no global Git setting was changed. Separate SDK Git calls used its own path.

## Actually executed

Preflight recorded git status --short --branch, git branch --show-current and
git rev-parse HEAD for the active repository; SDK HEAD/status were independently
recorded. Source-provenance.json contains those identities.

The local measurement runner data/geom1/run_cases.py loaded each of TURKEY3,
FRANCE1 and ITALY_S1 using geometry_delta.load_pair, compare and write_svg. It
called the original water_runtime.match_geometry on water-filtered faces and
selected ordinary ground anchors separately. Local sensitivity.py repeated the
three profiles on every course. Those scripts contain no new decoder; their full
per-face outputs are private local diagnostics and excluded from the handoff.
The public CLI below is the maintained equivalent comparison entry point.

Each baseline core report was regenerated from fresh original inputs and compared
byte for byte. A separate CLI execution also reproduced the Turkey3 hash:

    python -X utf8 ps2-research/tools/geometry_delta.py --course TURKEY3 --ps2-root "D:/Game/Master Rallye PS2" --pc-root "D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked" --sdk "D:/Game/Master Rallye/master-rallye-re-course" --output ps2-research/data/geom1/TURKEY3-cli.json
    python -X utf8 ps2-research/tools/build_geometry_report.py --directory ps2-research/data/geom1 --output ps2-research/data/geom1/geometry-delta-map.json

The compact inventory was copied to geom1 only after review. Full regression ran
with MASTER_RALLYE_PS2_INPUT, MASTER_RALLYE_PC_INPUT, MASTER_RALLYE_COURSE_SDK and
PS2_UI_CORPUS configured and the pre-existing UI2 XML fixture available:

    python -X utf8 -m unittest discover -s ps2-research/tests -v
    python -X utf8 -m pytest ps2-research/tests -q -p no:cacheprovider
    python -m compileall -q ps2-research/tools ps2-research/tests

Pytest dependencies on this workstation were found through PYTHONPATH pointing
to ignored ps2-research/data/cdelta1/python. The four external variables were
unset for isolation, and the same two suite commands ran from the check directory:

    python -X utf8 ps2-research/tools/package_geometry_handoff.py --check-dir ps2-research/data/geom1/bundle-check

Results and exact skip counts are in validation.md. Postflight called
water_runtime.verify_inputs, rehashed all 11 inspected PC files and checked SDK
HEAD/status and PC renderer/proxy diffs. Raw integrity receipt stays ignored;
compact original-file checks are preserved in source-provenance.json.

Final closeout: git diff --check, git status, explicit scoped git add, staged
diff review/check, commit with the message below and final status. No push:

    git commit -m "research: map PS2 and PC visual geometry deltas"
    python -X utf8 ps2-research/tools/package_geometry_handoff.py --archive ps2-research/data/geom1/PS2-GEOM1-handoff.zip

The committed document cannot recursively contain its own commit SHA. The archive
MANIFEST.json records the actual post-commit HEAD; the outer ZIP_SHA256.json
receipt and final response report that exact commit and archive hash.

## Reproduction recipes, not additional executed captures

The generic three-course CLI/SVG commands in HANDOFF.md reproduce the core source
comparisons. Change --profile and output filename to inspect strict/relaxed
thresholds. Numeric runtimes need not match the original workstation measurement.
The integration suite checks frozen water and ordinary ground anchors directly
against original files. Inspect standalone models through
geometry_delta.dinghy_study with the explicit roots; this does not fit a runtime
pose. No PCSX2 capture, Blender import, new Ghidra query or playable geometry
export command was executed in GEOM1.
