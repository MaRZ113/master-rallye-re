# Executed commands

python ps2-research/pc-port/tools/prepare_lamp_partition.py
python ps2-research/pc-port/tools/prepare_brake_glow_identity.py
python ps2-research/pc-port/docs/xtrail-brake-followup/runtime-pair/audit.py
python -m unittest discover -s ps2-research/pc-port/docs/xtrail-brake-followup/brake-contract -p test_*.py -v
python -m unittest discover -s ps2-research/pc-port/docs/xtrail-brake-followup/runtime-pair -p test_*.py -v
python -m unittest discover -s ps2-research/pc-port/tests -p test_lamp_followup.py -v
python ps2-research/pc-port/overlay/build_overlay.py
python -m compileall -q ps2-research/pc-port/tools ps2-research/pc-port/tests ps2-research/pc-port/docs/xtrail-brake-followup
git diff --check

Bothbuildcommands/generatedinterfaces/exports/fullportPython invokedby strict
serialoverlaybuildscript, existingcanonicalroots only. OriginalR5900/PC bounded
probe commandsin brake-contract/command-log.md. Raw outputs ignored. F10pair
providedbyuser; no memorymutation orautomatedgameinteraction. Proposedruntime
recipe inruntime-ab.md remains pendingnewDLL. Baseline/PS2 sourceassets unchanged.
