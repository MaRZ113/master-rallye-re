# Mercedes evidence gate

**Not audited in R5V-F.1's first stage.** The prompt makes Mercedes work
conditional on cleanup P0 and P1 both passing. No Mercedes binary, assets,
physics, collision, localization or frontend content was inspected or staged in
this turn.

After `R5V-F CLEANUP = FULL PASS`, audit sources independently using this order:

1. an already tested retail-compatible Mercedes package in the beta/research
   branch;
2. Mercedes resources from demo-8.4.1, only if the existing cooker/conversion
   route is proven for this source revision;
3. stop and name the exact blocker if neither provides validated retail-ready
   model and collision data.

Keep the target invariant `ID26 / T1 local7`; IDs0–25 and all other class
mappings remain unchanged. Do not declare a Mercedes runtime family until its
model, physics and authentic collision evidence is complete. Do not create a
Mercedes candidate before the cleanup runtime gate.
