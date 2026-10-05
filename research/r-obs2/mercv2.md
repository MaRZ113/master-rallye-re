# Mercedes v2 target

Expected target from the supplied task:

- Current reported file name: `MRallye.exe` (name is not a trust signal)
- Size: 3,121,214 bytes
- SHA-256: `1fbb3489208de9bc0af3802902a8611ea9a149c245031d1563960bd91b430c14`
- Expected family: `retail-broker-v1`
- Expected registry: `merc-id26`
- Expected active-race Broker capture: enabled
- Expected post-Results native Dump safe: false
- Expected legacy Loading-to-Attract path present: true

The user provided the target path in the sibling vehicle worktree; it was read only and not modified. It has the expected SHA and size. The family audit accepted it as `retail-broker-v1`, and the separate registry detector recognized `merc-id26`. The phase brief reports an earlier comparison of about 222 changed bytes in roughly 21 small ranges and unchanged Broker anchors relative to pristine and merc v1; the family audit now independently verifies every configured Broker anchor against the target.

The audit tests against the actual tracked `inputs/MRallye_merc.exe` (merc v1), the user-provided mercv2 target, and a synthetic non-anchor mutation. It proves this exact v2 image passes the family and registry audits, while synthetic critical changes still fail closed. It does not prove runtime behavior; the human smoke remains required.
