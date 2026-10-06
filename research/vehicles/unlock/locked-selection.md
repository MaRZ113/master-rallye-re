# Locked selection and commit gate

## Corrected-overlay runtime result

Fresh-profile ID3 and ID26 captures from the corrected package confirm the
expected Broker state, and the human visual/input test now closes the original
defect: ID26 displays the locked thumbnail, reports `UI/Enabled=False`, and
normal accept cannot commit it. After completing the native T1 Cup requirement,
ID26 becomes enabled and selectable with its normal Mercedes presentation.
This supersedes the earlier failed UI observation, which came from a process
whose Root did not contain the overlay. That failed run remains useful only as
a deployment-history finding.

## Runtime oracle correction

The fresh-profile comparison captures are `20261006-143000_merc_not-locked`
and `20261006-143558_id3-locked`. Both report `T1CupCar1=False` and both
unlock-cheat flags false. The raw sidecar hashes were recomputed and match the
JSON metadata.

| State | CarModel | Manufacturer | Model/reason | selectedCar | UI/Enabled |
|---|---:|---|---|---:|---|
| stock locked ID3 | `-1` | `CAR LOCKED` | `UNLOCK BY WINNING 2 T1 CUPS` | `3` | `False` |
| locked ID26 in prior test | `-1` | `CAR LOCKED` | `UNLOCK BY WINNING 2 T1 CUPS` | `26` | `True` |

This disproves the prior interpretation that `FrontEnd/Network/selectedCar`
means the selected vehicle was committed. Stock locked ID3 publishes `3` while
`UI/Enabled=False`. Treat `selectedCar` as highlighted/current frontend
identity. For a locked slot, `UI/Enabled` plus observed normal-accept behavior
is the stronger commit oracle. The human separately reported that the earlier,
uncorrected widget accepted ID26 into a race; the resulting participant was
`CarID=26`, `CarClass=0`. That old behavior is no longer the locked-state
result.

## Static stock control

Retail `VehicleSelect.xml` defines stock T1 local3 / physical ID3 as `T1_Car4`.
Its AI list contains:

* AI 0 `gaFrontendDisablerAI`, driven by `T1CupCar1 OR UnlockCars OR UnlockAll`.
* AI 2 `gaFrontendXYButtonAI`, with the slot's `Enabled` field.
* AI 3 `gaFrontendButtonUnlockerAI`, with the same three paths and
  `Control AI ID=2`.

Earlier Ghidra analysis maps the unlocker constructor/configuration to
`FUN_0044BEC0`, its availability callback to `FUN_0044C060` (vtable slot 5 at
`0x006901F4`), `FUN_0045D0B0` to publishing the XY button state as `UI/Enabled`,
and `FUN_0045D930` to the positive-action gate. This correction pass does not
reopen those handlers.

## Historical deployment mismatch

The new captures pin the candidate EXE, but their dump header's resource Root
was the captured `.../r5v_f_2e/runtime/` directory. That directory had no loose
`DataScene/FrontendScreens/VehicleSelect.xml`; the generated correction scene
was stored in another output directory. The Root did contain `Data.sma` and
the qualified Mercedes runtime package. Therefore `UI/Enabled=True` and the
normal thumbnail are not evidence that the cloned XML controls fail: the exact
generated scene was not under the Root used by the process.

The corrected XML clones locked-capable `T1_Car4` into `T1_Car8`, keeps
the three gates and false frame 15, sets the unlocked frame to 3, and binds the
unlocker to XY AI 2. The new package builder stages it beside the captured
resource files in an isolated root. Only if that exact root is confirmed in a
new capture and the mismatch persists should AI construction/ticking be traced.

## Evidence limit

The Broker pair establishes the on-screen state values but not rendered art or
input handling. The human test supplies the visual locked-art and blocked
acceptance evidence; successful natural unlocking confirms the same slot
becomes available after progression. Static `T1_Car8` construction remains
documented in `locked-presentation.md`.
