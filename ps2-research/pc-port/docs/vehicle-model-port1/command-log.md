# Executed command log

Primary cwd: `D:/Game/Master Rallye/master-rallye-re-general`.
Preflight `git status --short --branch`, `git branch --show-current`,
`git rev-parse HEAD`, renderer-tree/status and Course SDK HEAD/status were recorded.
Starting HEAD: a6daf3b17d32043c948e3ed9a843b1a5b3258f16. Existing unrelated dirty
docs/config and revalidation1/PILOT1.4 files remain untouched/uncommitted by this phase.

Actually executed:

```
python ps2-research/pc-port/tools/generate_vehicle_partitions.py
python ps2-research/pc-port/tools/prepare_vehicle_models.py --ps2-root "D:/Game/Master Rallye PS2"
python ps2-research/pc-port/tools/validate_vehicle_model_sources.py
python ps2-research/pc-port/tools/report_vehicle_model_port.py
python ps2-research/pc-port/docs/vehicle-model-port1/frontend-identity/verify_native_bytes.py
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights -p "test_*.py" -v
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-model-port1/frontend-identity -p "test_*.py" -v
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-model-port1/race-partitions -p "test_*.py" -v
python ps2-research/pc-port/overlay/build_overlay.py
python -m pytest ps2-research/pc-port/tests -q
python -m compileall -q ps2-research/pc-port/tools ps2-research/pc-port/tests ps2-research/pc-port/docs/vehicle-model-port1
git diff --check
```

The first private conversion caught case-sensitive host lookup; all requested
texture resources were absent from that dictionary despite existing canonical
names. After using unique canonical uppercase logical keys, all29 source models
resolve all texture slots. The earlier generated private-format artifacts were
updated only after validation of their unchanged source SHA. No game input changed.
The corrected conversion was repeated with the validated source update option;
final `private-model-preparation.json` records only the complete corrected artifacts.

Build environment used existing private assets:

```
MRR_REFLECTION_TEST_GXI=ps2-research/pc-port/.assets/reflection/PS2EnvSource64x64.gxi
MRR_COURSE_OBJECT_TEST_ASSET=ps2-research/pc-port/.assets/course-objects/Turkey3Puddles.ps2obj
MRR_GRASS_TEST_ASSET=ps2-research/pc-port/.assets/grass/Turkey3Grass.ps2grass
MRR_SHRUB_TEST_ASSET=ps2-research/pc-port/.assets/grass/Turkey3Shrubs.ps2grass
MRR_GRASS_MULTI_DIRECTORY=ps2-research/pc-port/.assets/grass
```

The script serially ran both generators twice, configured each canonical variant,
`cmake --build <canonical root> --config Release --parallel 1`, full CTest, proxy
verification,123-port-unittest and compileall, then published to `dist/current/`.
Actual full logs remain ignored `.build/logs`; report is included in this handoff.
The `.analysis/vehicle-model-port1/author_overlay.py` one-shot authoring script
derived exact0001 diff from immutable Git blobs in memory; it did not edit either
the frozen renderer or owned staging sources.0002 was unchanged. No other baseline
patch files were added.

Read-only EER/Rabbitizer source commands and their corrected exploratory failure
are preserved in `ps2-format-lights/command-log.md`. PC REA references/native-byte
checks are in `frontend-identity/native-owner-evidence.json` and
`native-byte-validation.json`. Runtime A/B commands in `runtime-ab.md` are USER
STEPS, not claims that they were executed here. No DLL deployment or push occurred.
