# Alpha-tested geometry without an invented foliage owner

**CONFIRMED_BY_EXE:** base/env/noise alpha-test setups use ALPHATESTENABLE15=1,
ALPHAREF24=128, ALPHAFUNC25=5 (GREATER), ALPHABLENDENABLE27=0. Base alpha-test
setup writes ZENABLE1/ZWRITE1; common emission can override depth from instance.
They join the opaque queue rather than the alpha-blend queue.

**CONFIRMED_BY_EXISTING_RESEARCH:** R5T foliage notes correlate source resources,
materials and compiled output, while retaining causal flag unknowns. This phase
does not silently convert those correlations into a proven vegetation classifier.

The shared scene/compiled draw path is established; a distinct tree/bush/fence/
grass renderer owner is not. Alpha-test signature alone also matches other cutout
content. Reliable classification needs model/texture provenance together with the
state signature. Future shadow replay must preserve the original cutoff and final
depth behavior. Alpha coverage/MSAA policy is later work and requires visual checks
of these edges.
