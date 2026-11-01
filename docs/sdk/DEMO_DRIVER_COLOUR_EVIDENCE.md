# Demo driver and race-marker evidence — V-DEF2.1

Eight ranked/research-shortlist vehicles are covered. Original registration,
localization and frontend/Results evidence is kept separate from a proposed
cross-version association. Full machine-readable evidence is in
`DEMO_DRIVER_COLOUR_EVIDENCE.json`; complete local tables remain private.
No next vehicle is imported or assigned a runtime slot by this audit.

## Findings

| Demo target | Authentic source driver evidence | Association with this Demo variant | Missing-name policy |
|---|---|---|---|
| Forester9.3.1 | **PROVEN**, PS2 Forester ID8: DARREN SUTHERLAND, category57/index8 in six tables | **PROVEN** accepted Forester correspondence and owner confirmation | Existing accepted project unchanged |
| Rav4 canonical9.3.1 | **UNKNOWN**. No qualified named Rav4 registration/driver pair; Newrav is a different family | **UNKNOWN**, no Reece Russell transfer | **REAL_FALLBACK DANIEL NEBOT**, active only in the new RAV4 candidate |
| Early WildCat8.4.1 | **PROVEN** later PS2 Wildcat ID15 / retail ID14: DREW BOWLER | **INFERRED** for earlier TOMCAT/blue geometry; not proof of its original PC driver | **REAL_FALLBACK HUGH HAINES** proposal where exact earlier identity is required; no project changed |
| NewRav9.3.1 | **PROVEN** PS2 Newrav ID13 / retail ID12: REECE RUSSELL | **INFERRED** continuity to PC9.3.1 Newrav/PICKUP; not retired Rav4 | Preserve authentic PS2 attribution with explicit version scope; no candidate created |
| LandCruiser8.4.1 | Later PS2/retail family has PHILLIPE BETAILLE, but its visible identity is TOMMEK DIRTBEAST | **UNKNOWN** for the early Toyota; same internal family is insufficient | **REAL_FALLBACK RONAN CHABOT** proposal; no project changed |
| megane8.4.1 | **PROVEN** PS2 Megane ID19 / retail ID18: JEAN LOUIS SCHLESSER | **INFERRED** early-PC continuity; both catalogs identify SCHLESSER MEGANE2001 | Keep original PS2 evidence distinct from early PC dispatch; no candidate created |
| Tata9.3.1 | **PROVEN** PS2/retail Tata ID2: TESSA BAMFORD | **INFERRED** to PC9.3.1 Tata ID10 / SAFARI; IDs must be remapped | Authentic PS2 attribution, no claim of a real-world driver or confirmed PC dispatch |
| Rav4Alpha9.3.1 | **UNKNOWN**, no independently qualified registry identity | **UNKNOWN**, not Newrav | **REAL_FALLBACK DANIEL NEBOT** proposal only; no alpha import |

`PROVEN` source names above mean the original executable actually binds that
name on the named platform. `INFERRED` continuity is not an `ORIGINAL` PC-Demo
assignment. The workflow rejects automatic ORIGINAL assignments from an
unproven name. Only the RAV4 fallback is installed in a newly generated private
candidate; every other row is research metadata. Any subsequently established
original identity takes precedence without deleting fallback history.

## Original race-marker values

These are exact source floating-point values, not sampled body-paint colors.

| Family | PS2 RGB (alpha1) | Transfer to selected Demo variant |
|---|---|---|
| Forester | 0.91796875, 0.29296875, 0.36328125 | Authentic PS2 Forester; accepted Forester marker is not changed |
| Wildcat | 0.46875, 0.6484375, 0.828125 | INFERRED for early8.4.1 geometry |
| Newrav | 0.72265625, 0.14453125, 0.171875 | Authentic PS2 Pickup; never copied to retired Rav4 |
| Landcruiser | 0.0859375, 0.43359375, 0.26171875 | UNKNOWN for early Toyota because later visible identity differs |
| Megane | 0.1328125, 0.25390625, 0.5 | INFERRED early-PC continuity |
| Tata | 0.8671875, 0.875, 0.75 | INFERRED PC9.3.1 continuity |
| Rav4 / Rav4Alpha | UNKNOWN | Existing SDK fallback0.25,0.55,0.85,1 retained and labelled UNKNOWN |

The static evaluator recovers all29 initialized PS2 markers. The bounded retail
reader recovers23/25 initialized markers; Bruno and Icecream remain unqualified
by that narrow immediate-store reader and are outside the ranked shortlist.
The retained JSON includes exact corresponding retail floats. For example,
retail Newrav is0.6981132030,0.1396226436,0.1660377383,1, different from PS2.
No normalization to255, paint inference or global color replacement is applied.

Both PC Demo constructors use0x24-byte records and do not initialize the later
RGBA tail. This establishes **UNKNOWN in these inspected constructors**, not
proof that the entire old game has no runtime color mechanism. PS2's0x34-byte
record stores RGBA at+0x20..+0x2c; retail PC uses+0x24..+0x30. Raw PS2 records
cannot be copied. Qualified values feed the existing `race_colour_rgba`, native
VehicleRecord emitter and editable Workshop marker controls.

