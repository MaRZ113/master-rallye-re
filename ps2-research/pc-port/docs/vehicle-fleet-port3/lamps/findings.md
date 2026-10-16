# Fleet PORT3 lamp source contract

Scope: all 25 paired playable CAR families, including Ufo. This report does not infer wheels for Ufo. No original files, renderer sources or native memory were changed by this audit.

`generate.py` rechecks original protected PC CAR hashes and original PS2 CAR bytes from hash-verified PackFS inputs. It preserves ordered material texture records, loader mode, shader uncertainty, original PS2 vertex RGBA words, original GXI hashes, exact native geometry and position/UV hashes, and source UV/index topology. Historical record numbers are source-table labels, never persistent runtime identities.

## Coverage

* ON_CORE: **25/25 exact native profiles**. All original PS2 primary BREAKLIGHTSON resources have SHA-256 `fd4c121f962ef4e9ee7491666c71b65db008d6ca276d9188881c0b35c7846131`. This is the already installed `PS2KiaBrakeOn.gxi`; reusing those original bytes for other proven source profiles needs no invented color filter.
* ADDITIVE_GLOW: **25/25 existing exact source profiles** remain valid. All original primary BREAKLIGHTSONGLOW resources have SHA-256 `b6350f92f674bf2b63200ce4bb39c0c26f03fd99856ac0b89e7fc0797861af09`. Keep the existing RGB fade/additive transaction and Terrano's additional normal/attribute check.
* Reflective OFF: **21/25 source pairs** retain the previous exact registry. Bruno has a UV revision; Jump and Mattserati have source geometry revisions; Ufo has no independently verified conditional OFF carshiny/mixed pair. Do not classify these entire lights as reflective by name.

Jump ON source geometry differs by up to 0.00240135193 from PS2; Mattserati differs by up to 0.00802320242. Both retain exact PC geometry and use exact native fingerprints plus exact source UV triangle correspondence. These profiles permit source texture fidelity, not an unreported PS2 lamp mesh replacement. Runtime matching uses zero tolerance; these are measured original asset differences, not relaxed admission.

## Mode and color semantics

Every ON source has generic final loader mode 1; every glow source has mode 14. The authored `$shader(carbrakelight)` / `$shader(carbrakelights)` handler remains untraced in the earlier executable contract, which is explicitly retained as UNKNOWN. ON secondaries split into ordered `perspex-tga` and `lightshine-tga`. Substituting the original primary GXI while preserving native blend/secondary behavior is a bounded material approximation, not proof of full GS parity. The original ON GXI's red/orange RGB is the demonstrated Kia color fix; changing global lighting or all red surfaces is unsupported.

## Required live gate

Source equality alone does not authorize damage. Require current same-frame family/chassis owner and WORLD, current exact healthy source, complete mirror and nonzero VB/IB generations/revisions, live material-vector/token and texture/generation. Bind retained healthy UV/index topology to that exact race lifetime/device/instance/packet/model. For a verified native private clone, allow deformed XYZ only while UV/index topology, original material-vector/token and texture-generation remain unchanged. Reject unknown topology, changed resources, cold damaged admission, unrelated owner, ambiguous profile or unsupported native layout with an explicit reason.

Kia has user runtime evidence for the retained clone path. Other families remain runtime qualification pending; shared texture names cannot supply missing owner or clone proof. The working Kia class should remain intact while reusable family-bound continuity is integrated. Preserve fallback before any draw transaction starts. A matching ON record is not authority to suppress a whole CAR.

## Fixtures and tests

`fleet_on_registry_draft.hpp` contains 25 metadata-only native ON profiles. `.assets/vehicles/port3-lamps-compact.bin` contains 774 original source records adapted to explicit FVF102/stride20 for hashing-adapter tests: 25 ON positives, 25 glow positives and 724 other source negatives. This is an ignored local fixture, not a claim every live family uses FVF102. Native FVF112/152 should be normalized only for identity inspection; never rewrite the actual native submission solely to fit a fixture.

`python -m unittest discover -s ps2-research/pc-port/docs/vehicle-fleet-port3/lamps -p 'test_*.py'`: 5 PASS, including exact ON-vs-all-other-source rejection. The fixture is intentionally absent from clean handoffs; that one test skips if original local corpus data is unavailable. Generated metadata and four independent registry tests remain portable.

Runtime acceptance must remain family-specific: same-session healthy brake OFF/ON, rear-damaged OFF/ON, Reset/MSAA, draw/restore HRESULTs and current owner/generation diagnostics. No new family is user-runtime-confirmed by this source audit.
