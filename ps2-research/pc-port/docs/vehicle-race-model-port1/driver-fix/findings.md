# X-Trail duplicate driver diagnosis

The private CAR conversion contains static PS2 occupants inside materials that were originally treated as interior trim. Excluding root8 helmet alone did not exclude the occupants: root0 contains both bodies and faces; root7 contains a separate head/visor insert for each occupant. Original PC driver/helmet draws remain native and are not suppressed. The user screenshot therefore shows two overlapping driver sets.

The mask is selected by exact source face topology, never by a runtime bounding box. `components.py` joins face vertices only when all three original float32 XYZ values are equal, including UV seam copies. `driver-masks.json` records the complete excluded and kept original face ordinals and SHA-256 of each ordered source-index component. It is pinned to private asset a15ee827bc93e7a7fe242d8ba2440afe1991cd06e8aeee15ce78b836e372ccac and PS2 CAR source af57572e92ce47d810666779fb60c8c178f1979feb203416131a3acc81449326.

| Root | Excluded component seeds | Faces removed | Faces retained |
|---|---|---:|---:|
| 0, underdash2 | 71,73 bodies;123,222 faces |348|221|
| 7, chair2 |6,10 head inserts|48|6|

The excluded body components sample the upper costume atlas (V=0..0.255); the separate face components sample V~0.286..0.531. Root7 head inserts have their own shared atlas island. Bounds are recorded only as diagnostic measurements. An independent front/side wireframe projection, visually inspected at `.analysis/driver-source-topology.png`, clearly shows two seated torsos, arms, legs and heads in red/orange/purple; the retained gray components are dashboard/chassis/arches, steering wheel and seats. This generated geometry image stays ignored, outside the source handoff.

Root0 steering-wheel component seed25,18 faces is retained. Root7 seed0,6 seat faces is retained. Root8,148 helmet faces was already excluded and remains excluded. No native PC driver geometry or animation is removed. Native PC driver draws16/18/19/20 occupy the same cabin but have different topology/positions; no exact face equivalence or safe animated-driver replacement is claimed.

Correction applies only to race private expanded geometry after the existing exact asset/owner admission. Original CAR asset, original positions/UVs and COMPLETE frontend behavior are unchanged. Total visible static CAR with parts becomes1436 faces, previously1832. Runtime confirmation must inspect both occupants from front/side, steering and cabin seats, then Reset and race restart.
