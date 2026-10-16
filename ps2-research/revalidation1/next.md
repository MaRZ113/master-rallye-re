# One next experiment

Recommend exactly one bounded follow-up: **PILOT1.4 alpha-test-only mode**.

Add one temporary mode to the existing state-mask pilot that changes only
`D3DRS_ALPHATESTENABLE=FALSE`. Keep alpha blending disabled, preserve the
original `SRCBLEND`/`DESTBLEND` values, preserve `ZWRITEENABLE`, and change no
other state. Capture it and Stock from the same France1 Free Camera bookmark,
resolution, and settings, after restarting for each mode. Retain the full
renderer log and screenshots with DLL/config hashes and the exact target
resource generations.

Why this has the highest information gain: the user-reported Mode 2 changes
alpha test, blending, and blend factors together and produces white cards, so
it does not tell which alpha operation causes that artifact. Mode 3 changes
only depth writes and reportedly reproduces the disappearance, which makes
depth writes a plausible contributor but does not establish the later
occluder or per-pixel depth interaction. An alpha-test-only sample cleanly
tests whether removing cutout rejection alone reveals the rectangular card
while leaving blending and depth policy at Stock.

Do not add texture replacement, transparent sorting, extra draws, or another
state change in that experiment. Keep the current root-cause result as
unresolved until the paired capture is supplied and reviewed. No PILOT1.4
code is started by this audit.
