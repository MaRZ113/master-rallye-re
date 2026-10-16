# PC PS2 Graphics Port

Current Turkey3 second-category pilot: [PS2-GRASS2](docs/grass-port2/final-report.md).
`GrassMode` and `ShrubsMode` are independent and default to Stock. Both source
categories now have runtime draw evidence and user-confirmed visibility;
the independent audit is adopted in rigid-port1/grass2-runtime-review.json.
Exact PS2 pixel parity remains unproved. The next bounded native physics
checkpoint is [RIGID-PORT1](docs/rigid-port1/final-report.md), with a read-only
lifecycle probe and byte-exact original convex conversion; safe private spawn
is still gated. [HUD-PORT0](docs/hud-port0/final-report.md) is research/design
only. Existing renderer and grass implementations remain unchanged.

This is the home for PS2-specific policies, material implementations, tests,
and the deterministic build overlay. `modernization/renderer/` remains the
immutable baseline; the overlay stages that renderer from a pinned Git commit
and applies exact patches only inside an ignored build tree.

## Current checkpoint

The newest addition is [PS2-COURSE-OBJECTS1](docs/course-objects1/final-report.md):
a Stock-default extra-surface layer for verified Turkey3 PS2 puddle source meshes.
It has its own private local asset and [manual A/B recipe](docs/course-objects1/runtime-ab.md).
This first material is a source-texture preview; full PS2 water rendering remains
separate. Earlier reflection and foliage bundles/builds remain preserved.

The preserved reflection checkpoint is [PS2-REFLECTION-PORT1](docs/reflection-port1/final-report.md):
one opt-in Tata bonnet material, using the original PS2 static environment
contribution. Its framebuffer contribution remains deferred. Stock defaults are
`FoliageMode=0`, `PixelProbe=0`, `ReflectionMode=0`. Follow the
[one-car A/B recipe](docs/reflection-port1/runtime-ab.md); live acceptance is pending.

The preserved `PC-VISUAL-PILOT1.3` added four temporary France1 `bush01` diagnostic modes to
the opt-in `treeblend` pilot. The standard build has no PS2 source or link
dependency. The PS2 build compiles the same single D3D8 proxy after staging
patches `0001` and `0002`.

The classifier requires the supported PC executable identity, a live France1
race-owner certificate, the exact submitted geometry fingerprint, complete
CPU upload mirrors, and current resource generations/revisions. It does not
match by texture, source draw ordinal, or callsite. User-supplied runtime
evidence confirms the exact draw was reached; the remaining question is
whether alpha/blend or depth-write behavior causes the observed visibility
defect. See `runtime-ab.md` for the four-mode test.

## Rebuild

From the repository root, run:

```powershell
python ps2-research/pc-port/overlay/build_overlay.py
```

The script rejects a different branch or frozen renderer tree, baseline renderer changes, source
hash mismatches, patch hash/path mismatches, or generator drift. It stages from
`git archive`, applies no fuzzy patch, builds both variants with MSBuild
`--parallel 1`, runs CTest and proxy verification for each, and then runs the
focused extension tests. See [the overlay handoff](HANDOFF.md) and
[`overlay/README.md`](overlay/README.md).

Unrelated research commits are permitted when the complete renderer tree stays
identical. Staging still reads immutable objects at the pinned baseline commit.
PILOT1.4's pixel diagnostic and previous handoff/build remain preserved.

Build outputs reuse `.build/baseline/` and `.build/ps2-enabled/`; verified source copies reuse `.staging/`. Final DLLs and manifests live under `dist/current/`. No DLL is installed into a
game directory. To test, manually copy the PS2-enabled DLL to a separate test
installation and follow [runtime-ab.md](runtime-ab.md).

## Reflection iteration after the independent runtime audit

The current bounded reflection experiment is [PS2-REFLECTION-PORT1.1](docs/reflection-port1.1/final-report.md). Mode4 includes a private mixed static/framebuffer source; modes2/3 separate the previous image and COLOROP changes. The exact Tata record19 classifier is unchanged. Stock remains default. New driver/visual results remain pending the next user test; prior Mode1 technical runtime success does not establish PS2 parity. Follow its runtime-ab.md, not the historical static-only recipe.

## First terrain-detail implementation

[PS2-GRASS-PORT1](docs/grass-port1/final-report.md) adds an isolated Turkey3 grass preview using original source/category placement and texture on strictly matched PC terrain. GrassMode0 is default; the private original-derived source pack stays local. Follow runtime-ab.md for the separate0/1 test. HUD/camera/other feature readiness and screenshot caveats are in visual-comparison.md. This is not exact PS2 clipping/projection or visual parity.
