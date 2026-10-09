# Executed commands versus pending runtime

Executed in master-rallye-re-general/master:

* Git preflight/status/HEAD/log8 and separate read-only Course SDK HEAD/status.
* Existing tools/build.py baseline:8 native suites PASS;initial sandbox MSBuild wait interrupted,normal reviewed execution completed.
* Baseline Python unittest100:initial restrictedTemp run5WinError5;reviewed rerun100PASS.
* Baseline and final verify_proxy.py:PE32/I386,exports/imports valid.
* New source mode:canonical PCFrance1/Turkey3 and canonicalPS2 input verification,strict PS2-to-PC surface check,new content hashes;repeated output compared.
* Native build/tests after additions:9 suites PASS. Development compile failures retained in ignored logs:FrameBuffer size gate,string moved to bounded external map;DWORD/UINT getter mismatch;missing algorithm include in test. The first PS2 bit-exact check correctly rejected unequal coordinates;replaced with the established independently bounded0.001 correspondence,not an enlarged tolerance.
* Production native F10 serializer:synthetic mock backend,not game runtime.
* Full renderer unittest/pytest,renderer-recon11tests,compileall,diff-check,source and reference integrity checks.
* package_foliage_pilot.py: source/test ZIP, CRC and every payload SHA check. The initial unbuilt isolated run reported native prerequisites and a missing general Python package/scratch directory. The corrected archive was extracted into a second ignored directory; tools/build.py passed 9/9 native suites, verify_proxy.py passed, and unittest discover passed 114/114 with no proprietary corpus. Final archive regeneration follows the local diagnostic commit.

Code-only CPU upload provenance continuation on 2026-10-09:

* Read `!backup/handoff/SUMMARY.md` and both supplied capture audits. Each audit was complete with 128/128 probes blocked on WRITEONLY managed buffers, zero content reads and no override.
* Implemented bounded CPU Lock/Unlock mirrors, resource creation caller metadata, generation/revision matching, raw escape/reset/ProcessVertices invalidation, and fail-closed wrapper registration. Updated `generate_interfaces.py` so the custom buffer forwarders remain deterministic.
* `python modernization/renderer/tools/build.py`: PASS; 9/9 native CTest contracts.
* `python -m unittest discover -s modernization/renderer/tests -v`: PASS; 114 tests, 0 failures/errors/skips, with `TEMP`/`TMP` directed to ignored `renderer/.analysis/python-temp` after the sandbox denied writes to system temp.
* `python -m pytest modernization/renderer/tests -q`: NOT AVAILABLE; the active Python installation reports `No module named pytest`. No package installation was attempted.
* `python -m compileall modernization/renderer/tools modernization/renderer/tests`: PASS. `verify_proxy.py`: PASS; current PE32/I386 proxy SHA256 `2726e51fd5dc3d1caa82a17ce6ecb021ea985a6c1b0bcf2f8786597a3c81a3db`.
* No new game capture, game launch, DLL deployment, PS2 capture, asset write, Course SDK write or push. All supplied old capture audit conclusions remain unchanged.

No game/emulator launch,DLL deployment,asset or EXE patch,Course SDK write,global transparency sorting,texture conversion,material override or push. Runtime capture/A-B instructions are pending human operations,not executed commands. Raw local build/test logs live under renderer/.analysis and are not packaged.
