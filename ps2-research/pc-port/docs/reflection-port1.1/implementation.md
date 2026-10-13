# Bounded reflection implementation

The audit established that the previous exact-target override worked, restored
its four native changes and changed hood/roof appearance. It did not establish
why the original PC highlight weakened: both the image and COLOROP changed.
This iteration isolates them and implements the original writer's second image
term as an explicit PC approximation.

`reflection_pilot.hpp/.cpp` add strict modes0–4 and COLOROP/texture mask3/2/1.
Only selected transaction slots are read, retained, attempted, rolled back and
restored. Failed calls are treated as potentially mutating. Mode0 produces no
request and no image/GPU capture. Mode3 needs no local original image. Modes1/2
use the same original-source weighted image. The geometry/classifier functions
are byte-identical to the previous built source; the compact witness preserves
that hash independently of this iteration's regenerated stage.

`reflection_capture.hpp/.cpp` own an optional private DEFAULT-pool copy texture
and64x64 target. They verify that the source is the main backbuffer, non-MSAA,
X8R8G8B8 orA8R8G8B8, with compatible capabilities and a16MiB copy ceiling.
POT/square/aspect limits are honored. NativeCopyRects transfers source pixels;
two native TL strips compose the private target. First: existing weighted ENV.
Second: vertically flipped framebuffer RGB multiplied by96/255, then ONE/ONE
addition. No vehicle draw is replayed, and no application depth is copied.

The transaction captures42 scalar/texture slots plus original target, depth,
viewport and stream0/stride. SetRenderTarget's viewport change and UP's stream0
clear are explicitly covered. All attempted writes are restored, even if the
setter reports failure. Getter references remain held until repair completes.
Capture runs at most once per frame (success or failure); unsupported fixed
caps/formats are cached until release/Reset. No stale frame's target is returned.

`reflection_native_integration.hpp` alone joins capture/transaction with the
verified draw. Native setters update only effective state through existing
Trace hooks. Private UP submissions are deliberately not reported as game
draws to the vehicle classifier or course layer. One bounded rejection and one
successful application record per device replace repetitive identity logging.
The logs include mode/mask, source format/size, copy and restoration HRESULT,
private composition count, exact geometry/resources, original colorop and
native vehicle-draw HRESULT.

The staged-only integration patch adds the new compilation/test target and
repairs pending capture before custom viewport/presentation/material access,
native-interface escape and generated target getters. The generator patch emits
the same protections on repetition. Frozen baseline files remain unchanged.
Existing ReflectionScope remains outermost, and the original native55-face
draw/HRESULT remains single and intact whenever native state is safe. An
unrepairable transaction prohibits a further unsafe native draw and reports its
actual failure; it does not pretend to have submitted the original draw.

Before a real Reset all retained target references and DEFAULT resources are
released, with failed repair recorded in the draw gate. Only a real successful
Reset resumes capture; internal window-mode reset echo is unchanged. Final
device Release frees extension-owned resources first. Original textures,
coordinates, buffer uploads and classifier remain the input to the experiment.

PS2 update timing, PSMCT16 color behavior, GS body passes/grayscale, original
VU coordinate basis and visual parity remain outside this approximation. This
is a mixed-source experiment for one proven material, not a full reflection
renderer. Foliage and Turkey3 layers remain available and disabled in this A/B.
