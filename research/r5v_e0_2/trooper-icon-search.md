# Trooper Vehicle Select icon search

## Result

Retail still has no stock Trooper-specific Vehicle Select icon binding. Both
historical demos do contain the authentic Trooper icon: carsheet frame 14,
bound to the Trooper's class-local widget in each build. The retail carsheet
frame25 is a red-and-white SUV, and frame31 is a forklift. Their numeric
filenames alone do not establish a retail vehicle identity.

The retail Vehicle Select scene has no Trooper-named icon resource. Retail
T3_Car widgets refer only to the carsheet bank and a numeric frame. Neither
frame25 nor frame31 is referenced by a stock car widget; frame30, by contrast,
is explicitly bound to T3_Car11 / ID24.

## Build-specific search notes

| Build / source | Finding | Interpretation |
|---|---|---|
| retail `DataGx/Frontend/VehicleSelect` | 32 carsheet frames; frame25 is red/white SUV; frame31 is forklift | no proven Trooper-specific Vehicle Select image |
| demo-8.4.1 VehicleSelect scene | T1=7, T2=8, T3=10; 16 carsheet images; Trooper is registry ID7/class1 and `T2_Car1` binds frame14 | authentic camouflage Trooper icon; `carsheet_014_000.dxt`, 128x128, SHA-256 `3994529FEC45E292918B36A7EEF4AF99CFBB7B753B52009AAD71A6FAB83476B6` |
| demo-9.3.1 `DataScene/FrontendScreens/Wjd/VehicleSelect.xml` | T1=7, T2=8, T3=11; 22 carsheet images; Trooper is registry ID9/class1 and `T2_Car3` binds frame14 | same authentic icon bytes and same hash as demo-8.4.1; no T3_Car12 |
| beta carsheet note, `master-rallye-re-rdemo/research/r-demo/carsheet.md` | documents sheet extraction/mapping limits but does not identify a Trooper icon by name | not a usable identity mapping |

No demo/beta images were copied into the repository. The decoded contact sheets
and binary analysis outputs are ignored under `research-output/r5v_f/demo-icons/`.
The demo builds are independently versioned; demo-9.3.1 Forester and
demo-8.4.1 LandCruiser are not retail vehicle names or payload mappings.

## P0 decision

Use retail frame5, already assigned to retail T3_Car3 / ID16 Astero, for the
structural icon-binding test. The authentic demo Trooper frame is a known
optional art donor, but it must be converted/profiled for the retail archive
before use; demo files are not copied into retail or Git. The E0.2 runtime
result is a user report and does not identify which installed archive hash or
frame was tested.
