# X-Trail focused handoff

Race: decal pilot implemented, user runtime pending. Frontend: source preparation
only, replacement blocked on current owner/cache/geometry join. Wheels/headlights:
source contracts proved, unchanged in this DLL. Read final-report.md and
runtime-ab.md. Merge PS2Port.ini controls into your working config; do not discard
existing asset paths. Defaults off. Manual DLL installation only; no push.

Archive includes clean committed source/tools/tests/compact evidence, exact staged
patches/renderer lock, both independently built proxy DLLs, SHA256SUMS and build
report. No original textures/models/log dumps/screenshots. Rebuild requires original
repository pinnedrendererGitobjects0bddf7c7bc5e95831f98714ff6231da05ab073ea,
Win32MSVC/CMake/SDK. Execute python ps2-research/pc-port/overlay/build_overlay.py;
it reuses .build/baseline,.build/ps2-enabled and .staging with --parallel1.

Corpus-independent extracted tests cover test_xtrail_fidelity.py and the6wheel/glass
and4frontend checks; private game inputs not needed. Regenerating original source
joins requires canonical PS2PackFS, protected PCvehicleDX corpus and read-only
CourseSDK. No Blender required. Full runtime recipe is in runtime-ab.md.

Commands actually executed: existing strict source audits, audit_xtrail_runtime.py,
generate_xtrail_decal.py, both serial builds/CTest/exports/generators,126portPython,
6+4source tests, compileall and git diff --check. The user A/B recipe has not been
executed for this new DLL. No visual parity or successful new override is claimed.
