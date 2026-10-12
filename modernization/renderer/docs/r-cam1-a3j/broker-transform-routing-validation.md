# R-CAM1-A3j.2 — Validation and handoff

## Validation status

- Exact-build SHA-256 matched the documented pristine retail target: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- PE identity remains PE32 / I386, timestamp `0x3C02695D`, ImageBase `0x00400000`, entry VA `0x005C4602`.
- Static trace connected reset-manager key selection, Broker payload, adapter backing pointer, physics-controller owner field, flag/matrix reads, and chassis pose call chain.
- Runtime validation: **not run and not needed to answer the routing question**. No game was launched and no reset was triggered.
- No code, executable, existing A3j.1 source document, or runtime state was modified.

## Pass/fail statement for this phase

**PASS — Broker transform routing is proven statically.** The reset writer resolves `Controller/CarN`; its adapter payload points to `P`; the physics controller stores the same `P` at `O+0x74` and reads the reset flag/matrix from it before the native chassis pose path.

**NOT A TELEPORT PASS.** Physics-state completeness and safe arbitrary relocation remain unproven. Do not add or exercise a Freecam teleport on the strength of this routing result.

## Preserved uncertainty

The static call chain does not determine reset-manager versus physics-manager scheduling, pause behavior, which physics tick consumes a flag, or the full consequences of a mid-race arbitrary relocation. Velocity, wheel/suspension, contact/manifold, broadphase, destination clearance, solver phase, and rollback questions remain open as recorded in the evidence JSON and A3j.1 feasibility note.

## Artifacts

- [`broker-transform-routing.md`](broker-transform-routing.md) — explanation and correction to the previous path attribution.
- [`broker-transform-routing-evidence.json`](broker-transform-routing-evidence.json) — machine-readable address and claim map.
- [`evidence-map.json`](evidence-map.json) — additive `a3j2_follow_up` entry; prior records retained.
- `research-handoff-a3j2.zip` — archive of only these A3j.2 documents and the updated evidence map.

No commit or push was made. Pre-existing working-tree changes outside this phase were preserved.
