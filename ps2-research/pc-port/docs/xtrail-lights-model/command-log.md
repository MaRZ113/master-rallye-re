# Actually executed

python ps2-research/pc-port/tools/prepare_xtrail_glass.py (twice, same SHA)
python ps2-research/pc-port/overlay/build_overlay.py (serial --parallel1 both variants)
Native private asset integration: MRR_XTRAIL_GLASS_ASSET points to local ignored
.assets/vehicles/XtrailHeadlight.ps2glass. Build script runs both CTest suites,
proxy verification, interface-generator determinism and Python port regressions.
python -m unittest discover -s ps2-research/pc-port/tests -p test_xtrail_glass.py -v
python -m unittest discover -s ps2-research/pc-port/docs/xtrail-fidelity/wheel-glass -p test_*.py -v
python -m unittest discover -s ps2-research/pc-port/docs/xtrail-fidelity/frontend -p test_*.py -v
python -m compileall -q ps2-research/pc-port/tools ps2-research/pc-port/renderer ps2-research/pc-port/tests
python -m pytest --version (unavailable, no module)
git diff --check
Get-FileHash canonical SLES_509.06

No new broad native reverse analysis; existing byte-verified R5900 and PC owner
contracts reused. Two research subagent attempts ended in model-capacity failures;
no unproduced subagent finding treated as evidence. Raw build logs ignored.
All runtime instructions in runtime-ab.md are pending user steps, not executed.
