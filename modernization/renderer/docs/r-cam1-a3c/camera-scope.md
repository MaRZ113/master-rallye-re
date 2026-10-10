# R-CAM1-A3c: camera scope boundary preserved

A3b's reviewed native reader extent is reused, not reopened. Its
[scope-closure](../r-cam1-a3b/scope-closure.md) and current
[machine map](../../research/r-cam1-a3/camera-scope-map.json) retain the evidence.

The existing pre-submit GameFov CALL is VA **`006532DD`**, RVA
**`002532DD`**, targeting `00509680` with RET8.
FinalizeCamera, particle Current Pose reads, EndFrame's late builder and debug
consumers all remain after traversal. Restoration at `006532E2`, `006532E9`,
or proxy Present is insufficient for a future full camera pose scope.

The completion candidate is VA `005B0166` / RVA `001B0166`, targeting scheduler
`00653080`; it returns at `005B016B`, with one float argument and RET4.
**That scheduler bridge is not installed, implemented or ABI-tested in A3c.**
The tested lifecycle RET4 wrappers are not evidence for the scheduler's full ABI.

This observer introduces no pose, VIEW or frustum writes. Existing GameFov-only
behavior and its Present/Reset restoration remain unchanged. No second owner is
introduced at its submit hook. There are no FreeCamera controls or INI options.

After the live certificate is proven, a single coordinated owner must span native
traversal through the post-scheduler seam, including reentrant cancellation. Its
owned fields remain CPU planes `+08..37`, Previous Pose `+38..77`, Current Pose
`+88..C7` (176 bytes). Native viewport `+78..87`, source/flags and snap must be
preserved. Earlier entity sorting/cache behavior still limits what a distant
renderer camera can activate. None of these future mutation contracts is claimed
implemented or newly tested by the observation build.
