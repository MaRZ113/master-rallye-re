# Remaining gates after J0

J0 delivers a usable offline manifest/compiler foundation. It is **PARTIAL**
as a public SDK because the unchanged-EXE runtime loader is not implemented or
qualified.

Before a runtime release:

1. Trace and correct the Vehicle Select re-entry/restoration writer so stored
   physical ID27 maps back to T2 local7 without disturbing stock Navara,
   ID26/T1, locked commit behavior, class changes, or per-player SplitScreen
   state.
2. Set ID27's race marker color to the desired independent `[1,0,1,1]` value
   in a runtime candidate and verify both initializer data and live Broker
   color. Existing I.1 captures show white.
3. Audit and experimentally qualify a removable unchanged-EXE runtime loader,
   resource overlay, rollback, and exact-build fail-closed behavior.
4. Exercise compiler output through a combined multi-addon runtime package
   using externally supplied qualified assets/physics data; the checked-in
   example definitions contain no proprietary payload.
5. Continue to separate runtime qualification from synthetic planning tests.

R5V-J.1 should focus on runtime integration/loader feasibility; J.2 on
multi-addon end-to-end qualification; J.3 on release packaging. No ID28,
custom class ordering, or new cooker work is authorized by J0.
