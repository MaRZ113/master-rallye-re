# DAMAGE-FIX1: focused runtime A/B

## Confirmed candidate

User tested ec383668b403b8bd42761cb2f1544b891eef1f1569e364e81e8c38bbb19a6110:
Tata, KiaSportage, Mattserati, Simmbugghini and IceCream COMPLETE now show;
X-Trail damaged chassis retains its reflective appearance. Brief impact flicker remains OPEN.
Session14520 independently contains successful healthy/private-tree admissions with HRESULT0.

## Transition-only follow-up

The transition diagnostic changes no rendering policy. Install its DLL manually only.
Keep the same private assets and graphics settings, MSAA4x if previously used.
In [PS2Port] keep RacePS2ModelMode=1, ReflectionMode=4 and add RacePS2DamageCapture=1.
Start a fresh X-Trail race healthy, drive briefly, then cause two distinct body impacts.
Observe whether the body briefly changes shape/appearance. No timed F10 is required.
Exit normally; collect race-transition-PID-dDEVICE.jsonl plus the session JSONL.
Optionally F10 healthy/after each impact retains the existing three-frame raw capture.

The new file records at most64 success/fallback transitions AFTER the first successful
private submission; repeated stable frames do not log. It is written directly and can be
read while playing. No framebuffer readback or new native resource polling was added.

Fields: frame, private_submitted, gate, context_gate, seen, certified,
private_tree, root (diagnostic only), refresh_flags, proxy_sha256.
Flags:1=race generation/lifetime invalidation;2=owner/tree/gap invalidation;
4=previous-frame upload tokens incomplete/stale;8=current source cache refresh.
Gate8 means certificate/environment/deformation preparation, not a proven depth defect.
A successful event means actual private draw AND state restore returned success.
These events isolate a transient fallback; they do not prove pixel-level PS2 parity.

## Existing separate checks

FrontendModelMode=0/2: compare the five newly confirmed families, rotate and switch away/back.
RacePS2ModelMode=0/1: compare same X-Trail/camera, healthy and twice damaged.
Inspect two static crew, number decal, headlight glass, OFF lamp base, brake ON/glow,
independent wheel steering, then window Reset. Do not infer these from body-only admissions.
WOOLDAND and UFO remain explicit Stock; their unresolved shader contracts are unchanged.
Diagnostics OFF by default. No automatic deployment.
