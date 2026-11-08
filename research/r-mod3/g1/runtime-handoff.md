# G1 focused runtime handoff

Use a disposable copy of the exact supported retail installation. The G1
development ZIP is separate from the published beta. Do not replace the
original `MRallye.exe`, the graphical `d3d8.dll`, or another mod's
`dinput8.dll`. If a test copy already has a local DirectInput proxy, create a
clean copy for this candidate instead of overwriting that proxy.

The candidate accepts only the pinned retail executable:

```text
SHA256  bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4
```

Copy one profile from `profiles\` to `MRallyeRandomizer.ini` beside
`MRallye.exe`, then launch the original executable normally. Restart the game
when changing `MaxOpponents`; that limit is fixed at startup. The existing
live-reload behavior applies to policy snapshots only at new roster
generation boundaries.

Run this short sequence and stop at the first crash, malformed roster, or
course-placement problem:

1. With a T1 player, use `six-ai-t1-same-class.ini`. Confirm six AI with
   distinct non-human T1 CarIDs and normal Start.
2. Restart, select `seven-ai-t1-same-class.ini`, and select a T1 player.
   Confirm eight total participants, strict T1 eligibility, and at least one
   repeated AI CarID in separate participant slots.
3. Restart, use `seven-ai-t2-same-class.ini`, select a T2 player, and make
   the same checks.
4. As a control, use `seven-ai-t1-outside-class.ini` with a non-T1 player.
   The selected AI must remain T1.
5. Optionally use `seven-ai-full-control.ini` as the mixed-class control.
   `seven-ai-t1-never.ini` should refuse an impossible all-unique T1 roster
   before race setup.

For each accepted race, check that every slot has its own participant and AI
movement, and that the race can finish, show Results, and return to the
frontend. Where Observatory is available, capture CarID, CarClass, PlayerType,
and DriverID for Car0 through Car7. Repeated CarIDs are expected only among
AI participants; each slot must retain its own DriverID and controller.

These tests do not require Vehicle SDK, addons, Observatory hooks, or a
particular track. Course geometry, start-grid clearance, and RaceLine remain
separate owner-managed qualification. Synthetic participant fixtures do not
prove the live actor lifecycle.

