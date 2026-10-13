# HUD-PORT0 verification and reproducibility

Research date:13October2026. No native implementation/staging/build change was
made by the HUD subtask; serial proxy builds remain the parent task's ownership.

| Check | Result / scope |
|---|---|
| Repository |master, HEAD0bddf7c7bc5e95831f98714ff6231da05ab073ea; renderer subtreee33386bcf682db6983380c499e4928726c758fe0|
| Frozen renderer status |No changed renderer paths at HUD preflight; no renderer files edited|
| Read-only Course SDK |HEAD4244fa0c4d878523c9947f54816bf377cdfb2589; clean status, branchresearch/r5t-course-archaeology; existing DXT reader reused|
| Canonical PS2 identity |Allfour inputs freshly full-file SHA256/size checked against UI provenance; PASS|
| Source payloads |4HUD PSBs/24HUD GXIs +1pause PSB/GXI decoded from original PackFS;4PCDXTs validated by existing SDK; PASS|
| PC scene/source formats |Original Hud0.xml parsed; PC DXB unsupported by PS2 PSB parser explicitly recorded; no guess/repair|
| R5900 byte probes |Rabbitizer1.16.2, explicit InstrCategory.R5900;6originalJALs+15matrix-kernel words valid; canonical PT_LOAD mapping; PASS|
| F10 captures |Visible2579:268forwarded native draws/32packet identities; hidden26331:268suppressed attempts/32identities. Both complete, owner mappingunmapped; PASS within scope|
| Existing HUD math tests |`test_hudruntime.py`:29/29PASS, including3canonical corpus checks;0skips|
| Existing PSB tests in Rabbitizer venv |24/25PASS;1ERROR:`ModuleNotFoundError: No module named 'PIL'` at `GeometryTests.test_quad_and_v_origin`; unavailable optional image dependency, no assertion failure; not silently skipped|
| Existing PSB canonical rerun by parent |Bundled Python with existing Pillow12.3.0, canonical PS2_UI_CORPUS and MASTER_RALLYE_PS2_INPUT:25/25PASS,0skips/0errors,0.053seconds. No dependency installed; separate rerun preserves the first attempt above|
| New HUD native implementation tests |NOT_APPLICABLE — no feature implemented|
| New HUD runtime acceptance |NOT_PERFORMED|
| Current menus/HUD performance |User-reported priorfix success retained as USER_RUNTIME_OBSERVATION; no new measurement claim|

Executed read-only source/capture audit (uses existing dependencies; installs
nothing and writes only compact research metadata):

```powershell
& ps2-research/data/revalidation1/tooling-venv/Scripts/python.exe `
  ps2-research/pc-port/docs/hud-port0/review_evidence.py `
  --ps2 'D:\Game\Master Rallye PS2' `
  --pc-retail 'D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked' `
  --course-sdk 'D:\Game\Master Rallye\master-rallye-re-course' `
  --logs 'D:\Game\Master Rallye Pristine\MRRRenderer\logs' `
  --output ps2-research/pc-port/docs/hud-port0/source-evidence.json

$env:MASTER_RALLYE_PS2_INPUT='D:\Game\Master Rallye PS2'
$env:PS2_UI_CORPUS='D:\Game\Master Rallye\master-rallye-re-general\ps2-research\data\ui1\extracted\TNG\DATAPSM\HUD'
& ps2-research/data/revalidation1/tooling-venv/Scripts/python.exe `
  -m unittest discover -s ps2-research/tests -p test_psbtool.py -v
& ps2-research/data/revalidation1/tooling-venv/Scripts/python.exe `
  -m unittest discover -s ps2-research/tests -p test_hudruntime.py -v
```

The PSB test command needs an already installed Pillow-equipped Python for
its one raster fixture. The first attempt in the existing Rabbitizer venv
failed for that missing dependency and is retained above; source/tests were
not changed to skip it. The parent reran the same suite with canonical corpus
variables using the already installed
`C:\Users\MaRZ\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
and Pillow12.3.0:25/25PASS,0skips/0errors. That separate rerun required no installation.

`review_evidence.py` requires canonical external PS2 inputs,protectedPCretail,
the read-only Course SDK and the two named F10captures. It is not a standalone
game-free test. The handoff can inspect docs/compact JSON without those private
inputs. No proprietary images, complete meshes,UIXML,ELF or raw logs are copied
into the docs. Existing `test_hudruntime.py` synthetic math/metadata tests and
noncanonical PSB tests can run without the game corpus when their conventional
dependencies/fixtures are supplied.

No new Ghidra/REA session was opened for HUD-PORT0. Prior exact PC consumer REA
dossier and historical UI1/UI2 maps were reused with explicit limitations.
Independent R5900 checks settle only the admitted words/kernel identity, not
live PS2 display state or a complete exact-EE HUD reconstruction.

Recommended subsequent HUD phase: **HUD-PORT1 — SpeedDial semantic packet mapping
and source plate pilot**, subject to the gates in `pilot-proposal.md`. Do not
start a full HUD rewrite, pause replacement or minimap during native physics work.

