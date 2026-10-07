# UI2 validation, 2026-10-08

## Repository and baseline

Active worktree `D:\Game\Master Rallye\master-rallye-re-general`, branch
`master`. Starting HEAD `f138de2364ea0457a220413507cfafa04704b84e`.
Preflight working tree clean, diff-check clean. UI1 commit
`ff8049b8e7f04406298f5938ecbb7eefa73eeeb5` was already committed and is the
direct parent of starting HEAD; PackFS foundation
`1d47e84bd3587e9dd56c393830a690ad3ef40368` is preserved. The intervening
PC renderer fix was not modified. No branch/worktree/push was created.

Before UI2, all **51** PackFS/UI1 tests passed with canonical inputs and UI
corpus enabled, zero skips. After changes all **80** tests passed, zero skips,
failures or errors: **26 PackFS +25 UI1 +29 UI2**. PSB/GXI/parser/resource
semantics were not redesigned. UI1 speculative Map init/update labels are
superseded in UI2 documentation without rewriting the historical UI1 report.

## Checks

| Check | Result and scope |
| --- | --- |
| Original provenance | All four canonical input hashes rechecked unchanged after analysis; ELF hash lock preserved |
| PackFS | Existing decompression/directory/range/unknown-build/malformed tests PASS |
| UI1 | Existing PSB mapping, quad verification, Null-bit preservation, GXI fail-closed and canonical primary-bank tests PASS |
| UI2 XML | Float32 values, document order, missing/duplicate route, malformed/vector type/count, NaN/Inf/overflow/declarations rejected |
| UI2 memory | 80-byte array with position +40, header pointer resolution, invalid offsets/alignment/counts/reversed pointers/stride/truncation/nonfinite rejected |
| Transform math | Four corners/center/interior, translation/quarter rotation, inclusive clipping, outside rejection, vertical/diagonal/zero-length segments PASS |
| Sprite diagnostic | Five screen-area anchors, local-Y sign and half-pixel bias PASS as conditional equations, not final GS-position proof |
| Map behavior | +/-32 marker window, finish bound, no bounds-fit, player chevron/opponent clipping and deterministic JSON/SVG PASS |
| Static evidence | Exact ELF map/rank vtable lifecycle entries, concrete polyline slot, original float-load offsets and scale matched independently of decompilation |
| Real route | Actual ITALYS1 decoded SHA and 293 records verified |
| CLI source parity | Direct named PackFS read and decoded XML read produce identical geometry; provenance differs appropriately |
| CLI repeat | JSON and SVG from identical XML/state are byte-identical on independent runs |
| Output protection | CLI refuses existing geometry output with exit2, preserving it byte-for-byte; path traversal/outside data/source overwrite rejected |
| Metadata repeat | Four generated UI2 JSON reports byte-identical on repeated build |
| Preview | Ignored map preview rendered and visually inspected; 16 clipped endpoint pairs /16 queue batches /one continuous debug strip; no screenshot tracing |
| Python | `python -m compileall -q ps2-research` PASS |
| Whitespace | `git diff --check` PASS; staged check performed before commit |
| Hygiene | Only tools/tests/address/layout/schema/transform/docs committed; all raw assets, exports, route geometry, screenshots and previews ignored |
| PC scope | No PC source edited; no PC renderer build needed; no gameplay/runtime confirmation claimed |

Local XML JSON SHA256:
`2ccaa683c3d51a4423097eb266bcfd997181a4404cdefeb379b26632bb35e494`.
SVG SHA256:
`76ee1fb7d013591817c76a12de42e6753b1e04431e239a79fe34c1ec2e04278f`.
These identify the explicit diagnostic state in minimap.md, not a captured
frame. Final verified outputs are `data/ui2/italys1-map-verified.json` and
`.svg`; direct PackFS equivalent is `italys1-packfs-verified.json`.
Earlier exploratory outputs are retained locally but superseded by these
verified files. Bounds, original/rotated points and generated files remain ignored.

## Screenshot evidence

The two full-race images were visually inspected:

- `Master Rallye_SLES-50906_20251213161001.jpg`, 1763x984;
- `Master Rallye_SLES-50906_20260415224620.jpg`, 1920x1072.

Both correlate with rank upper-left, timer/status upper-right, map lower-left,
dial lower-right and progress strip at bottom. Map route/chevron/dark shadow
and the later image's opponent crosses agree with the recovered procedural
primitive classes. The displayed partial route does not prove a fixed
overview; ELF subtraction/rotation proves the player-centered behavior.
No course or exact vehicle state was inferred from pixels.

Grade: **SCREENSHOT_CORRELATION**. Exact running ELF SHA, emulator version,
video-mode fields and per-frame source state remain UNKNOWN. Coordinates
were not changed to fit either screenshot, and the offline sample is not
presented as matching their route/frame.

## Reproduce tests

```powershell
$env:MASTER_RALLYE_PS2_INPUT='D:\Game\Master Rallye PS2'
$env:PS2_UI_CORPUS='D:\Game\Master Rallye\master-rallye-re-general\ps2-research\data\ui1\extracted\TNG\DATAPSM\HUD'
python -m unittest discover -s ps2-research/tests -v
python -m compileall -q ps2-research
git diff --check
```

Canonical corpus tests skip when the external inputs/local extracted assets
are unavailable; this run enabled them all. Ignored logs include
`data/ui2/validation-tests-final.log` and the bounded query logs. An initial
metadata-dependent run failed while the three source JSON files did not yet
exist; report creation/fallback to three unchanged UI1 exports corrected it,
and the complete final run passed. This is retained in the ignored first-run
log, not erased or described as a clean first attempt.

Final assembly review corrected the initial conventional-polyline assumption
in `146d80`; the odd/even endpoint comparison now matches the code. A new
continuity/batch test also found a shared-list bug in diagnostic merging,
which is fixed: every source segment remains an independent two-point list.
After those changes, all tests and both source/repeat CLI comparisons were
rerun. The final ordinary-sprite projection remains a **research limitation**, not
a failing automated test. Passing mathematical tests does not close that
ELF/COP2/runtime provenance gap or constitute a gameplay test.
