# V-CAP3: registry finalization

## Delivered scope and evidence

V-CAP2 with 34 vehicles (ID0–33, including Evo2FourRunner) is the owner-accepted gameplay baseline. V-CAP3 adds registry-driven Extra Options pool agreement, final class ordering, and active-competition dependency protection. It does not repeat the capacity research or claim a new global engine limit.

The private candidate is `.research-output/vehicles/v-cap3/candidate`. It contains 35 records, class sizes T1=8, T2=14, T3=13. Independent authored resources are Evo2FourRunner ID33 and prepared Demo 9.3.1 HeritageNewRav ID34. Their geometry/UV signatures, physics values, CarSheet frames 38/39 and SIDE frames 36/37 differ. Geometry checks compare actual vertex/UV payloads, not renamed files. NewRav has not been gameplay-qualified in this phase.

Final T2 positions are ID34 at local index 2 and ID33 at index 13. A second derive places them at indices 8 and 1 respectively; all metadata matches the final maps, identity and competition contract remain unchanged. The relative stock/SDK33 ordering is retained. These are repeatable manifest changes, not per-ID code patches.

## Extra Options AI fix

The accepted candidate's boot log proves that the SDK roster provider registered successfully. Its generated table already contains ID33/T2/slot7. Complete native class-loop execution also includes ID33. Therefore a missing provider row or a native ID33 range check is **not** the observed cause.

The copied configuration had `Addons/Include=0` and an obsolete standalone-only comment. Randomizer's policy/weight/capacity calculations therefore used stock candidates while native physical builders used the expanded SDK pool. The implementation reconciles these two sources, rather than adding a special ID33 exception:

- Registration validates provider completeness against the active MRVC descriptor and every class against its live reverse map. Class lookups use the descriptor snapshot.
- Policy selection and physical pool filtering share one generation snapshot. The new optional `MRFilterAiPoolV1` callback intersects native materializable records with that snapshot before the existing selector runs.
- Original human exclusion, duplicate handling, participant limits, Invitation rules and Challenge handling remain owners of their original behavior. The callback never adds nonexistent models or modifies race participant counts.
- Stock mode leaves the native pool untouched, including when AI Extender is enabled. `Include=0` retains stock-only semantics for active Randomizer; `Include=1` admits registered eligible addons.
- The private package changes only copied `Addons/Include=1` and `Logging/Enabled=1`. It preserves other INI choices. `AI_REGISTRY_POOL` reports eligible IDs so random selection can be distinguished from exclusion.

This establishes a real configuration/pool inconsistency and corrects it. It does not retrospectively prove why an individual old random draw omitted ID33. The new callback still needs the narrow owner gameplay check below.

## Ordering and persistence

`capacity_profile.py` preserves the relative subsequence of ID0–32 in each class, allowing new IDs at arbitrary valid positions. `build_vehicle_registry.py` derives **all** addon `class_local_index` fields from the single final profile. Temporary canonical cloning indices never become published metadata. Existing tombstone/reactivation rules remain in force.

`competition_contract.py` writes `mr-competition-contract/1`. It fingerprints stable namespace/family/physical ID/class/retirement, mode eligibility, canonical gameplay XML values, collision payloads and the qualified native rules ABI. Texture pixels, livery files, artwork and frontend order are excluded. SHA here is a dependency-change detector, not a creative asset allowlist.

An active imported save requires its previous roster identity and matching previous competition contract. A contract change blocks the build without rewriting the source save. Old active V-CAP2 saves with no dependency baseline are not silently trusted: finish in the accepted package or perform an explicit qualified migration.

The integrated launcher checks each private launch. `competition-baseline.txt` binds both the compiled contract and exact saved bytes. Copying an unrelated active save into a fresh candidate cannot borrow that candidate's baseline. After its own resumed game exits normally with code 0, the launcher validates the result and records the new association atomically. Suspended preflight does not establish ownership of a game-generated save. A crash/nonzero exit with changed save bytes fails closed; recovery requires an explicit matching-contract rebuild/import. No save XML is edited by these guards.

`--verify-roster-state` now reports `IDENTITY_ONLY_PASS`. Full offline checking is `--verify-competition-state <save.xml> <private-runtime-bundle>`. An inactive save may create/update its baseline. Contract coverage concerns the qualified SDK gameplay dependencies, not arbitrary third-party physics/rules mods.

## Reproducible workflow

Use this worktree and the isolated Extra Options worktree `master-rallye-re-v-cap2-extra-options`; preserve other worktrees. Python must provide the project's existing dependencies including Unicorn for CPU validation; native builds use MSVC x86 and the x64 launcher toolchain.

