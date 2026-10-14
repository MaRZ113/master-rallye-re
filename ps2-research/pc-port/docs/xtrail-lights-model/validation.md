# Executed validation

Current master start1aa6762eaa7cb8c6875699e9e96d45360999074f; unrelated pre-existing
document changes excluded from this commit and clean archive. Frozen renderer
worktree diff empty; tree e33386bcf682db6983380c499e4928726c758fe0; staged immutable
objects0bddf7c7bc5e95831f98714ff6231da05ab073ea. Course SDK unchanged/clean at
4244fa0c4d878523c9947f54816bf377cdfb2589, read-only.

Both Win32 Release builds --parallel1 PASS; baseline24/24 CTest and PS2-enabled
33/33 CTest PASS; proxy exports PASS both; exact patch application and repeat
interface generator PASS. Final port Python suite130/130 PASS; independent
wheel/glass6/6, frontend4/4 PASS. Compileall and diff-check PASS. Pytest NOT
AVAILABLE (C:/Python315: No module named pytest); no installation attempted.

Glass native mocks: Stock/version/build fail-closed; two original-source material
passes; original S_FALSE result;15 first-pass and17 second-pass setter failure
positions; every modified scalar, texture/matrix and UP stream/index state
restored; failed restoration retained/repaired; read failures produce zero
writes; texture/VB/IB reference balance; real Reset vs echo/failure. Synthetic
22vertex/18face positive attribute mapping and negative geometry/normal/UV/color/
resource-generation/build/index checks. Managed texture creation/upload, cached reuse, release/recreation after Reset and
creation failure fail-closed were also tested. Private6920-byte asset decode integration
executed via MRR_XTRAIL_GLASS_ASSET, corrupt SHA rejected. Actual driver runtime,
visual parity, window Reset and MSAA with the new glass feature NOT_PERFORMED.
Existing baseline Reset/MSAA tests pass; these do not establish new live behavior.

prepare_xtrail_glass.py rerun: identical asset SHA4a7dce3c248cfbf621c8565f85c15058d4eddcb3f7daa498a2070aa7f48fe91e;
original PackFS sources and protected PC DX reverified by tool. Canonical ELF
SHA b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2 confirmed.
No original executable/assets, renderer, SDK, physics, HUD or course edits.

Final baseline DLL SHA011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138.
PS2 DLL SHA d0059a788bb270fa54f2091e00052149b74565452b677cd9a19c84760b37efe6.
First test attempt failed because a test expected16 first-pass writes despite
unchanged FOGENABLE being correctly skipped. Corrected test15; implementation
was not weakened. Final rebuilt suite passed. No deployment or push.
