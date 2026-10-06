# G.1 locked-state runtime correction #2

## Runtime evidence

All four supplied JSON captures were parsed. Their four raw `.dump.bin`
sidecars were rehashed and matched their JSON `source.raw_sha256` metadata.

| Capture | Candidate EXE SHA prefix | State |
|---|---|---|
| `20261006-143000_merc_not-locked` | `3346eb…` | ID26 locked text is correct; `CarModel=-1`, `selectedCar=26`, `UI/Enabled=True` |
| `20261006-143558_id3-locked` | `3346eb…` | stock ID3 lock oracle; `CarModel=-1`, `selectedCar=3`, `UI/Enabled=False` |
| `20261006-143842_merc-masterrallye-mode` | `3346eb…` | `Race/Car0/CarID=26`; Race Details vehicle string is `GALOCAL UNKNOWN` |
| `20261006-144257_merc-rallyecup-mode` | `3346eb…` | `Race/Car0/CarID=26`; Race Details vehicle string is `GALOCAL UNKNOWN` |

Human interaction evidence additionally establishes that the prior locked
ID26 widget could be accepted and driven: race state became `CarID=26`,
`CarClass=0`. This is separate from Broker `selectedCar`, which is now
classified only as highlighted/current frontend identity.

## Deployment provenance finding

The EXE image path and the raw Broker dump's `Root` header agree on the runtime
root suffix:

```text
.research-output/retired-worktrees/e0.1/research-output/r5v_f_2e/runtime/
```

The captured process used the exact G.1 candidate EXE SHA
`3346eb00442b88cca3f76f7a65606ca56006c5b981acdbf0ee4ad16412e5b055`. The
captured resource root contained a 282,687,977-byte `Data.sma` with SHA256
`131d61ee8241df9cee4885db046e4e68d4df8177df40638bab01662ee12dc736` and the
qualified loose `DataGx/Vehicles/Mercedes` package. It did **not** contain a
loose `DataScene/FrontendScreens/VehicleSelect.xml`. The generated XML with
SHA256 `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`
was outside that Root.

Therefore the exact correction overlay was absent from the active Root during
the failed lock-art/button test. This is a confirmed staging/provenance error.
The actual archive/loose search precedence and the exact scene member consumed
by that prior process remain `UNKNOWN`; Broker output cannot identify a file
source. The correction pass stops native control analysis until a run from the
new staged root confirms its `Root` header.

## Corrected package

`runtime-root-profile.json` pins the captured base resource components by
per-file inventory fingerprints. `tools/vehicle_unlock_runtime_package.py`
copies the pinned archive, loose audio/video, Vehicle Setup options, and
qualified Mercedes DX/DXT files into a new ignored runtime package, installs
the exact candidate EXE and loose VehicleSelect overlay, and omits previous
PlayerState files. It refuses an unknown or changed source component and does
not write into the captured root.

The package is a complete isolated launch tree under
`.research-output/vehicles/unlock/runtime-package/`. The prelaunch verifier
checks hashes and exact file inventory. It proves the on-disk tree; a postlaunch
capture Root header is still required to establish the process-selected Root.

## Race Details issue

The two mode captures independently show:

* Master Rallye: `CurrentRaceString="LEG 1/10 - FRANCE"`,
  `Race="MASTER RALLYE"`, `Car0/CarID=26`, vehicle display
  `GALOCAL UNKNOWN`.
* Rallye Cup: `CurrentRaceString="RACE 1/3"`, `Race="RALLYE CUP"`,
  `Car0/CarID=26`, vehicle display `GALOCAL UNKNOWN`.

This proves a separate Race Details presentation defect, not a wrong runtime
vehicle ID. Its producer/group has not been retraced in this correction pass:
the deployment mismatch is handled first, and Race Details code changes are
deferred until the exact loose scene path is validated. Do not infer Quick Race
group 0x35 as its owner from the symptom.
