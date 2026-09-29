# SFL / FL / SF spatial registration status

R5T-A's structural findings remain the current evidence: retail SFL files have
a 20-byte header followed by `width * height` bytes; old Demo 8.4.1 FL/SF
candidates include 20-byte headers with four payload bytes per cell. The
semantic field names, cell interpretation, and FL/SF-to-SFL evolution remain
unproven.

The R5T-B.1 local course-source inputs do not include the raw SFL/FL/SF fields
or matching developer TGA visualizations needed for new spatial registration.
No dimensions were stretched onto course bounds, and no association to GXM
points, DX vertices, markers, or BSP was made. This phase adds no new SFL
correlation or visualization result.

The source-to-DX global coordinate relation does not resolve the SFL origin,
axis order, sampling, payload semantics, or whether a field describes the
whole terrain or a course-dependent subsystem. Keep SFL semantics **UNKNOWN**.
