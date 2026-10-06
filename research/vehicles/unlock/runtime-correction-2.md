# G.1 locked-state runtime correction #2

> Historical correction record. The pending Race Details text below reflects
> the state at the time of this note and is superseded by the final captures in
> `runtime-captures.json` and the status in `closeout.md`.

## Follow-up result: corrected deployment and final localization candidate

The earlier XML deployment mismatch is resolved. New Observatory captures
`20261006-150942_merc-locked` and `20261006-151258_merc-unlocked` report the
active Root as
`.research-output/vehicles/unlock/runtime-package/`. The exact overlay hash
`6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d` was
staged there and verified before the human test. Human testing confirmed locked
ID26 shows the locked slot art, `UI/Enabled=False`, and cannot be accepted; once
the T1 Cup requirement is met, it unlocks and becomes selectable normally.
Both raw capture hashes match their metadata. Full values are appended to
`runtime-captures.json`.

Race Details is now statically traced. Master Rallye and Rallye Cup converge on
`FUN_0047C080`, whose group-`0x35` selector is the absolute
`RaceData/CompetitorN/CarID`. The deterministic final candidate returns the
existing `MERCEDES ML-320` string only for ID26 and replays the original lookup
for every other ID. It is installed in the same verified runtime package.
At the time of this correction, the Race Details result remained pending. It
was subsequently confirmed in both modes. See
`racedetails-localization.md` and `runtime-handoff.md`.

## Earlier runtime evidence before corrected scene deployment

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

## Historical deployment provenance finding

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
checks hashes and exact file inventory. At the time of this correction, a
postlaunch Root header was still needed; the later final Race Details captures
now report this exact Root.

## Race Details pre-fix captures

The two mode captures independently show:

* Master Rallye: `CurrentRaceString="LEG 1/10 - FRANCE"`,
  `Race="MASTER RALLYE"`, `Car0/CarID=26`, vehicle display
  `GALOCAL UNKNOWN`.
* Rallye Cup: `CurrentRaceString="RACE 1/3"`, `Race="RALLYE CUP"`,
  `Car0/CarID=26`, vehicle display `GALOCAL UNKNOWN`.

This proved a separate Race Details presentation defect, not a wrong runtime
vehicle ID. At that point the producer had not yet been traced. The static
follow-up above now identifies its shared writer and independent group-`0x35`
lookup. The final candidate was subsequently checked in both modes; see
`racedetails-localization.md`.
