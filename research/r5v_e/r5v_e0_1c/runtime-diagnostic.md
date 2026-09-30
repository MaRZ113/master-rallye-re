# Runtime tint diagnostic status

## No candidate was produced

The requested red Player1/Car0 tint diagnostic was not built. The allowed patch order starts with a producer input/table entry, `Race/Car0/Colour` creation value, or participant-specific property write. None of those write sites or their semantic owner is known. Patching a generic HUD colour setter or the marker renderer could affect every participant or unrelated HUD objects, so there is no evidence-supported narrow patch point.

Accordingly, none of the following exists for E0.1c:

- `MRallye_slot25_trooper_colour_test.exe`
- patch manifest
- binary diff
- human test instructions
- candidate SHA-256

The existing ignored scratch directory `research-output/r5v_e0_1c/debug-run/` contains prior debugger setup copies, not a tint candidate. No files in original retail installation paths were changed.

## Required evidence before a diagnostic

Capture the retail consumer reading Car0 during a real race, record the four values, and identify the property backing storage. Then break on the specific write/initialization path and trace its caller to a Player1/participant source. If that source is a small participant palette, record every entry and prove which index selects Car0. A candidate can then change only the proven Player1/Car0 value.

The eventual human test should reuse the runtime-confirmed Trooper + SmallCarSheet29 baseline. Expected unchanged systems are Trooper model, physics, collision, race/results icon, and the E0.1b frontend stat profile; only the bottom progress marker should change tint. This expected result has not been tested because no candidate exists.
