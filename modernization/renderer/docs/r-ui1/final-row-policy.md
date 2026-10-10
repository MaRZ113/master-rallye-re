# R-UI1-FINAL — Deterministic Carousel Row Alignment

Status: `READY_FOR_EXPERIMENTAL_IN_GAME_VALIDATION`. Visual acceptance of this new DLL is **PENDING**. Starting repository/branch: `D:/Game/Master Rallye/master-rallye-re-general`, `master`; starting HEAD `33835ae`. Worktree was clean; no branch/worktree created.

## Root cause and evidence

`CONFIRMED_BY_SOURCE`: generic LEFT admission survives carousel motion. D3a corrected only individually promoted packets, mixing zero and negative margins inside one row. D3b removed that correction, but its group-roster requirement left every draw on the buggy fallback. A uniform current draw-type policy needs neither previous positions nor a complete sibling roster. It does not establish a native widget owner or read selection state.

`CONFIRMED_BY_TRACE`, independently parsed read-only from `D:/Game/Master Rallye Pristine/MRRRenderer/logs/`:

- Session `session-20261010-034226-25264.jsonl` identifies pristine EXE SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and D3b DLL `9239753836649802f375624e3176b3f3981526ed3f1811b9c5806126e07d7fa5`.
- Three F10 windows contain 64 `ui_render_local` samples each, all 192 with `GROUP_UNKNOWN`, `PRESERVE_MARGINS_FALLBACK`, no carousel override. These remain bounded samples, not complete widget rosters.
- Each observed Y=309 card has packet mode 1 and two relevant DrawPrimitive calls: caller VA `0x0056D7C4` / RVA `0x0016D7C4`, FVF `0x142`, TRIANGLELIST, primitive count 1. Native consumer is VA `0x0056D110` / RVA `0x0016D110`.

| Frame | Observed source X, sorted | LEFT subset | Source spacing |
| --- | --- | --- | --- |
| 5166 Race | 153,264,375,486,597,708,819,930,1041,1152 | 153 through 708 | 111 |
| 6649 Race | -180,-69,42,153,264,375,486,597,708,819 | -180 through 375 | 111 |
| 8927 Vehicle | 275,375,475,575,675,775 | 275,375,475 | 100 |

The second frame's actual LEFT subset differs from the prompt's general description; the regression uses the parsed distribution. D3b's -106.667 LEFT offset doubles a boundary gap to 217.667 (Race) / 206.667 (Vehicle). All three native frame captures completed with Present result 0, no dropped records or restoration failures. Vehicle selection border at (371,304) is distinct from the card class.

Provenance SHA256 of the read-only inputs:

| File | SHA256 |
| --- | --- |
| session-20261010-034226-25264.jsonl | c9bae9704b612b3026e354ce369f396dc8b8a4e51ea1a020374454566495ae50 |
| frame-25264-d1-00005166.jsonl | ef75c2972e0c028a9206a156ce1be9c202988ce0880d74db36e4c082ff03bcc6 |
| frame-25264-d1-00006649.jsonl | abc06f5e07bd4f2946d4269571a6eb5f0d9dbde748f01a799fa055183aea9652 |
| frame-25264-d1-00008927.jsonl | 3dd1537c2bba60a383bfbe44f0390740b856d18abf017dcb06a73ab439a8fb8f |

Earlier sessions `session-20261010-025801-31248.jsonl` and `session-20261010-025935-37336.jsonl` were also read: 554/149 consume records, 58/16 at Y=309. Non-row packets in the old broad lane include Y=299.794,303.5,303.891,304,310.964,310.989,318.41; all fail the new narrow coordinate condition. No independently established non-card collision was found in these captures. A bounded capture cannot establish global uniqueness across all screens.

## Production policy

`carousel_row_reason()` receives current facts from `UiWorldScope` before the native draw. Required conjunction:

