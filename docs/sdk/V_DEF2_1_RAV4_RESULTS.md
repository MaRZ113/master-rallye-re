# V-DEF2.1 — RAV4 retail physics and historical identity

## Changed

The owner accepts V-DEF2 RAV4 visuals/integration and rejects its hybrid handling.
The new private candidate uses the existing Heritage → Workshop → CMD pipeline
and an independent **complete retail Newrav** family named DefRav4. No overrides,
owned tyre table, ride datum or collision-fit substitution is applied.
All147 vehicle fields and26 player setup fields match the clean retail donor
after the family-prefix change. The previous hybrid differs at96 vehicle
fields. All121 historical Demo8.4.1 values remain pinned and recorded as
**inactive** evidence; their previous compatibility policy remains in the
per-car manifest and Git history.

No other vehicle family changes. Slot31/T2 local11 and the existing32-record
candidate layout remain unchanged; no new capacity or vehicle is added.
The proxy SHA startup gate remains removed. Installed wrappers are untouched.

## Measured consistency and remaining WARN

| Item | Authentic source geometry/rest assembly | Complete retail Newrav physics |
|---|---|---|
| Wheelbase | 2.553561m | 2.450000m; previous hybrid2.400000m |
| Track, both axles | 1.495122m | 1.600000m |
| Maximum local wheel radial extent in YZ | 0.39050578m | Contact radius0.380000m |
| Hub X | −0.748669 / +0.746453m | No geometry shift applied |
| Hub Z | −1.263246 / +1.290315m | No geometry shift applied |
| Mass | Historical parameters preserved as evidence | Stock1300kg |
| Front / rear spring | No inferred source solver transfer | Stock33500 /37500 |
| Front / rear damping | No inferred source solver transfer | Stock2100 /2400 |
| Bounce / droop | Runtime settling not measured offline | Stock0.3 /0.1m, both axles |

The complete clone **does not eliminate the alignment discrepancy**: its axle
spacing remains0.103561m shorter than the source rest assembly (previously
0.153561m). Track is0.104878m wider; radial contact is about0.010506m smaller
than the mesh's maximum radial extent. Source hub midpoint isX−0.001108,
Z+0.0135345m. These measurements do not establish exact runtime contact points,
suspension settlement or a justified body offset. No symmetric-axle assumption,
new wheelbase override, body scaling, mesh edit or automatic arch fit is hidden
inside the clone. The owner should compare handling/contact with this baseline
before a separately explicit wheel-fit authoring adjustment.

The three native models, wheels, intact/broken glass, OFF/ON lamps, textures,
frontend art and HUD artwork are unchanged. All258 DX/DXT resources in the
32-record package match the accepted visual candidate byte-for-byte. Of381
resource-root entries,380 are identical; only DataGame/vehicles.xml changes.
The native extension/plan additionally changes the fixed RAV4 Results name;
this is outside the loose-resource geometry set.

## Historical identity

See `DEMO_DRIVER_COLOUR_EVIDENCE.md` and its JSON for all eight shortlist cases,
original registration/localization evidence, exact PS2 marker RGB and confidence.
Retired Rav4's original driver and marker remain **UNKNOWN**. Reece Russell is
not assigned: original PS2/retail Newrav/Pickup bindings are a different family.

The new RAV4 display uses **DANIEL NEBOT — REAL_FALLBACK**, a verified Toyota
Dakar2003 driver, following the owner's fallback policy. Original null identity,
historical credentials and sources remain separate. The existing blue SDK
marker is explicitly an UNKNOWN/SDK_FALLBACK, not recovered original paint or
marker data. Workshop's existing Results-name and marker controls remain editable.

## Validation and private delivery

Private root: `.research-output/vehicles/v-def2/physics-identity`.

* `release/Open-Restoration-Workshop.cmd`: persistent editable project.
* `release/workshop/builds/first/candidate/Launch-SDK-Roster.cmd`: new owner test.
* `delivery-validation.json`: exact retail-clone and roster/source checks,32 native record/ABI
  emulation. `release-validation.json` also records two actual Workshop builds;
 258 DX/DXT resources deterministic.
* `physics-and-resource-proof.json`: exact clone,96 field differences, geometry
  measurements and resource-root differences.
* `historical-evidence.json`: complete original PC/PS2 table and XML inventory.
* `focused-delivery.json`, `workshop-edit-validation.json`,
  `launcher-validation.json`, `current-proxy-validation.json`,
  `protected-after.json`: focused checks and preservation.

1570 pre-existing protected files,72 restoration source pins, four original
executable corpora and208 original scene XMLs verify unchanged. The installed
proxy changed externally during this task; no task operation wrote it. Its
before/after hashes are diagnostic only in protected-after.json. The current
proxy passes the unchanged launcher environment checks with hash_gate=disabled.

Focused regression is used for this scoped revision. The previous full suite
remains historical evidence; it is not claimed rerun here. Native preflight,
mocked allocation and CPU ABI emulation are not D3D8 gameplay qualification.
The owner-confirmed visual baseline remains accepted; **handling/contact and
the new Results name for this revision remain pending owner verification**.
No new D3D9 fidelity claim is needed for byte-identical visual resources.

Reproduce into a fresh private directory:

```powershell
python tools/restore_demo_vehicle.py --manifest research/vehicles/sdk/restorations/rav4-931.json --roots .research-output/vehicles/v-def2/roots.json --roster-config .research-output/vehicles/v-def2/accepted-31.json --output .research-output/vehicles/v-def2/rav4-retail-new
```

## Owner checklist

1. Launch the **new** CMD above, select Toyota RAV4; retain the old candidate
   as rollback. Existing Forester and roster must still be selectable.
2. Compare acceleration/braking, steering, tyre wear and suspension over bumps
   against retail Newrav. Use the same track/setup for the comparison.
3. Inspect front/rear wheel centers, steering extremes, full bump/droop and
   ground contact from both sides. The remaining10.36cm wheelbase difference
   is known; do not treat this clone as an exact geometric fit.
4. Confirm the accepted visuals, damage, glass, rear lamps and separate HUD
   icon remain intact. Verify DANIEL NEBOT as the intentional fallback label.
5. Complete a race, inspect Results, return to the menu and re-enter. These
   lifecycle checks are pending for this exact revision.

Stop after this candidate and identity/color audit. No next vehicle, roster
expansion, physics auto-fit, original-asset edit, mod installation, push or release.
