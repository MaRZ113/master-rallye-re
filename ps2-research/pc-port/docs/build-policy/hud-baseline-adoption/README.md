# Approved HUD baseline adoption

Previous pinned source: `3f837f4ddcb27ee1034a4b0753634c92009360ec`, renderer tree `7f9f5a7d9464b7b86ff09a9bf6c34b7ce341682d`. Current approved source: `0bddf7c7bc5e95831f98714ff6231da05ab073ea`, renderer tree `e33386bcf682db6983380c499e4928726c758fe0`.

The renderer commit difference contains exactly four previously authorized HUD-cache files. Applying the archived third patch to pristine old Git objects independently reproduced all four current Git blobs byte-for-byte. The Markdown working copy has CRLF while its Git blob has LF; both hashes are recorded separately. Native source and test Git/worktree bytes agree. No renderer worktree file was modified.

The new exact seven-file extension patch applies to the new baseline, then the unchanged generator patch applies. Every resulting affected renderer byte equals the previously staged PS2-enabled renderer with the approved HUD patch. Both interface generators ran twice and produced identical locked output hashes. The old patch and lock are preserved here; the redundant HUD patch is not an active input.

Only source validation was performed during this adoption. No CMake tree or DLL was built in the migration step. Final build/test reports from the parent phase are the build evidence. Canonical stages are reused with their ownership manifest and verified synchronization; old CMake roots are never migrated or deleted by this step.

The builder still requires clean current renderer source and the exact complete renderer tree. Unrelated research commits remain permitted. Missing, extra, unreviewed or hash-mismatched active patches fail closed. This audit does not permit automatic baseline rebinding on later source changes.