1. Opt-in `CarouselAlignment=1`, enabled PreserveMargins consumer and **exact pristine retail** profile. The device configures this separately using `Session::target`; ordinary feature-local margins on modified EXEs remain supported as before.
2. D3a valid frontend evidence, same frame before draw or immediately preceding successfully presented frame (age 1). Unknown, stale, failed/incomplete Present, race Source90, contradiction or invalidated epoch reject.
3. Active consumer scope; safe current entity/packet/point/content-storage/mode identity; finite XYZ and Z=0. Content storage must be non-null; no new content-vector dereference or owner hook.
4. Packet mode 1; `abs(source_Y-309) <= 1/4096` (0.000244140625, 8 float ULP at 309). Captured Y is exactly 309; this small numerical tolerance is an implementation choice, not evidence of a wider animated lane.
5. Existing wrapper safety gate: PreserveMargins UI projection, exact caller, identity VIEW, known FVF `0x142`, forwarded/non-suppressed DrawPrimitive TRIANGLELIST **count 1**.

There is no X bound, no motion/anchor admission prerequisite, no two-draw delay and no card-index or pointer constant. Both relevant subdraws satisfy the same predicate independently from the first call.

Match: `row_card_match=true`, `carousel_row_reason=verified_card_row`, `carousel_render_policy=source_coordinates`, effective extra margin 0. Nonmatch: original margin remains. `original standard margin` is recorded separately as `margin_requested` / `margin_standard`; sticky anchors and motion IDs remain intact. GROUP_UNKNOWN describes only historical diagnostics and is never rendering authority.

`CONFIRMED_BY_SOURCE`: original native draw occurs once in original order; its HRESULT is preserved. Source XYZ, content data, cached matrices, entity data, selection index and camera hooks are not written. Nonzero fallback retains the accepted WORLD copy/temporary translation/immediate exact restore/repair logic. Zero-margin draws do not set WORLD or need restoration; outside F10 they do not read WORLD. During bounded F10, GetTransform records native/effective WORLD without changing it.

## Regression and boundaries

`CONFIRMED_BY_SYNTHETIC_TEST`: production Device8 tests cover the exact captured 10/10/6-card rows and mixed LEFT/NONE distribution; all effective X values equal source X, preserving 111/100 intervals. Both subdraws, first observation, forward/reverse long scrolling, new/offscreen/negative X, packet reuse, storage/mode changes and unchanged anchor IDs are covered. Zero policy without F10 has no native WORLD reads/writes. Failure HRESULT and source bytes remain intact.

Negative tests cover border Y=304, decoration Y=303.89, old broad-lane endpoints, mode/FVF/caller/primitive/count mismatch, missing token, suppression/nonforwarding, unsupported exact profile, invalid storage, stale/unknown/race/epoch scene state, Stock, Centered4x3, opt-out, UI projection and VIEW guard. Existing HUD/decorative anchor, WORLD restore failure/repair, D2 repeated F10, D3a phase, display, reflection, camera and foliage suites remain active. Motion-only proof is still tested to have no rendering authority without current facts.

The camera-family classifier does not identify screen owners. Arrow/sidebar/main-menu/loading/HUD negatives are guarded by differing source or draw/context facts in synthetic tests; this does not prove every native element has been individually identified. Unknown scenes always reject; a yet-unseen frontend element with the **entire** matching signature remains an experimental collision risk. Any such runtime counterexample must be handled specifically, not with a broad lane or fabricated group membership.

Counters: `carousel_row_draws_matched`, `carousel_row_left_margins_suppressed`, `carousel_row_nonleft_draws_matched`. Bounded packet/draw records expose predicate reason, original anchor/margin, current source coordinates, scene provenance, native/effective WORLD, draw and restoration result. Zero-margin success correctly has `restore_attempted=false`; restoration is required only when a native WORLD change occurred.

See [validation](validation.md) for the actual build/test results and [handoff](runtime-handoff.md) for the single in-game acceptance run. Do not enable automatically or remove the public toggle before that run passes. No new EXE hook, camera implementation, Exclusive recovery, asset changes or deployment to the game directory occurred.
