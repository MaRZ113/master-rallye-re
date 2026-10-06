# Untuned fallback semantics

For an ID outside the explicit tuned switch (including current ID26), retail
constructs a `vehicles/rev9` sample object. Its helper defaults include
sample-object field `+0x1C = 0x3FC00000`; the common constructor then writes
shared fields and the default path uses curve table A. It emits
`gaAiVehicleSound: Warning - untuned car engine sound used (CarID %d)` with
the original queried ID.

This is a working engine-audio fallback. It is not an explicit tuned profile,
and it should not be described as a broken or missing WAV. The G.2 candidate
does not suppress the warning. It changes the profile-selector result for ID26
so the original constructor reaches a donor's tuned arm. The runtime test
must verify the warning disappears naturally.

Pristine retail ID25 is not an initialized vehicle record. G.1 uses the slot
for Trooper, but its audio selector remains outside the retail tuned cases and
is not changed by this G.2 patch.
