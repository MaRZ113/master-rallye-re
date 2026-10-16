# Correction: current sorted queue is only one native material pass

The original queue-contract recommendation to require the complete chassis cohort in manager+44/+48 was too strict. Fresh retained REA analysis of original `00562810` establishes why a valid Kia mixed opaque/glass body fails `queue_multiplicity`. This corrects that earlier interpretation; exact resource/geometry checks should remain unchanged.

Executable SHA-256 remains `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, evidence `ev_19a1616c2e1cbcfcc2f626e219c2a78f8fa4df86b01a740b7602ea72eccc1bf6`, full compact assembly/pseudocode in `queue-two-pass-evidence.json`.

## Original instruction-backed contract

- 00562831–0056288E enumerates contiguous 24-byte submission records in manager+24..+28, inserting their addresses into the pointer vector manager+44..+48.
- 00562890–005628C8 sorts that vector and dispatches its records. At 005628B2 it reads record+8 as material subindex, record+0 as instance and record+4 as mesh. The native emitter returns to 005628C1.
- 005628CA–0056290B clears/resets both that first backing vector's logical end and the pointer vector's logical end.
- 0056290E–00562960 enumerates the separate contiguous 24-byte submission vector manager+34..+38 into the same pointer vector.
- 00562962–005629CD sorts the second vector; 005629D9–005629F1 dispatches it with the same `[instance,mesh,subindex]` fields and emitter return address 005629EE.
- Existing producer 00562560 selects these two backing queues according to the material-vector flag bit 0 at leaf-material-vector+14. They are native opaque versus sorted-alpha submission boundaries, not two duplicate copies of a complete body queue.

## Minimal safe change

At an original first-pass source draw (emitter caller 005628C1), preflight the UNION of the two backing vectors manager+24..+28 and manager+34..+38. Each vector must be valid, aligned, divisible by 24 and bounded. Require every selected current source exactly once across their union, same instance and subindex 0. Recheck all descriptor/token/selected-owner/WORLD proofs as before. Keep the existing current pointer-vector join for the actual emitted draw; it remains correct.

Keep that complete cohort decision through the second alpha pass using the exact same frame, owner, target/camera cohort and current resource checks. Do not require the union to be rediscovered after first-pass submission: the original first backing vector has already been logically cleared. If no complete first-pass admission was made, an alpha-only arrival must retain Stock for the frame rather than replace a chassis after its opaque native part has rendered. If a complete body exists only in the second queue, a separately proven alpha-only policy is needed; do not infer it automatically.

This preserves the queue multiplicity safety gate using the actual full original queue representation. It does not remove the gate or accept missing/duplicate source records.
