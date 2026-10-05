# Vehicle addon roadmap after F.2

R5V-F.2f addresses Race Options presentation only. ID26's current test-only unlock is not the final add-on unlock architecture. The Mercedes sound-family/fallback path is also unresolved and is not closed by the gameplay smoke.

The agreed next order is:

1. **R5V-G.1 — Vehicle Unlock Architecture.** Trace and replace the bounded test-unlock policy with a dedicated add-on unlock model.
2. **R5V-G.2 — Vehicle Audio Identity / Sound Family Architecture.** Trace CarID-to-sound selection and support an independently configurable stock sound family/donor for an add-on vehicle.
3. **R5V-H — AI Opponent Vehicle Pools.** Add eligible add-on identities to AI only after the prior identity systems are defined.
4. **R5V-I — Multi-slot Registry Expansion.** Qualify the additional T2 vehicle/class path as a required proof point.
5. **R5V-J — Generic Addon Vehicle Tool / SDK.** The generic SDK is not complete until it passes an independently registered T2 addon vehicle, in addition to the existing qualified workflows.

F.2f does not begin any of these phases.
