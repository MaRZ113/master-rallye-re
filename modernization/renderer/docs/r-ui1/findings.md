# R-UI1 — Carousel Selection Alignment

**Status: READY_FOR_UI_DIAGNOSTIC_VALIDATION.** The current build adds bounded F10 evidence linking each verified UI packet consumer to its enclosed `DrawPrimitive` calls. No carousel-specific transform change is enabled because Race Select and Vehicle Select ownership is not proven by the currently available source/captures.

## Evidence and calculation

The supplied capture summary reports 1920×1080 Borderless with PreserveMargins, logical UI width 640, virtual width about 853.333, and `half_extra` about 106.667. It reports card WORLD X=375 and selection-frame WORLD X=371, with the card receiving a left adjustment and the frame remaining unshifted.

The reported 4:3 relationship is `375 − 371 = +4`. With the reported retained-left adjustment, the relationship becomes `(375 − 106.667) − 371 = −102.667`, a relative change of −106.667 logical units. The arithmetic matches the existing PreserveMargins policy. The original `course-frame-bug.jsonl`, `car-frame-bug.jsonl`, and screenshots were not present in the current checkout, so the reported production coordinates are treated as supplied evidence rather than independently re-parsed captures.

Current source confirms that `MarginAnchors::resolve` admits a direction from the existing historical point/left-text rules, then retains it on the validated entity/packet/point/content-storage/mode identity while coordinates animate. `draw_decision` uses the current packet point with that retained direction. `UiWorldScope` applies the margin only at the final UI draw seam (`DrawTextPacket` VA 0x0056D110 / RVA 0x0016D110; final draw return VA 0x0056D7C4 / RVA 0x0016D7C4), and restores the copied native WORLD matrix immediately. Packet coordinates and the engine transform cache remain untouched.

The native synthetic regression exercises this real policy and the production wrapper gate. It admits a left anchor at (23,370), retains it after the same packet moves to (375,250), and pairs that draw with an unanchored frame at (371,250). It observes the 106.667-unit relative displacement and verifies packet-byte immutability and full native WORLD restoration. This proves the policy can reproduce the supplied shape of mismatch; it does not prove that the two production packets are carousel members.

## Ownership boundary

Existing R-GFX5 ownership research records no proven cross-packet widget or sibling root at the final consumer. The current captures were unavailable, and the current checkout does not expose a safely validated Race Select / Vehicle Select owner, selected item index, or highlight-to-card relationship. The camera projection classifier provides only a last-classified `frontend`/`race` family; it does not identify a frontend screen. No unknown widget memory is read, and no semantic carousel ID is fabricated.

Therefore this change does not alter selection state, item order, packet anchors, transform policy, draw count, or draw order. Existing left/right/HUD/menu retention remains unchanged. The observed retained-anchor mechanism remains a strong hypothesis until the new capture connects packet identities and draw transforms to the actual card and highlight.

## Bounded diagnostics

During the existing three-frame F10 UI diagnostic window, a `ui_packet_lifetime` record now includes up to eight enclosed draw observations. The existing 64 observed-identity table and 256 UI-record cap remain. Overflow is explicit per packet and cumulative. Existing `ui_render_local` events are retained.

Each nested draw records caller VA/RVA and in-image status, primitive arguments, the known vertex-shader token and FVF 0x142 gate result when applicable, adjustment-gate result, suppression/forwarding, the current packet point, requested/applied margin, `GetTransform` HRESULT, native and effective WORLD X/Y, temporary `SetTransform` HRESULT, draw HRESULT, and restoration request/result. Restoration telemetry states that the original 16-float matrix was requested and whether `SetTransform` succeeded; no post-restore readback is performed. `current_screen_status` and `carousel_owner_status` remain `not_proven`; `selection_state_read` is false.

The added WORLD reads are read-only and occur only while F10 UI capture is active, inside a validated packet-consumer scope, and while an existing bounded record is available. Outside that diagnostic window, draw behavior follows the pre-R-UI1 path. R-CAM1-A2 camera-owner snapshots and other renderer diagnostics are unchanged.

## Conclusion

The retained-left path is a viable explanation for the reported relative offset, but membership and expected stock carousel geometry are not established. The candidate is ready for a short Race Select / Vehicle Select capture. Do not label either carousel fixed based on this synthetic result.
