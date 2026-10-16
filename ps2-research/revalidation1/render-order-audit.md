# Render-order and four-mode hypothesis audit

## What the static PS2 queue proves

TREEBLEND1 identifies `tree`/`object` bucket 0 and `treeblend` bucket 1. The
queue drain at `0x0031cd98` emits ascending bucket groups for that drain. It
does not prove a global frame ordering, a distance sort, a global opaque vs
transparent order, or that later PC draw calls are the same PS2 queue. The
queue and handler findings remain prior `CONFIRMED_BY_EXE` evidence; REA did
not re-decode the PS2 ELF.

## What the user-reported A/B suggests

Mode 1 changes alpha test, alpha blend/factors and depth write; mode 2 changes
the alpha bundle while preserving PC depth-write; mode 3 changes only depth
write. The reported pattern is therefore:

- Mode 2 stays visible as opaque-looking white rectangular cards even with
  the alpha bundle changed.
- Mode 3 becomes nearly invisible when only depth writing is disabled.

This makes disabled depth writes a plausible primary contributor to the
disappearance. It does **not** prove that a particular later draw overdraws
the bush, nor exclude interactions with target alpha, texture-stage state,
depth testing, neighboring foliage, or draw order. Mode 2's white-card result
shows that the alpha bundle has its own symptom but does not isolate alpha
test from blending because those settings change together.

Confidence: **low-to-medium directional evidence**, strictly
`USER_RUNTIME_OBSERVATION`; root cause unresolved.

## Competing hypotheses

| Hypothesis | Supporting evidence | Missing proof |
|---|---|---|
| Disabled depth write causes later foliage/geometry to occlude the target | Modes 1 and 3 reportedly disappear; mode 3 changes only depth writes; target was early in the reported PC frame | Raw mode captures, later occluder identities, depth values, per-pixel test |
| Alpha/test/blend and texture-stage interaction creates the card/disappearance behavior | Mode 2 reportedly becomes white cards; PS2 and PC images have different dimensions/alpha distributions; pilot retains PC texture | Actual bound stage states, texture/diffuse alpha, sampling and original screenshots |
| Combined ordering and state interaction | Draw order is known to be early in one reported frame and blended mode retains opaque/cutout placement | No frame-level state/order trace or controlled captures in handoff |

Do not describe the current evidence as a proven Z-buffer defect.
