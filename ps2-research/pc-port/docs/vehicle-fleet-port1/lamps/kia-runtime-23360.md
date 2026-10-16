# Kia runtime23360: new glow blocked before identity

The supplied88dd4e7a DLL F10s show no32-vertex/32-face glow-shape candidate
in7771 or8691. Frame14443 has exactly one, sequence1022, native call
`DrawIndexedPrimitive(4,24244,32,48342,32)`, HRESULT0, shared-world caller
RVA0x17707E. This sequence number is diagnostic only.

The decisive difference is **FVF0x102, stride20 (XYZ+UV, no normal)**. Existing
`brake_glow_native.hpp` only accepts FVF0x112/stride32 and exits before the
identity matcher and its diagnostic. `fleet_glow_identity` and its
`position_uv_corner_sha` dependency also exclude0x102. Therefore this observed
candidate cannot receive the current override, even though its source-count
shape matches the original Kia glow.

The same frame contains ON-shape native call `(4,24228,16,48306,12)`,
FVF0x102/20, texture creation serial778. Its vertex/index ranges directly
precede the glow range (16vertices,36indices apart), matching original PC
Kia records31 ON /32 glow. Glow texture serial779 is32x32. This supports the
reported held-brake observation, but F10 does not include raw upload bytes;
the exact current XYZ+UV identity remains unproved by this report. The earlier
frames contain neither compact-layout ON candidate nor glow candidate.

Glow logical/native-input states match the established admission policy:
ZENABLE1, ZWRITEENABLE1, ALPHATESTENABLE0, ALPHABLENDENABLE1,
SRCBLEND5(SRCALPHA), DESTBLEND6(INVSRCALPHA). F10 tracks logical state; no
private glow transaction occurred. WORLD is finite and retained verbatim in
`kia-runtime-23360.json`. Resource IDs and ranges are historical observation,
never persistent classifiers.

The installed PS2BrakeGlow.gxi matches the required original SHA
`b6350f92f674bf2b63200ce4bb39c0c26f03fd99856ac0b89e7fc0797861af09`.
Current INI has BrakeGlowMode1/Version1/Diagnostics1 and ReflectionMode4.
The final session file is8,049,198bytes, **not16MiB**; it contains no
ps2_brake_glow event, consistent with rejection before logging. This does not
prove all other admission gates would pass after layout correction.

## Smallest safe correction

Admit the exact additional XYZ+UV layout0x102/20 in this bounded glow path.
Normalize a CPU identity snapshot to the existing0x112/32 shape (copy XYZ,
zero unused normals, copy UV). Match the unchanged original PC position+UV
and geometry hashes; do not widen geometry tolerances or use counts as
identity. Keep original native buffers/FVF and the one original draw unchanged.
Since normal bytes do not enter the fleet hashes, this adapter is exact for
their semantics. Terrano's additional normal-inclusive certificate must remain
enforced; do not remove it to accommodate another family.

Run positive/negative corpus fixtures through both0x112 and0x102 encodings,
including one-bit UV/XYZ corruption, bad lengths and stale generations. Then
bounded current-upload diagnostics should record the identified family/hash,
layout and apply/draw/restore HRESULTs. If the compact candidate fails its exact
hash, add a single F10-only compact upload capture rather than relaxing it.

No renderer, build, configuration or installed asset was modified by this audit.
