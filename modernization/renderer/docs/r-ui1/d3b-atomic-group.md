# R-UI1-D3b — Atomic Carousel Group Alignment

**Status: `BLOCKED_ON_ATOMIC_GROUP_OWNERSHIP`.** The D3a per-packet override is disabled at the render-decision boundary. The bounded motion classifier remains available as diagnostic evidence. PreserveMargins remains the fallback and `CarouselAlignment` remains opt-in.

## Evidence and decision

The supplied runtime evidence reports the following Race Select source X positions:

```text
375, 486, 597, 708
```

At 1920×1080, individual LEFT offsets on only the middle two packets produce:

```text
375, 379.333, 490.333, 708
```

That matches the reported 4.333-unit first gap and 217.667-unit last gap. This is `CONFIRMED_BY_TRACE` as supplied; `logs.zip`, the two session files and nine F10 JSONLs were not available in the checkout for independent parsing. The local `r-ui1-d3a-20261010.zip` archive contains only source, tests and documentation, not those raw runtime captures. The current attachment contains the trace summary, not the raw capture set.

The source-level cause is `UiMargins::draw_decision()` applying `margin=0` on a single `CarouselSemanticDecision::proven`, then discarding the matching retained anchor. This is `CONFIRMED_BY_SOURCE`. D3b now treats member motion as discovery evidence only. No packet state or anchor is deleted when a member is promoted; all draws continue through the ordinary PreserveMargins decision unless a real group policy is available.

## Membership boundary

The exact-retail owner investigation documented in [ui-group-ownership.md](../../research/r-gfx5/ui-group-ownership.md) checked the final consumer and nearby candidates:

| Candidate | Evidence | Boundary |
| --- | --- | --- |
| `DrawTextPacket`, VA `0x0056D110`, RVA `0x0016D110` | Reads one entity's packet and its point/content storage | No verified sibling/root link |
| Packet content vector | Validates rows within one packet | Does not establish membership across packet entities |
| Cached matrix at packet `+0x84` | Existing constructor/setter evidence | Matrix lifetime, not widget ownership |
| Camera submission/sort lists | Exact-build submit and sort functions | Broad scene ordering, not a complete carousel roster |
| Global renderer dispatcher | Exact-build singleton/vtable evidence | Renderer service, not UI subgroup ownership |

The previous bounded F10 capture was explicitly prefix/sample data. Its packet identities and candidate groups do not demonstrate total row coverage. The new trace summary strengthens evidence for a mixed-positioning defect, but does not provide group owner, selected-index linkage, full per-frame roster, or a pre-first-draw membership boundary.

The 100/111-unit gaps, common Y band, common FVF/caller and `proven_motion_path` can contribute evidence but are not enough alone. Other frontend packets around Y≈303.89 move with approximately 43.7-unit spacing and also satisfy the individual motion classifier. No independent source evidence separates every carousel member from those packets, or proves that a previous frame's observed set is complete for the next frame.

The completed-frame snapshot strategy is not safe yet: the proxy observes streaming draw calls, and a member can enter or be omitted after the snapshot while an earlier member has already been submitted. Applying a policy to the observed subset would recreate the partial-transform defect. No buffering or draw replay is introduced.

## Render policy and diagnostics

When `CarouselAlignment=1` is requested and the exact supported UI path is active:

- Individual status remains `candidate_motion_path`, `promoted_motion_path`, `proven_motion_path`, or the existing rejection reason.
- Group status is `GROUP_UNKNOWN`.
- Group membership status is `not_proven_no_pre_draw_roster`.
- Policy is `PRESERVE_MARGINS_FALLBACK`.
- Group ID, commit frame and member count are null.
- `carousel_override`, `carousel_group_override`, and `carousel_override_draws` remain false/zero.
- The fallback reason is `no_verified_pre_draw_owner_or_complete_roster`; missing frontend evidence reports `frontend_scene_evidence_unavailable`.
- A promoted motion member retains its original anchor; the anchor-discard count remains zero.

The same provenance is included in bounded `ui_packet_lifetime` draw observations and `ui_render_local` rows. `carousel_group_blocked_draws` counts member observations that are individually eligible but remain under fallback. D3a's completed-Present scene timing is unchanged.

## Synthetic coverage

The D3b native regression feeds four distinct packet identities through `UiMargins::enter_consume()` and `draw_decision()` across two frames, first at X=50 (admitting LEFT anchors), then at X=`375 + n×spacing`. Member A is promoted on the second frame while B–D remain candidates. All four preserve their original anchor ID and margin. The case is repeated with 111-unit Race Select spacing and 100-unit Vehicle Select spacing; effective source-relative intervals remain unchanged and no per-member override occurs.

Existing UI wrapper tests continue to cover `UiWorldScope` application, native draw count/HRESULT, packet immutability and exact WORLD restoration. D3a tests continue to cover previous-completed-frame authorization and stale/race/Reset rejection. Together these prove the fail-closed fallback contract, not a positive group correction or in-game visual result.

## Minimal next evidence

One focused owner verification must identify, before the first relevant draw:

1. The Race Select and Vehicle Select list owner and its UI epoch/screen lifetime.
2. The complete member set for the frame, mapped to validated entity/packet/point/content-storage/mode identities.
3. The selection-frame relationship and safe member join/leave/reuse boundaries.

If the game has no such owner, the next candidate design needs an independently verified complete pre-render roster. A bounded F10 prefix, geometric clustering, common texture/material, or motion alone cannot unblock group correction.

No visual validation is requested for this fallback build: it intentionally preserves the established policy and may preserve the older alignment defect. Keep the A/B setting opt-in. Do not enable it by default or remove the toggle until a complete group policy is implemented and passes Race Select, Vehicle Select, and unrelated-UI controls in game.
