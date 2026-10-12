# Corrections and scope notes

This pass supersedes no original TREEBLEND1 or PILOT1.3 implementation finding. It adds an independent R5900 byte check and a fresh four-mode PC runtime correlation.

* The earlier PILOT1.3 symptom was described with two competing hypotheses. New Mode 3 evidence shows that disabling depth writes alone is sufficient to reproduce the disappearance in the supplied view; it still does not identify an occluding draw or prove the PS2 cause.
* The white-card Mode 2 result is not explained by the stored PC DXT alpha-zero RGB: inspected source texels have non-white RGB values. Runtime format, bound texture identity, sampled texels, diffuse alpha, and blend calculation remain open.
* The user previously reported 5,364 successful identity events in a longer session. This pass uses the four supplied mode-specific sessions and complete paired F10 frames, which each contain one target call. Those sample counts are not contradictory because they cover different session scopes.
* Screenshot-to-mode association is ordinal and supported by file timestamps. The JPEG files themselves do not assert mode identity, and some surrounding scene details differ between stills. The selected camera bookmark is reported, but exact camera pose and pixel registration are not established.

The only independently confirmed cause is: the pilot's `ZWRITEENABLE=FALSE` policy is sufficient for the captured disappearance. The specific mechanism that makes bush pixels disappear remains unresolved.
