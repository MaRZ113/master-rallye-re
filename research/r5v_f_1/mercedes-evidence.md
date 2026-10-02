# Mercedes evidence gate

Mercedes work was not audited during R5V-F.1. The R5V-F.2 prompt reports cleanup
P0 FULL PASS and an ID26 red marker runtime observation. It explicitly makes
the unreported ID0 marker A/B check non-blocking for the source audit. The
Mercedes audit is now starting; no Mercedes candidate has been built.

Audit sources independently using this order:

1. an already tested retail-compatible Mercedes package in the beta/research
   branch;
2. Mercedes resources from demo-8.4.1, only if the existing cooker/conversion
   route is proven for this source revision;
3. stop and name the exact blocker if neither provides validated retail-ready
   model and collision data.

Keep the target invariant `ID26 / T1 local7`; IDs0–25 and all other class
mappings remain unchanged. Do not declare a Mercedes runtime family until its
model, physics and authentic collision evidence is complete. Do not create a
Mercedes candidate before all F.2 static model, physics, collision and
dependency gates pass.
