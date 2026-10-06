# Challenge presentation / authored identity owners

Evidence: **CONFIRMED_BY_EXE** for exact pristine retail hash in
[map](challenge-preview-map.json); **CONFIRMED_BY_CORPUS** for retail
DataScene/FrontendScreens/Challenge.xml widget bindings. No XML is modified.

| Field | Source and consumer |
|---|---|
| Selected event | gaFEScreenChallengeAI instance+0x10; index0..10 |
| Authored human/AI | Registry singleton45A3C0, +570/+574+(event+25)*2C |
| Preview name | 45ECBE/45ECC1: language singleton485CF0 virtual+0xC, bank53, EDI absolute ID; 45ECE2 publishes Frontend/Challenge/Car2Text |
| Preview model | 45ED38/45ED41 publish the same EDI into Frontend/Challenge/OpponentCar |
| Model widget | XML OpponentCarModel -> gaFrontendCarMoverAI Model ID* |
| Model loading | 44C460 binds Model ID* at object+10; 44C4C0 reads Broker Int, registry+24+ID*34 family, loads Vehicles/<family>/complete when ID changes |
| Driver name | No DriverID/name widget in this Challenge screen; Driver6 was a runtime draw, not an authored challenge field |
| Class indicator / icon | No participant class indicator or separate vehicle icon here; the opponent visual is a 3D model |

Registry constructor458CD0 ->4598D0 ->45A330 initializes the event table.
At459F24/459F26, opponent23/human18 precede the RaceID35 record call459F4D.
Challenge11 therefore uses Megane18 versus Icecream23. Challenge1/RaceID25
uses Frontera6 versus Tata2, call459D81. All11 exact pairs are in the map.
No fixed DriverID6 field exists in these record inputs:44FEC0 builds/shuffles
a ten-driver pool before45010E;450150 publishes the chosen DriverID separately.

Challenge title/list, Logo, TimeToBeat, BestTime, unlock text/status and VersusText
are authored event/rule/progression presentation. They remain untouched.
Vehicle localization bank53 is identity, not challenge flavor prose.
Race setup consumes the same authored record ID fields before optional vehicle
substitution. Class always derives from the selected absolute ID at registry+0xC.

Frontend/Challenge/Challenge is a widget/selection value initialized separately;
arrow handling changes instance+10 directly. It is not used as authoritative
cache ownership. Pair checker event provenance is the explicit DLL Begin event
and race RaceID, with that Broker selection value reported only as context.
