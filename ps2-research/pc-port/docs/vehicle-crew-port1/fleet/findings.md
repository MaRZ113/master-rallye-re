# Fleet expansion source gate

The canonical PS2 archive inputs were verified, and all 29 COMPLETE and 29 CAR
payloads were independently decoded again. All 29 COMPLETE models have flat root
mesh trees, with 13–27 mesh records. Terminal 102 auxiliary data remains handled
by the existing proved reader; no relaxed parser or guessed trailer was added.
The 26 paired PC COMPLETE and CAR resources were decoded from the protected
retail corpus. Each compiled record has an exact geometry signature and ordered
texture slots in `coverage.json`.

WOOLDAND is paired with PC Forester. PS2 FORESTER is deliberately unpaired and
remains a separate additional vehicle. MOONBUGGY and TANK also have no verified
PC replacement owner in this corpus. The earlier CAR audit's name-only
FORESTER→Forester pairing must not be inherited.

## Prepared COMPLETE resources

`convert_fleet_complete.py` reuses the established PS2VEH01 validator and X-Trail
vertex/strip/GXI conversion primitives. It created 22 local private runtime
assets initially. Native decoder validation then identified two unproved
explicit-shader primary bindings (KiaSportage/Tata); the admitted registry now
contains 20 assets (13,184,732 bytes total). The two rejected ignored artifacts
are preserved, not deleted. Outputs reside under the already ignored `.assets/vehicles/`.
No original geometry or texture bytes are placed in Git, this folder or a
distributable handoff. `frontend-profiles.json` and the generated draft C++
registry contain only hashes, counts, dimensions and source identities.

All 20 admitted profiles have source anchors unique among all 26 paired compiled COMPLETE
resources. The maximum PC source record count is 26; the maximum PS2 mesh count
is 24; the maximum texture count is 29. These bounds fit the implemented fixed
capacity 32 owner certificate and 64-entry rejected-probe cache without scene-wide scanning. Current live owner,
generation, transform and complete suppression checks remain mandatory; source
uniqueness alone is not runtime admission.

The original missing-shader constructor path selects mode 0. Authored primary
textures are retained and inactive secondary slots are cleared; only a missing
primary receives the exact original default GXI proved in PORT2. An explicit
unknown shader is rejected rather than silently interpreted as mode 0 or 3.
The per-mesh `mixedReflection` flags follow the existing source-backed material
contract: mode 3 whose effective secondary is `rendertarget64x64` uses the mixed
reflection source; rubber preserves its authored secondary. No X-Trail wheel or
helmet ordinals are generalized to other vehicles.

Precise COMPLETE exclusions:

| Source | Reason |
|---|---|
| MATTSERATI, SIMMBUGGHINI | Source mode 2 is not implemented by the private model transaction. |
| KIASPORTAGE | Mode-3 node 379852 has missing primary and authored secondary 14; its explicit-shader fallback is not proved. |
| TATA | Mode-3 node 349913 has missing primary and authored secondary 9; its explicit-shader fallback is not proved. |
| UFO | Explicit `$shader(carbrakelight)` is unresolved, and mode 21 is also outside the transaction. |
| WOOLDAND | Explicit `$shader(crashiny)` spelling requires original fallback verification. |
| FORESTER, MOONBUGGY, TANK | No verified PC replacement counterpart; not parser failures. |

## CAR source candidates

`car-candidates.json` is a conservative per-record surface control, not an
activated fleet CAR replacement registry. Every paired CAR has some exact
unconditional surface candidates, but no all-record suppression certificate is
granted by this analysis. PC tag 7/8 named/alternative records are excluded, as
are native glow/on textures and any surface matching a conditional PS2 branch.

The important counterexample is X-Trail PC CAR record 24: it is tag 2 but contains
`breaklightsonglow`. Suppressing all tag-2 records would remove a native braking
effect despite appearing structurally unconditional. Additionally, crew can be
mixed with interior in a source record. Generic replacement must either suppress
the full corresponding crew+interior set while drawing all original static PS2
parts, or prove an exact per-triangle partition. Reusing X-Trail's crew masks on
another family is not safe. Separate wheel resources require their own current
native wheel owner/transforms; no wheel-to-chassis attachment is proposed.

## Reproduction and validation

Run from the primary worktree:

```powershell
python ps2-research/pc-port/docs/vehicle-crew-port1/fleet/inventory.py
python ps2-research/pc-port/docs/vehicle-crew-port1/fleet/convert_fleet_complete.py
python ps2-research/pc-port/docs/vehicle-crew-port1/fleet/car_candidates.py
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-crew-port1/fleet -v
```

The converter uses the previously verified 29 local `.ps2vehicle` source
representations. Missing originals must be prepared with the existing
`tools/prepare_vehicle_models.py`; it must never be replaced by a copied modern
mesh. The private runtime assets regenerate byte-identically. Focused tests:
6/6 PASS, including explicit-shader missing-primary rejection, source counts, distinct FORESTER/WOOLDAND mapping, exact
registry metadata, original-derived binary hashes and source-driven secondary
selection. Actual vehicle menu/race coverage still depends on main integration
and user runtime tests.
