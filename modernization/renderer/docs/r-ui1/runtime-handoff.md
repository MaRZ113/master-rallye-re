# R-UI1-FINAL — Experimental In-Game Acceptance

Status: `READY_FOR_EXPERIMENTAL_IN_GAME_VALIDATION`; visual result **PENDING**. Use the new DLL/hash in [validation.md](validation.md), not D3b. The deterministic [card-row policy](final-row-policy.md) is positive from the first eligible draw and no longer waits for a roster or motion promotion. D3a scene timing remains required.

Use accepted Windowed/Borderless at 1920x1080. Leave other display/AF/MSAA/camera settings unchanged; do not reopen Exclusive. Keep EXE/assets unchanged.

```ini
[Widescreen]
InterfaceMode=2
CarouselAlignment=1

[Trace]
Enabled=1
FrameSummaries=1
```

The option still defaults off. Optional A/B: restart with `CarouselAlignment=0` and identical other settings.

1. Vehicle Select: long list, beginning/middle/end, forward and reverse, stop at old broken positions. Central card should retain its stock relationship to yellow frame; no overlap, artificial doubled gaps, missing selected slot or learning-period snap. Large 3D preview must still match selection.
2. Race Select: long Challenge/Race list both directions, especially entries 5/6/7. Neighbor order and selected description must remain correct. Renderer does not change logical indices.
3. Brief negatives: selection frame, class/race-mode arrows, sidebars, moving decorations, static menu, loading, 3D preview and race HUD. No new shifting. Check return from race/Reset using the accepted display mode.
4. If visuals appear correct, take one Vehicle Select and one Race Select F10 capture. Keep session and matching frame JSONLs outside Git. Detailed sampling is bounded and cannot prove a complete roster.

Expected positive records:

```text
row_card_match=true
carousel_row_reason=verified_card_row
carousel_render_policy=source_coordinates
anchor_direction=left, margin_requested approximately -106.667
  -> margin_effective_request=0, margin_applied=0
anchor_direction=none, margin_requested=0
  -> margin_effective_request=0, margin_applied=0
```

Caller `0x16D7C4`, FVF `0x142`, mode 1, TRIANGLELIST/count 1, current source Y=309. Both relevant subdraws should follow this policy without waiting for motion. `carousel_status` is motion evidence only. GROUP_UNKNOWN does not veto a row match; group policy reports `diagnostic_only_not_render_authority`.

Scene should report valid `same_frame_before_draw` or `previous_completed_frame`, age 1 for early next-frame draws. Startup may reject unknown scene until first validated camera evidence; there is no per-card learning delay after frontend authorization. Inspect source/native/effective WORLD and actual draw HRESULT. `persistent_packet_writes=0`; no WORLD restore errors. A zero-margin draw has no WORLD set/restore, so `restore_attempted=false` is expected.

Summary counters `carousel_row_draws_matched` and `carousel_row_left_margins_suppressed` must increase; `carousel_row_nonleft_draws_matched` verifies unchanged neighbors also matched. On a specific failure, capture that item and inspect its emitted reason/context rather than starting a new broad investigation. An unseen non-card element with the entire matching signature is a remaining opt-in collision risk, since individual native screen ownership is not established.

Report:

```text
Vehicle forward/reverse, first frame and stopped positions: PASS / FAIL
Race forward/reverse, entries 5/6/7 and description: PASS / FAIL
Yellow frame and neighboring spacing stable: PASS / FAIL
Large preview still correct: PASS / FAIL
HUD/arrows/sidebar/decorations unchanged: PASS / FAIL
Return from race / Reset: PASS / FAIL
F10 positive LEFT/NONE zero-margin policy: PASS / FAIL
Capture IDs and any predicate rejection: ...
```

After both carousels pass: R-UI1 closeout makes the accepted fix automatic in PreserveMargins and removes the public toggle, followed by final regressions. Only then return to R-CAM1-A3. No Freecam or further camera-owner research in this pass.
