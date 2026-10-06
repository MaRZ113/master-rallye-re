# Raw-resource device escape audit

**Decision: SAFE_TO_KEEP_RAW for the mapped pristine-retail renderer paths;
STATIC_INFERENCE, conditional on human coverage checks.** No reviewed resource
GetDevice→render/state-call chain was found. Resource wrapping is not justified
by the current evidence. This is not an exhaustive proof for every unused linked
function, alternate build, overlay or external helper.

All children stay native: textures/base textures/cubes/volumes, VB, IB and surfaces.
Their methods, QI, AddRef/Release and Lock/Unlock remain native. Their own GetDevice
would return the raw device and could bypass this proxy. The proxy deliberately
does not invoke it internally or return a raw root/device through known QI.

The review reused R-GFX1's texture, geometry, COM callmap and indirect-call exports,
then queried the installed ghidra-bridge exporter with Ghidra12.1.4, the newest
installation on D:. The existing project was opened read-only; an in-memory
analysis transaction was rolled back; nothing was saved. New raw exports/settings
are ignored under this phase's `.analysis/child-audit/`.

| Reviewed seam VA / RVA | Evidence and consequence |
|---|---|
| Texture create 0x005589CD / 0x001589CD | Native CreateTexture result enters handle/cache; GetSurfaceLevel obtains upload surface, with no device recovery required |
| Upload 0x005D8982 / 0x001D8982 | Surface +0x20 GetDesc, +0x24 LockRect, +0x28 UnlockRect; CPU image conversion. No +0x0C GetDevice |
| Mipmap 0x005D9281 / 0x001D9281 | Texture GetLevelCount/GetLevelDesc/GetSurfaceLevel, surface filtering via005D902F, Release. No device recovery |
| Surface filtering 0x005D902F / 0x001D902F | Source surface GetDesc/LockRect/UnlockRect→destination upload; no device recovery |
| Linked texture helper 0x005D9794 / 0x001D9794 | Receives device explicitly, creates texture via that device, uses surface helpers, optionally UpdateTexture on original device |
| Shared VB/IB manager 0x00587070 / 0x00187070 | R-GFX1 resource lifecycle uses cached device for creation/binding and child lock/release; no reviewed GetDevice chain |
| Dynamic ring and mapped draw owners | R-GFX1 creates via renderer device, locks resources, draws via engine device accessor/cache; no child recovery required |
| Sprite state setup 0x005DFD97 / 0x001DFD97 | Takes device explicitly, AddRef/caps/state blocks/Set* use that argument; not a child escape. Game reachability remains unproved |

The old all-program Ghidra listing contains 454 indirect +0x0C calls. An offset
alone is not an interface identification. Targeted receiver reviews excluded:

* VA0x005815FC / RVA0x001815FC and other +0x0C calls in00581590:
  CoCreateInstance/video graph, filters and enumeration (DirectShow), not D3D children.
* VA0x00582B15 / RVA0x00182B15: video sample/buffer retrieval, followed by pixel
  conversion and the video device's surface workflow; not child GetDevice.
* VA0x0054138D / RVA0x0014138D and0058F100/0058F115: input-device creation/caps,
  setup/data format/cooperative level through00571400; not D3D resources.
* VA0x005DE5B7 / RVA0x001DE5B7: linked helper uses caller stack cleanup
  `POP ECX; POP ECX` after the +0x0C call. That is incompatible with native
  STDMETHODCALLTYPE GetDevice's two-argument stdcall stack contract; no recovered
  device is used afterward. Receiver semantics otherwise stay unnamed.
* Linked005E311F +0x0C calls retrieve assembler buffer data; validator-name lookup
  is explicitly present. They are not D3D resource GetDevice calls.

Runtime diagnostics include per-frame BeginScene/EndScene/Present/draw counts,
caller-module/RVA coverage and warnings for unexpected supported QI or parent
mismatch. `bypass_suspected` flags a Present without BeginScene/EndScene. Missing
mapped draw families, a visible scene with zero draws, or native render activity
unexplained by captures is a failure to investigate, not a semantic classification.

These diagnostics can reveal likely bypass but cannot detect every balanced raw
draw or state write. If evidence establishes an escape, the next correction in
this phase must wrap the affected child interface and preserve its identity/
GetDevice route; do not compensate by changing game memory or inventing state.
Raw-resource Release is unobserved, so metadata is explicitly last-known creation,
not an authoritative lifetime record. Serial keys are `(device, creation_serial)`.
