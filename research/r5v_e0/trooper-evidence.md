# Trooper evidence baseline

| Item | Source/build | Evidence | Status and limit |
|---|---|---|---|
| Retail physics family | retail `Data.sma`, `DataGame/vehicles.xml` and `Modifications.xml` | Existing config parser plus family semantic validator | `COMPATIBLE`; 147 fields, 120/120 fixed required fields, 13 Player1 overrides |
| Model source | demo-9.3.1 Trooper revision-131 snapshot under beta `inputs/!other_research/9.3.1_dxTrooper` | SHA-256 locked by R-COOKER1.1 evidence | Exact tested source snapshot; not the similarly named extracted folder whose DX hashes differ |
| Converted model | revision 131 → 135 with `dx_revision_upgrade.py` | Deterministic output hashes and parser/index validation | All 3 files pass; no errors or warnings; geometry, index order, collision, global table and trailing bytes preserved |
| Texture source | demo-9.3.1 `DataGx/Vehicles/Trooper` | Every DX texture reference resolved; each needed DXT parses | 24 referenced files staged unchanged; one unused source DXT omitted |
| Collision | Trooper `car.dx`, tag101 | Current R4G parser/writer invariants and R5V-E0 topology checks | Structural PASS; runtime collision behavior is not separately confirmed for ID25 Trooper |
| Prior runtime evidence | R-COOKER1.1 retail test | Owner report covers Trooper `complete.dx`, `car.dx`, `wheel.dx`, appearance, and vehicle operation | Applies to those converted resources in a prior Trooper path, not to their new ID25 binding |
| Current P0 report | Owner message, 2026-09-30 | Slot confirmed, vehicle shown, other vehicles not replaced | Limited owner report; executable hash, texture detail, stats, menu stability and debug capture unreported |

Build identity is explicit: this is `demo-9.3.1/Trooper` plus retail physics.
The retail archive is the source for physics; the beta branch's exact hashed
revision-131 snapshot supplies the DX bytes used by the already runtime-tested
conversion; the supplied demo-9.3.1 tree supplies DXT files. Vehicle identities
from other builds are not merged.