1. Author/build an independent Vehicle SDK project using existing `mrtool.py addon project-build`. Keep model variants, materials, livery/artwork in that project. Existing unsupported native audio/shadow/mechanical contributors fail explicitly; this phase does not add those importers.
2. Add its family, physical ID, class, project/build paths and wheel configuration to the registry manifest. Keep `previous_roster`; retain previously reserved IDs. Specify each class's final ordered ID list. The actual input and reordered control input are saved beside the private candidate as `registry-build.json` and `reordered-registry-build.json`.
3. Build into a **fresh** output:

```powershell
python tools/build_vehicle_registry.py --manifest .research-output/vehicles/v-cap3/registry-build.json --output .research-output/vehicles/v-cap3/candidate-next
```

4. In the isolated Extra Options worktree, build against that exact runtime bundle:

```powershell
python tools/build_extra_capacity_candidate.py --output .research-output/extra-set1/v-cap3-next --sdk-runtime ../master-rallye-re-v-cap/.research-output/vehicles/v-cap3/candidate-next/runtime --sdk-root ../master-rallye-re-v-cap
```

This regenerates the provider, required byte preimages and the two composed Challenge hooks. The delivery's `capacity-build.json` records all code-generation inputs and hashes. Do not mix an old proxy with a newly mapped registry.
5. Prepare separate private hosts with `tools/package_vehicle_registry_candidate.py --candidate <fresh-output> --extra <matching-extra-build> --renderer-host <accepted-private-renderer-host> --registered-ai`. This never installs into a working game. `private-hosts.json` records binaries and copied INI overrides.
6. Use the generated launch scripts. The launcher loads the computed extension once at startup; it is not a hot-resize registry. Allocation follows profile/layout/overflow checks, not a hardcoded target of 35/64/128/256. SDK33 stays supported.

## Validation and qualified bounds

| Evidence | Result | What it establishes |
|---|---|---|
| Owner V-CAP2 gameplay | 34 records accepted | Existing ID33 gameplay baseline, SDK alone/Renderer; old Extra Options AI issue remains the targeted delta |
| Focused SDK suite | 63 passed | Ordering, roster/network/routes, UI assets, damage, identity and native save guard |
| Contract suite after final validation tightening | 4 passed | Active dependency failures, formatting/visual independence, interleaving |
| Extra Options Python suites | 33 run, 31 passed, 2 existing optional skips | Generated selector frame/flags/stack, plan and bridge composition |
| x86 production harnesses | PASS | Live provider completeness/classes, actual AI callback, Include0/1, Stock, Invitation; existing native options and multi-page SDK verification |
| Complete native AI loops | 9 cases each for accepted34 and candidate35 | Actual emitted detours and native class loops; vector/progress services mocked; one/two human exclusions |
| Composite core CPU | 70 map queries, 3 lifecycle routes, 2 initializers, invalid indices rejected | Exact emitted x86 addressing for the 35-record composite; native constructor/allocator mocked |
| Boundary callback tests | 127/128, 254/255, 255/256 and 512 | Provider/class/pool integer addressing only, not hundreds of independent vehicles in game |
| Four suspended process preflights | PASS, 3.85–4.23 s | Image/preimages, descriptor35, RX extension + two RW/NX pages; **game thread not resumed** |

No new game session was run in this phase. Gameplay-qualified capacity remains **34**, while the private **35-record** candidate awaits targeted owner acceptance. The global maximum is unknown. Old byte-based network/replay/save consumers retain the separately documented V-CAP2 admission boundaries; component tests above do not qualify those modes for high IDs. T1/T2/T3 only; no new classes or network protocol widening.

The candidate builds 8062 resources. Measured full build: 60.97 s including launcher compile (composition 12.25 s, copy 7.06 s, resource verification 34.81 s). Order-only derive: 11.08 s. These are local measurements, not gameplay performance claims. The builder reuses its just-verified bundle while compiling the launcher to avoid an unnecessary third full archive hash pass.

## Narrow owner checklist

Use `Launch-input.cmd` and `Launch-both.cmd` in the private candidate; do not copy DLLs into installations.

1. Quick Race, T2 or Full Randomizer, `Addons/Include=1`: inspect `AI_REGISTRY_POOL` for eligible IDs33/34 and run enough starts to observe actual opponents. One random grid without a particular car is not evidence of exclusion. Keep existing opponent limits.
2. Switch Randomizer to Stock: check the native expanded selection still works; retain current AI Extender participant configuration.
3. Verify T2's third item is NewRav and final item is 4Runner, distinct names/CarSheet/SIDE, correct physical cars. One short NewRav player/AI/Results check qualifies its newly composed resources.
4. Start/save a fresh competition, exit normally through the launcher, restart and confirm admission. The offline suite already covers wrong dependencies/missing or borrowed baseline, with unchanged save bytes.

There is no request to repeat atmosphere, lighting, Ghost, MODEL, GENERAL Tires or the accepted V-CAP2 campaign matrix. Both DLLs remain independent; no Renderer code was changed. Final source/build manifests, file SHA-256, preservation checks and validation logs accompany the private candidate. No files were installed or published.
