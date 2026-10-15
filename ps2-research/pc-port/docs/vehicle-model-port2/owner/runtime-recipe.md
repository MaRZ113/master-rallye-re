# One current owner to model consumer

This is a bounded diagnostic, not replacement admission. Original executable
SHA-256: bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4.
Do not use the observed pointers in a later process, after car change, menu exit,
restart or Reset. A running sampler cannot discover this owner without scanning;
the initial register evidence therefore requires user-operated x32dbg.

1. Leave X-Trail selected in VehicleSelect, replacement disabled. Attach x32dbg
   to the current MRallye PID. Run `scriptload` with owner-stop.x32dbg, then
   `scriptrun`, then F9. It stops once at original callback0044C4F6 and disables
   that breakpoint. Copy the PORT2_OWNER log line. Remain paused. EDI must have
   vtable0069020C; EBP is the current Egg, [EBP+50] its packet.
2. Run probe.py with that current PID, AI and Egg, writing a NEW ignored analysis
   JSON. It opens PROCESS_QUERY_LIMITED_INFORMATION|PROCESS_VM_READ only and
   reads only proven fixed fields, with repeat-read checks and a64KiB cap.
3. Generate consumer_script.py with the current packet and exact original EXE.
   Load its output in x32dbg, run script and F9. One identity-filtered stop at
   0056BDD4 records ESI packet, ECX original compiled model and [ESP] instance.
   The instance's B0 back-reference must equal packet. This original call invokes
   0054C9D0, whose54CAF4 writes model into instance+8C before dispatching nodes.
4. Copy PORT2_CONSUMER, remain paused, run the same one-shot reader again into
   a different output. Compare current model/cache/back-reference. Then remove
   the two breakpoints, resume, and take a same-session F10 frame with frontend
   diagnostic enabled. Preserve current upload generations and full geometry
   signatures, scene and matrices; do not substitute draw ordinals for identity.

The completed process53228 observations additionally used consumer_script.py
`--emitter` to stop at00577067, filtered by current instance+B0 packet. That
record and a bounded current model-list traversal close the source node to
actual draw/buffer descriptor join; see current-findings.md/current-join.json.
Model-name field+C is a string ID, not a char pointer; its resolver remains
UNKNOWN. Source proxy COM addresses require existing unwrap APIs before comparing
current native F10 buffers. No observed pointer becomes future admission authority.

Instrumentation adds temporary debugger breakpoints and changes timing; it does
not alter the original file, call a loader, mutate game data, or spawn objects.
Current live captures are retained separately, with exact process identity and
read-only boundaries. Replacement itself was not implemented by these tools.
