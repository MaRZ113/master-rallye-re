# Visual Parity Expansion handoff

Contains the exact tested PS2 overlay sources/tests, compact source contracts,
per-vehicle/course coverage, unchanged baseline lock and exact patches, build
report, two independent Win32 DLLs and SHA-256 manifest. No original GXI, DX,
PSM, terrain/point arrays, game binaries, process dumps or staged renderer copy
are included. No second proxy/chaining or automatic deployment exists.

See `docs/visual-parity-expansion/final-report.md` and `command-log.md`, then
`docs/reflection-port2/runtime-ab.md` and `docs/grass-port3/runtime-ab.md`.
Physics evidence is preserved, not implemented. HUD is roadmap-only.

## Rebuild

Requires a Git checkout containing frozen commit0bddf7c and renderer tree
e33386b, the original untouched renderer worktree, CMake/MSVC Win32 and Python:

```powershell
python ps2-research/pc-port/overlay/build_overlay.py
python ps2-research/pc-port/overlay/package_visual_expansion.py
```

The reusable `.build/baseline`, `.build/ps2-enabled` and `.staging` are generated
and ignored. Stage only exact verified Git objects; no fuzzy patches. Do not
install either DLL into the game automatically. Stock defaults remain0.

## Corpus-independent review

From the extracted layout, synthetic asset/signature/configuration tests need
Python only. Tests that inspect staged native integration require the external
frozen checkout and staging. Native CTest requires MSVC, baseline SDK headers
and staging; it does not require private game assets for synthetic coverage.
Optional private-input native integration requires the explicit MRR_* asset
environment variables documented in the command log. A complete345-test PS2
research suite is external to this compact handoff; its actually executed
results are reported, not promised as bundle-only coverage.

The new vegetation inventory test needs `course-inventory.json` and existing
detail parser source, included. Asset preparations require canonical PS2
TNG.PAK/TNG.000, protected PC retail corpus and read-only Course SDK. Original
resource/placement blobs must be regenerated locally into ignored `.assets`.
`compare_selected.py --asset-directory` is restricted to `.assets/grass` and
requires byte-identical independently frozen artifact hashes. Raw game image
content is intentionally absent. Reflection source audit additionally needs
the validated local vehicle extractions used by REFL1.

No Blender dependency exists. New visual runtime/parity remains user-pending;
the earlier Mode4 trace is independent evidence for the retained fallback.
The original renderer Python quality module remains BLOCKED on missingpefile;
other tests are not silently skipped or weakened to hide it.