## Native and resource evidence

The source JSON pins all four original executables by SHA, file size, addresses
and original table offsets. These are research pins, not new runtime admission
restrictions.

* PC8.4.1: registration0x447870, record initializer0x447f10,26 initialized rows.
* PC9.3.1: registration0x44d360, initializer0x44df00,27 rows. REA/Ghidra12.1.4
  independently reproduces its original argument sequence and0x24 stride.
* Retail: registration0x458e70..0x4598cc, initializer0x45a0b0,25 explicit rows
  in this range. Do not mistake the26-record allocation or the separate hidden
  Trooper qualification for26 initialized calls in this function.
* PS2: existing read-only Ghidra EER project, exact `r5900:LE:32:default` and
  canonical ELF SHA checked; registry0x116f88..0x117af0, initializer0x118638.
  Rabbitizer1.16.2 `InstrCategory.R5900` independently checks771 original words.
  The bounded evaluator observes register/stack/FP-bit moves and delay slots;
  two explicitly identified calls are mocked. It is static initialization
  evidence, not PS2 emulation or gameplay.
* PS2 localized pointers may point inside a longer string: the reader preserves
  these references. Requiring a pointer to the start of a maximal printable
  string previously missed valid entries such as PICKUP.

The PC Demo category57 tables contain a **12-driver list**, including player
labels, rather than the later vehicle-indexed driver table. For example, index8
would yield VLADIMIR STRAKHOV, not Forester/Darren. Even retail has conflicting
legacy/category records at index8; alternatives remain explicit. Six PS2 tables
consistently bind Forester8/Darren and Newrav13/Reece. Neither numeric index nor
an isolated string authorizes a cross-build assignment.

Original PC XML was inspected recursively: the remaining9.3.1 test scene has
Forester with different AI DriverIDs0 and9, while Results consumes its dynamic
NameList. These are test-scene defaults, not canonical historical drivers.
REA confirms PC NameList publishers0x4657b0/0x465870; PS2 native publisher is
0x135a40. The original Results XML binds `Frontend/RaceResults/NameList`.
No fixed original driver binding was recovered for retired Rav4 from these
paths. Two malformed original8.4.1 files under `DataScene/old` are explicitly
unparsed (`Default.xml`, `SceneBug2.xml`); their raw files remain untouched.
Unresolved empty/global registry names are not renamed to Rav4 by inference.

## Real fallbacks and editing

* **Daniel Nebot:** contemporary [Nissan Dakar2003 event report](https://au.motorsport.com/dakar/news/dakar-nissan-stage-ten-report/1013503/)
  establishes him as driver of Toyota280; [Le Monde,14January2003](https://www.lemonde.fr/archives/article/2003/01/14/accident-mortel-et-explosion-d-une-mine-sur-le-dakar_4270403_1819218.html)
  independently confirms Toyota/driver. A [secondary vehicle catalog](https://www.webcarstory.com/champ.php?ch=299&resultats=2)
  identifies that entry as RAV4; its page returned403 on direct fetch, so that
  model claim remains secondary search-index evidence. No original-game,
  #263 livery or exact chassis identity is asserted.
* **Ronan Chabot:** [Toyota France's own release](https://media.toyota.fr/toyota-france-competition-engage-un-hilux-sur-le-dakar-2016-avec-ronan-chabot-et-gilles-pillot/)
  documents production Land Cruiser Dakar entries starting2003. This is a
  period/manufacturer-appropriate proposal, not an original Demo identity.
* **Hugh Haines:** [Historics Auctioneers' Wildcat200 listing](https://www.classicdriver.com/de/car/bowler/wildcat-200/2001/863943)
  identifies the off-road rally driver as its first registered owner in May2001.
  This supports a period Bowler association; later2006 successes are not
  presented as1996–2003 results or as an exact Wildcat100 match.

RAV4's manifest stores `driver.value=null` separately from
`driver_assignment.kind=REAL_FALLBACK`, credentials and URLs. Workshop's existing
**Driver / Results Name** field, Apply, Undo, Redo and Restore remain the edit
path. It is a fixed presentation name, not a new AI DriverID or behavior change.
`historical-identity.json` records the baseline evidence; editable overlays do
not rewrite original evidence. Later recovered original data wins during a new
manifest restoration. Accepted Forester and other vehicles are untouched.

Reproduce locally:

```powershell
python tools/audit_demo_identity.py --config research/vehicles/sdk/restorations/demo-identity-corpus.json --output .research-output/vehicles/v-def2/identity-new.json
```

The input paths are configurable; original hashes and bounded code anchors must
match the selected evidence profile. Outputs are fresh, private and outside
original source roots. Full tables, Ghidra exports and instruction words stay in
ignored private research directories, outside source-only archives.
