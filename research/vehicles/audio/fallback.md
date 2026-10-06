# Untuned fallback semantics

For an ID outside the explicit tuned switch (including current ID26), retail
constructs a `vehicles/rev9` sample object. Its helper defaults include
sample-object field `+0x1C = 0x3FC00000`; the common constructor then writes
shared fields and the default path uses curve table A. It emits
`gaAiVehicleSound: Warning - untuned car engine sound used (CarID %d)` with
the original queried ID.

This is a working engine-audio fallback. It is not an explicit tuned profile,
and it should not be described as a broken or missing WAV. G.2 does not patch
or suppress the warning. Its profile selector changes the constructor input
for physical ID26 so the original switch reaches a normal tuned arm. Exact-
candidate A/B and audible results confirm profile selection at runtime; the
literal warning line was **NOT DIRECTLY RECAPTURED** in the Broker snapshots.

Pristine retail ID25 is not an initialized vehicle record. G.1 uses the slot
for Trooper, but its audio selector remains outside the retail tuned cases and
is not changed by this G.2 policy. Its current result remains fallback unless
separately configured with a proven stock profile.
