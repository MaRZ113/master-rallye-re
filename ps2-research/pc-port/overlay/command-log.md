> Historical checkpoint: old build paths/hashes below are preserved provenance. For current builds use overlay/README.md and dist/current/build-report.json.

# PC-VISUAL-PILOT1.3 command log

Baseline: `master` at `61cb84d5c7f28d3bd88a3f1f9a8ce16d4c178390`.

Executed from the repository root:

```powershell
python ps2-research/pc-port/overlay/build_overlay.py
ctest --test-dir ps2-research/pc-port/.build-overlay/ps2-enabled/build -C Release -R ps2_port_extension_contracts --output-on-failure
python -m unittest discover -s ps2-research/pc-port/tests -v
python -m compileall -q ps2-research/pc-port/renderer ps2-research/pc-port/tests
git diff --check
```

The overlay script checked exact branch/HEAD/source/patch hashes, staged both
variants from the immutable Git archive, applied patches in fixed order,
regenerated interface outputs twice per variant, and performed independent
serial Win32 Release builds. It ran CTest and proxy-export verification on both
variants and emitted `overlay/build-report.json` with output hashes.

Results: baseline build PASS, CTest 24/24, proxy verification PASS;
PS2-enabled build PASS, CTest 25/25 including
`ps2_port_extension_contracts`, proxy verification PASS; focused CTest 1/1;
Python tests 8/8; compileall PASS; diff-check PASS. The initial rerun before
updating one obsolete source-text assertion failed only that Python assertion;
the assertion was changed to match the masked state transaction contract and
the complete clean staging build then passed.

Full build output remains in the ignored `.build-overlay/logs/` directory.
The DLL hashes and generated-interface digests are recorded in
`build-report.json`. No game files were changed or installed, and nothing was
pushed.
