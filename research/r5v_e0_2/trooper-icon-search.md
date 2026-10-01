# Trooper Vehicle Select icon search

## Result

No Trooper-specific Vehicle Select icon or carsheet binding was identified in
retail, demo-8.4.1, demo-9.3.1 or the cited beta carsheet research. The retail
carsheet frame25 is a red-and-white SUV, and frame31 is a forklift. Their
numeric filenames alone do not establish a vehicle identity.

The retail Vehicle Select scene has no Trooper-named icon resource. Retail
T3_Car widgets refer only to the carsheet bank and a numeric frame. Neither
frame25 nor frame31 is referenced by a stock car widget; frame30, by contrast,
is explicitly bound to T3_Car11 / ID24.

## Build-specific search notes

| Build / source | Finding | Interpretation |
|---|---|---|
| retail `DataGx/Frontend/VehicleSelect` | 32 carsheet frames; frame25 is red/white SUV; frame31 is forklift | no proven Trooper-specific Vehicle Select image |
| demo-8.4.1 VehicleSelect scene | T1=7, T2=8, T3=10; 16 carsheet images; no Trooper Vehicle Select binding | its separate Trooper reference is in `DataScene/FrontendScreens/Demo2MainMenu.hnt` and renders `Vehicles/Trooper/complete`, so it is a 3D attract/menu model rather than an icon |
| demo-9.3.1 `DataScene/FrontendScreens/Wjd/VehicleSelect.xml` | T1=7, T2=8, T3=11; 22 carsheet images; no T3_Car12 or Trooper icon hit | no Trooper Vehicle Select artwork established |
| beta carsheet note, `master-rallye-re-rdemo/research/r-demo/carsheet.md` | documents sheet extraction/mapping limits but does not identify a Trooper icon by name | not a usable identity mapping |

No demo/beta images were copied into the repository. The demo builds are
independently versioned; demo-9.3.1 Forester and demo-8.4.1 LandCruiser are not
retail vehicle names or payload mappings.

## P0 decision

Use retail frame5, already assigned to retail T3_Car3 / ID16 Astero, for the
first icon-binding test. It gives a clear visible response without fabricating
Trooper art or changing the Trooper model/profile. Replace it later with a
Trooper image only after a real icon source or user-supplied asset is
identified. The current diagnostic frame is explicitly a donor, not final
visual identity.
