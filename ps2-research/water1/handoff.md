# Handoff integrity

The fresh local WATER1 archive contains this phase's documents/compact JSON,
PS2 research Python tools/tests, and all four small historical UI2 JSON fixtures:
`elf-hud-functions.json`, `hud-runtime-map.json`, `hud-runtime-structures.json`
and `minimap-format.json`. The three mandatory UI2 test fixtures are explicitly
included rather than relying on a neighbouring checkout.

Every bundled file has a manifest path, size and SHA256. The manifest records
the actual containing commit and external roots. Its own integrity is covered
by the archive's external SHA256 receipt; it cannot hash itself recursively.
No proprietary ELF/PAK/000, extracted PSM/GXI/PSB, screenshot, full geometry,
Ghidra project, full decompilation or RAM dump is bundled.

Bundle-only tests use synthetic fixtures and compact metadata. Original-corpus
tests require separately provided canonical inputs. Some synthetic scene tests
also need the read-only Course SDK. Pillow is needed by UI image diagnostics;
pytest is optional for unittest and required for pytest coverage. Ghidra/bridge
are optional external dependencies for new executable queries, not for running
the offline Python parser/matcher tests.

Required external roots for full validation:

| Variable | External source |
|---|---|
| MASTER_RALLYE_PS2_INPUT |Canonical SLES_509.06,SYSTEM.CNF,TNG.PAK,TNG.000 directory|
| MASTER_RALLYE_PC_INPUT |Validated retail Data.sma_unpacked root|
| MASTER_RALLYE_COURSE_SDK |Read-only SDK checkout with master_rallye package|
| PS2_UI_CORPUS |Ignored extracted HUD PSB/GXI directory from UI1|

Historical UI2's original RaceTest XML test additionally expects ignored local
`ps2-research/data/ui2/ITALYS1.XML`; the proprietary XML is deliberately not
bundled. Its absence must remain an explicit SKIP, not be filled with an invented
original fixture. Full repository tests on this workstation had zero skips.

An isolated copied bundle was tested with all corpus/SDK variables unset:
unittest reported167 runs and15 skips; pytest reported154 passes,22 skips and
153 passing subtests. There were no failures. The differing skip totals reflect
unittest class-level skips versus pytest's per-test collection. These are
bundle-only synthetic/metadata results, not original-corpus or runtime PASS.

The final archive and SHA receipt remain ignored under data/water1. Its manifest
is checked by extracting into a new scratch directory and verifying every
listed payload. Standalone test results and explicit external-input skips are
recorded in the local closeout receipt and final handoff README.
