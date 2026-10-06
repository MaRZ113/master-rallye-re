# Vehicle registry profiles are independent

The Broker family admits only compatible observation layout. Registry semantics come from a separate detector and data table.

| Registry | Proven records | Detection |
|---|---|---|
| `pristine` | Canonical stock IDs 0–24; ID25 reserved/uninitialized; ID26 invalid | Exact committed pristine build profile |
| `merc-id26` | Stock IDs plus Trooper ID25 (T3/local11) and Mercedes ID26 (T1/local7) | Exact four-window forward/reverse hook and helper fingerprints |
| `unknown` | No ID/class/type assumptions | Default for family-compatible builds with no complete registry fingerprint set |

The four `merc-id26` fingerprint windows cover the T1/local7 forward hook/body and ID26 reverse hook/body. The hashes and VAs are stored in `research/r-observatory-modded-builds/registry-profile.json`. The current tracked v1 binary passes them. The v2 target binary is absent from this checkout, so detection for it is pending direct execution of the audit command.

Generic `check-broker` accepts structurally valid capture paths and reports raw CarIDs without class claims. `check-vehicle` requires a recognized registry and verifies CarID, class, family/type, participant identity, and materialization evidence; with registry `unknown`, it returns `UNKNOWN_REGISTRY_PROFILE` rather than guessing.

Registry tables retain the stock canonical map and add only separately proven records. Vehicle unlock/reachability and runtime actor behavior remain outside this profile detector.
