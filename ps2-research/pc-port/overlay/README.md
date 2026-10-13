# Deterministic PS2 overlay — permanent build policy

From the repository root:

```powershell
python ps2-research/pc-port/overlay/build_overlay.py
# Or: powershell -File ps2-research/pc-port/overlay/build.ps1
```

The only persistent CMake configurations are `.build/baseline/` and
`.build/ps2-enabled/`. Verified source copies reuse `.staging/baseline/` and
`.staging/ps2-enabled/`. Final DLLs, build report and SHA256SUMS are published
under `dist/current/`; handoff archives remain under `dist/`. No auto-deployment.

Unset old per-phase MRR_PS2PORT_BUILD_ROOT/MRR_PS2PORT_REPORT_PATH variables.
Noncanonical build roots are rejected. Intermediate build trees are not releases.

The lock pins master, approved immutable source commit
`0bddf7c7bc5e95831f98714ff6231da05ab073ea`, full renderer tree
`e33386bcf682db6983380c499e4928726c758fe0`, original source hashes, exact
patch paths/hashes and deterministic generated-interface hashes. Renderer edits
or source-tree drift fail closed; unrelated research commits are allowed.

Every run validates all ordered patches against fresh immutable `git archive`
bytes in a temporary SOURCE-ONLY directory inside `.staging/`. Verified results
are synchronized into stable stages, preserving unchanged file timestamps.
Unknown/modified persistent staged files are rejected. Only previously owned
verified files no longer present in inputs can be removed. CMake build trees
are NEVER cleaned by this workflow. Temporary validation sources never contain
a third CMake configuration and are released when validation finishes.

The original interface generator runs twice inside staging. Verified identical
outputs regain their original timestamps so unchanged incremental builds do
not recompile everything. An exclusive workflow lock blocks concurrent staging
and builds. Both Win32 Release configurations use --parallel 1, CTest, proxy
verification, focused Python tests and compileall. Only fully validated DLLs
are published under dist/current, with source/patch/Git provenance.

Patch0001 is the existing seven-file extension integration, exactly rebased
onto this approved source. Patch0002 is the staged-only interface generator
correction. The four-file HUD context cache fix is now independently committed
in the immutable baseline and reaches both variants. The former third patch
is archived as historical evidence and is never applied again. The old lock,
patches and exact Git-blob comparison are preserved in
`../docs/build-policy/hud-baseline-adoption/`. Future renderer drift still
requires explicit review; the builder does not adopt new trees automatically.

After verified staging, direct incremental commands are:

```powershell
cmake --build ps2-research/pc-port/.build/baseline --config Release --parallel 1
cmake --build ps2-research/pc-port/.build/ps2-enabled --config Release --parallel 1
ctest --test-dir ps2-research/pc-port/.build/baseline -C Release --output-on-failure
ctest --test-dir ps2-research/pc-port/.build/ps2-enabled -C Release --output-on-failure
python -m unittest discover -s ps2-research/pc-port/tests -v
```

Use the public builder when source inputs change, to reverify and publish.
Optional private corpus test inputs: MRR_GRASS_TEST_ASSET,
MRR_COURSE_OBJECT_TEST_ASSET, MRR_REFLECTION_TEST_GXI. Missing optional inputs
print NOT_PERFORMED and do not become a corpus-verification claim.

Historical reports keep paths of commands actually run then; those are not
future build instructions. Legacy roots are inventoried without deletion by
inventory_build_roots.py. See ../docs/build-policy/. All feature defaults remain
Stock. Original game assets, Course SDK and frozen renderer are never modified
by the public workflow.
