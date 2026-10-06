# R-GFX4-3: current draw context and temporal frame history

**CONFIRMED_BY_CODE_AND_RUNTIME_TRACE:** R-GFX4-2 reset the temporal tracker whenever a successful PROJECTION setter left the source90 race family. A normal captured frame switches from race perspective to late HUD ortho before Present. Consequently its observed groups were erased before matching, and previous-frame identities never matured. This is independent of the already fixed resource-pool lifetime.

The four supplied R-GFX4-2 files contain 585/609/524/535 draw records, 252/286/190/203 known signatures and zero tracked or modified draws. Each has a perspective setter at sequence3, followed by a late non-perspective setter after its last race draw. Two actual successful Resets in session4884 report epochs21170/21598, despite reset_count2. Managed metadata retained1510, removedDEFAULT1 each time. [Hashed input evidence](continuation2-runtime-evidence.json) preserves these observations; raw captures stay external. A visible lack of reflection change on that DLL establishes **zero execution**, not a subtle reflection result.

The previous [findings](findings.md) said that “projection/context/resource transitions do” clear identity. That statement conflated two lifetimes. The correction is limited to this continuation:

| State/event | R-GFX4-3 behavior |
|---|---|
| `race_context` | Eligibility of the current draw only |
| `race_seen_this_frame` | Set by a successful known race projection or mapped world draw under a retained cached race projection |
| Race → HUD/2D projection | Current context becomes false; observed groups and previous identities survive |
| Successful Present after any race in the frame | Match/age groups, solve existing constellations, serialize completed results, advance observation buffer |
| First completed menu-only frame | Expire stale race history once; following menu frames do not repeatedly increment epochs |
| Failed Present | Invalidate active race history; no new completed-frame proof |
| Successful Reset | Clear tracks and frame/context flags; retain MANAGED/SYSTEMMEM/SCRATCH generations, remove DEFAULT/RT/depth metadata |
| Failed Reset | Preserve classifier/resource state; camera FOV proof separately expires at the Reset boundary |
| Resource pointer reuse/capacity invalidation | New generation still clears temporal identity conservatively |
| Disappearance | Existing one-complete-frame lease expires; reappearance must relearn |

No constellation thresholds, four-wheel geometry, nearest-match rule, fingerprint, reflection material gate or aesthetic tuning changed. A source45 frontend projection suppresses its current draws immediately. If it follows race in the same interval, history expires only after a subsequent frame with no race context. VIEW/lookback does not define object lifetime.

**CONFIRMED_BY_SYNTHETIC_TEST:** a real wrapper/mock timeline repeats race projection → body/four wheels → HUD ortho → HUD indexed draw → Present. Its IDs remain stable and age, epoch stays constant, reflection starts on mature body draws, and the HUD contributes no vehicle signature or temporary TCI. A menu-only interval clears the lease once. Successful Reset retains managed generations and then relearns through full HUD-ending frames. Logger-off and serialized F10 paths both pass. These results establish software contracts; human game classification remains pending.

F10 schema1 remains additive. `frame_summary.classifier.epoch` and `race_seen_this_frame` now expose the lifetime boundary. Frame-end classification and draw-time reflection decisions retain their distinct meanings. Human Stage A must establish positive mature body/wheel tracks before later reflection judgments.
