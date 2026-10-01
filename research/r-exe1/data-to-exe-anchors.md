# Retail Data.sma semantic anchors into the executables

## Corpus inventory

Retail `Data.sma` has 7,714 sequential local records (7,595 file records and 119 directory records), roots `DataGame, DataGx, DataScene`, and 122 human-readable config/text files selected. Format observation: **ZIP local-file records followed by central directory; standard EOCD record is absent**. The pre-existing extracted view is used only after CRC and size checks against archive headers (122 text/config files verified; mismatches: 0). No archive member was extracted or changed by this script.

Vehicle families: Astero, Bruno, ChevyBlazer, Forester, Frontera, IceCream, Jump, Kamaz, Kangoo, KiaSportage, LandCruiser, Mattserati, Navara, NewRav, Pajero, Patrol, RMonster, SeatBuggy, Simmbugghini, Tata, Terrano, Ufo, WildCat, Xtrail, forklift, megane.

Course and RaceTest names: France1, France2, FranceM, FranceS1, FranceS2, FranceW, FranceWFlip, France_M, France_S1, France_S2, France_W, France_W_flip, Italy1, Italy2, Italy3, ItalyM1, ItalyM1Flip, ItalyM2, ItalyS1, ItalyS2, ItalyS3, ItalyS3Flip, ItalyS4, ItalyW1, ItalyW2, Italy_M1, Italy_M1_flip, Italy_M2, Italy_S1, Italy_S2, Italy_S3, Italy_S3_flip, Italy_S4, Italy_W1, Italy_W2, Multi, Spain1, Spain2, SpainM, SpainS1, SpainS1Flip, SpainS2, SpainW, SpainWFlip, Spain_M, Spain_S1, Spain_S1_flip, Spain_S2, Spain_W, Spain_W_flip, Template, TemplateNew, TestFrance1, Turkey1, Turkey2, Turkey3, TurkeyM, TurkeyS1, TurkeyS2, TurkeyS2Flip, TurkeyW, Turkey_m, Turkey_s1, Turkey_s2, Turkey_s2_flip, Turkey_w, smash.

High-frequency XML element names: `Value` (260983), `Marker` (45185), `AI` (16184), `AI_List` (4046), `Egg` (4046), `List` (980), `gaRacePaceNoteAI` (730), `gaBootAICar` (332), `enAiSoundSource` (328), `enUIFormattedTextAI` (249), `gaLimitBuilderAI` (204), `enUITextButtonAI` (182), `enUIMultiImageAI` (161), `gaFrontendStandardButtonAI` (126), `gaRaceSplitTimeAI` (117), `Scene` (99), `EggLists_Version4` (83), `gaAiCloudSetUp` (82), `gaFrontendBackgroundFaderAI` (77), `gaCameraManagerAI` (76), `gaFrontendXYButtonAI` (69), `MarkerLists` (46), `gaFrontendArrowAI` (44), `enUIText` (42), `aiShadowBoot` (41), `gaVehicleResetManager` (41), `gaHudLoader` (40), `gaIContAIManager` (40), `aiTrackBoot` (39), `gaRacePostFirstSplitTimeAI` (39), `gaFrontendMultistateAI` (38), `gaFrontendPulserAI` (32), `gaFrontendButtonUnlockerAI` (32), `gaFrontendDisablerAI` (25), `gaHudAiRaceProgress` (24).

High-frequency XML attribute names: `Name` (266021), `Type` (260983), `Value` (252891), `No` (61369), `Row0` (8092), `Row1` (8092), `Row2` (8092), `Row3` (8092), `SaveOptions` (7153), `SavePlayerState` (7153).

## Executable string matches

Matches use whole data-path fragments or distinctive identifiers, avoiding generic words such as `Input` and `Physics`. `CONFIRMED_BY_EXE_XREF` means a Ghidra xref reaches the string; string-only matches are kept separate. A missing literal does not rule out a dynamically formatted or hashed lookup.

| Grade | Build | String address | Data anchor | Executable string | Referencing functions |
|---|---|---:|---|---|---|
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e4de4` | `Vehicles/Bruno/car; Vehicles/Bruno` | `vehicles/Bruno/car` | FUN_00403350 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e4e3c` | `Vehicles/Bruno/car; Vehicles/Bruno` | `vehicles/bruno/car` | FUN_00403a40 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e4e50` | `Course/Italy1; Italy1` | `Course/Italy1/Italy1` | FUN_00403a40 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e52d0` | `gaAiWaterfallSound` | `gaAiWaterfallSound` | FUN_00407e00, FUN_00408080 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005e53a8` | `RaceLine` | `Draw To RaceLine` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005e53c8` | `RaceLine` | `Draw RaceLine` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005e53f4` | `Italy1` | `Italy1` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e53fc` | `RaceLine` | `RaceLine` | FUN_004674d0, FUN_005b2b20, FUN_005b2c60 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e5410` | `RaceLine` | `raceLine` | FUN_0040a070 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e6294` | `gaIContAIManager` | `gaIContAIManager` | FUN_004296c0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e62a8` | `gaIContAIManager` | `gaIContAiManager` | FUN_004298e0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e631c` | `gaIContDriverParams` | `gaIContDriverParams` | FUN_0042a9f0, FUN_0042b410, FUN_0042b670 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e65fc` | `gaPhysicsManager` | `gaPhysicsManager` | FUN_0042dc90, FUN_00439180 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005e697c` | `multiPlayer/Console/console` | `multiPlayer/console/console` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e6e14` | `RaceRetry` | `RaceRetry` | FUN_00441ff0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e6ea8` | `AudioOptions` | `AudioOptions` | FUN_00441ff0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e6ee4` | `RaceResults` | `RaceResults` | FUN_00441ff0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e6f14` | `VehicleSetup` | `VehicleSetup` | FUN_00441ff0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7000` | `Frontend/Running` | `Frontend/Running` | FUN_00442220, FUN_0046d230, FUN_0046d260 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7014` | `Frontend/OutputRaceData` | `Frontend/OutputRaceData` | FUN_00442220, FUN_0046d350, FUN_0046d380 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e702c` | `Frontend/Active` | `Frontend/Active` | FUN_00442220, FUN_0046d1d0, FUN_0046d200 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e703c` | `gaFrontendAI` | `gaFrontendAI` | FUN_00442220 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e70e8` | `gaFrontendArrowAI` | `gaFrontendArrowAI` | FUN_00444e10, FUN_00444ee0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7118` | `enUITextButtonAI` | `enUITextButtonAI` | FUN_00444fe0, FUN_004484a0, FUN_00448f90, FUN_004bb500 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e712c` | `gaFrontendBackgroundFaderAI` | `gaFrontendBackgroundFaderAI` | FUN_00445140, FUN_00445240 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e717c` | `gaFrontendCarMoverAI` | `gaFrontendCarMoverAI` | FUN_00445570 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e71a0` | `Frontend/VehicleSelect/CarModel; CarModel` | `Frontend/VehicleSelect/CarModel` | FUN_0044e3e0, FUN_004515a0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e71c0` | `gaFrontendCarSpinnerAI` | `gaFrontendCarSpinnerAI` | FUN_00445760 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7248` | `gaFrontendMultistateAI` | `gaFrontendMultistateAI` | FUN_004465d0, FUN_00446720 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7344` | `gaFrontendPulserAI` | `gaFrontendPulserAI` | FUN_004473f0, FUN_004474d0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e759c` | `Italy3` | `RaceTest/Italy3` | FUN_00447cb0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e75ac` | `Italy2` | `RaceTest/Italy2` | FUN_00447cb0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e75bc` | `Italy1` | `RaceTest/Italy1` | FUN_00447cb0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e75dc` | `WildCat` | `Wildcat` | FUN_00447870 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7600` | `LandCruiser` | `Landcruiser` | FUN_00447870 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e760c` | `Turkey3` | `RaceTest/Turkey3` | FUN_00447cb0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7620` | `Turkey2` | `RaceTest/Turkey2` | FUN_00447cb0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7634` | `Turkey1` | `RaceTest/Turkey1` | FUN_00447cb0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7648` | `Spain2` | `RaceTest/Spain2` | FUN_00447cb0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7658` | `Spain1` | `RaceTest/Spain1` | FUN_00447cb0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7668` | `France2` | `RaceTest/France2` | FUN_00447cb0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e767c` | `France1` | `RaceTest/France1` | FUN_00447cb0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7690` | `gaFrontendStandardButtonAI` | `gaFrontendStandardButtonAI` | FUN_00448170, FUN_004482c0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e76cc` | `gaFrontendTitleAI` | `gaFrontendTitleAI` | FUN_00448960, FUN_00448a30 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e76f4` | `Frontend/XYButton/Moving` | `Frontend/XYButton/Moving` | FUN_00448c30, FUN_0046d290, FUN_0046d2c0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7710` | `Frontend/XYButton/ForcePosition` | `Frontend/XYButton/ForcePosition` | FUN_00448c30, FUN_0046d2f0, FUN_0046d320 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7730` | `gaFrontendXYButtonAI` | `gaFrontendXYButtonAI` | FUN_00448c30, FUN_00448d80 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7980` | `gaFEScreenMultiplayerSelectAI` | `gaFEScreenMultiplayerSelectAI` | FUN_0044b6a0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e79bc` | `Frontend/NetworkGameSelected` | `Frontend/NetworkGameSelected` | FUN_0044bb70, FUN_0044c020 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7b00` | `Frontend/QuickModeSelect/CountdownDifficultyList; Frontend/QuickModeSelect/CountdownDifficulty` | `Frontend/QuickModeSelect/CountdownDifficultyList` | FUN_0044d3e0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7b34` | `Frontend/QuickModeSelect/RaceDifficultyList; Frontend/QuickModeSelect/RaceDifficulty` | `Frontend/QuickModeSelect/RaceDifficultyList` | FUN_0044d3e0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7b60` | `Frontend/QuickModeSelect/NumOpponentsList; Frontend/QuickModeSelect/NumOpponents` | `Frontend/QuickModeSelect/NumOpponentsList` | FUN_0044d3e0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7bb0` | `Frontend/QuickModeSelect/ModeList; Frontend/QuickModeSelect/Mode` | `Frontend/QuickModeSelect/ModeList` | FUN_0044d3e0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7bd4` | `Frontend/QuickModeSelect/Mode` | `Frontend/QuickModeSelect/Mode` | FUN_0044dad0, FUN_0044dbf0, FUN_0044def0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7bf4` | `Frontend/QuickRace/FlagImageID; QuickRace` | `Frontend/QuickRace/FlagImageID` | FUN_0044dbf0, FUN_0044e630 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7c14` | `Frontend/QuickRace/LogoImageID; QuickRace` | `Frontend/QuickRace/LogoImageID` | FUN_0044dbf0, FUN_0044e630 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7c34` | `Frontend/QuickRace/CurrentRaceString; QuickRace` | `Frontend/QuickRace/CurrentRaceString` | FUN_0044dbf0, FUN_0044e630 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7c5c` | `Frontend/QuickRace/CurrentVehicleString; QuickRace` | `Frontend/QuickRace/CurrentVehicleString` | FUN_0044dbf0, FUN_0044e630 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7c84` | `Frontend/QuickRace/CurrentManufacturerString; QuickRace` | `Frontend/QuickRace/CurrentManufacturerString` | FUN_0044dbf0, FUN_0044e630 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7cb4` | `Frontend/QuickModeSelect/CountdownDifficulty` | `Frontend/QuickModeSelect/CountdownDifficulty` | FUN_0044dbf0, FUN_0044def0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7ce4` | `Frontend/QuickModeSelect/RaceDifficulty` | `Frontend/QuickModeSelect/RaceDifficulty` | FUN_0044dbf0, FUN_0044def0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7d0c` | `Frontend/QuickModeSelect/NumOpponents` | `Frontend/QuickModeSelect/NumOpponents` | FUN_0044dbf0, FUN_0044def0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7d54` | `gaFEScreenQuickRaceAI` | `gaFEScreenQuickRaceAI` | FUN_0044e320 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7d6c` | `Frontend/QuickRace/CountdownDifficultyLevelString; Frontend/QuickRace/CountdownDifficulty; QuickRace` | `Frontend/QuickRace/CountdownDifficultyLevelString` | FUN_0044e630 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7da0` | `Frontend/QuickRace/DifficultyLevelString; Frontend/QuickRace/Difficulty; QuickRace` | `Frontend/QuickRace/DifficultyLevelString` | FUN_0044e630 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7dcc` | `Frontend/QuickRace/NumOpponentsString; Frontend/QuickRace/NumOpponents; QuickRace` | `Frontend/QuickRace/NumOpponentsString` | FUN_0044e630 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7df4` | `Frontend/QuickRace/GhostTypeString; Frontend/QuickRace/Ghost; QuickRace` | `Frontend/QuickRace/GhostTypeString` | FUN_0044e630 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7e18` | `Frontend/QuickRace/CurrentModeString; QuickRace` | `Frontend/QuickRace/CurrentModeString` | FUN_0044e630 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7e54` | `gaFEScreenRaceResultsAI` | `gaFEScreenRaceResultsAI` | FUN_0044ed90 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7e7c` | `Frontend/RaceResults/PointsList; RaceResults` | `Frontend/RaceResults/PointsList` | FUN_0044eee0, FUN_0044f6f0, FUN_0044f790 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7e9c` | `Frontend/RaceResults/TimeList; RaceResults` | `Frontend/RaceResults/TimeList` | FUN_0044eee0, FUN_0044f6f0, FUN_0044f790 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7ebc` | `RaceResults` | `Frontend/RaceResults/CarList` | FUN_0044eee0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7edc` | `Frontend/RaceResults/NameList; RaceResults` | `Frontend/RaceResults/NameList` | FUN_0044eee0, FUN_0044f6f0, FUN_0044f790 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7efc` | `Frontend/RaceResults/PositionList; RaceResults` | `Frontend/RaceResults/PositionList` | FUN_0044eee0, FUN_0044f6f0, FUN_0044f790 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7f20` | `gaFEScreenRaceRetryAI` | `gaFEScreenRaceRetryAI` | FUN_00450220 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7f38` | `gaFEScreenRaceSelectAI` | `gaFEScreenRaceSelectAI` | FUN_00450510 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7fb0` | `Frontend/RaceSelect/RightArrow` | `Frontend/RaceSelect/RightArrow` | FUN_004509c0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7fd0` | `Frontend/RaceSelect/LeftArrow` | `Frontend/RaceSelect/LeftArrow` | FUN_004509c0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e7ff0` | `Frontend/RaceSelect/RaceName; Frontend/RaceSelect/Race; RaceName` | `Frontend/RaceSelect/RaceName` | FUN_004509c0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e8030` | `Frontend/RaceSelect/RaceImage2; Frontend/RaceSelect/Race` | `Frontend/RaceSelect/RaceImage2` | FUN_004509c0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e8050` | `Frontend/RaceSelect/RaceImage1; Frontend/RaceSelect/Race` | `Frontend/RaceSelect/RaceImage1` | FUN_004509c0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e8088` | `Frontend/TitleScreen` | `Frontend/TitleScreen` | FUN_00450db0, FUN_00450f00 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e80b0` | `gaFEScreenVehicleSelectAI` | `gaFEScreenVehicleSelectAI` | FUN_00450fe0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005e80cc` | `Player2` | `Player2` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005e80d4` | `Player1` | `Player1` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e818c` | `Frontend/VehicleSelect/Endurance` | `Frontend/VehicleSelect/Endurance` | FUN_004515a0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e81b0` | `Frontend/VehicleSelect/Handling` | `Frontend/VehicleSelect/Handling` | FUN_004515a0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e81d0` | `Frontend/VehicleSelect/Acceleration` | `Frontend/VehicleSelect/Acceleration` | FUN_004515a0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e81f4` | `Frontend/VehicleSelect/Speed` | `Frontend/VehicleSelect/Speed` | FUN_004515a0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e8214` | `Frontend/VehicleSelect/ModelName` | `Frontend/VehicleSelect/ModelName` | FUN_004515a0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005e8238` | `Frontend/VehicleSelect/ManufacturerName` | `Frontend/VehicleSelect/ManufacturerName` | FUN_004515a0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005e9d0c` | `LandCruiser` | `TOYOTA LANDCRUISER` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005e9e14` | `LandCruiser` | `LANDCRUISER` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea3c8` | `gaRaceFinishAI` | `gaRaceFinishAI` | FUN_004527f0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005ea3e4` | `TimeToFirstCheckpoint` | `Race/Countdown/TimeToFirstCheckpoint` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea438` | `gaRaceFinishAreaAI` | `gaRaceFinishAreaAI` | FUN_00452f90 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005ea460` | `gaRaceFinishAreaAI` | `gaRaceFinishAreaAI: No FinishArea markers found! ` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea4a0` | `gaRaceLineAI` | `gaRaceLineAI` | FUN_00453320 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005ea4b0` | `RaceLine` | `***Raceline not found in scene*** ` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea52c` | `gaRacePaceNoteAI` | `gaRacePaceNoteAI` | FUN_00453c10, FUN_00453ff0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea5c0` | `gaRacePostFirstSplitTimeAI` | `gaRacePostFirstSplitTimeAI` | FUN_00454180, FUN_004542b0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea608` | `TimeToFirstCheckpoint` | `TimeToFirstCheckpoint` | FUN_004542b0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea620` | `gaRaceSplitTimeAI` | `gaRaceSplitTimeAI` | FUN_004543f0, FUN_00454900 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005ea6c8` | `SplitTimes` | `SplitTimes: Split Time %d initialised ` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005ea6f0` | `RaceLine` | `No raceline found - SplitTime percentage value not filled in ` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea7f8` | `gaRaceStarterAI` | `gaRaceStarterAI` | FUN_004555b0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea8e4` | `gaRaceTimerAI` | `gaRaceTimerAI` | FUN_00455ff0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea908` | `gaDefaultParamBrokerRegistration` | `gaDefaultParamBrokerRegistration` | FUN_00456590, FUN_00456650 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea92c` | `CarModelDataFile` | `CarModelDataFile` | FUN_00456650, FUN_00456710 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ea948` | `gaDefaultTyreParamBrokerRegistration` | `gaDefaultTyreParamBrokerRegistration` | FUN_00457220, FUN_004572e0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eaf0c` | `gaHudAiCarDamage` | `gaHudAiCarDamage` | FUN_00465d60, FUN_00465ea0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005eb024` | `Damage/MAX_Suspension` | `Damage/MAX_Suspension` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005eb03c` | `Damage/MAX_SteeringWheel` | `Damage/MAX_SteeringWheel` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005eb058` | `Damage/MAX_Tyre` | `Damage/MAX_Tyre` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005eb068` | `Damage/MAX_Engine` | `Damage/MAX_Engine` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb0b4` | `gaHudAiGameTimer` | `gaHudAiGameTimer` | FUN_00466e30, FUN_00466f30, FUN_00467610, FUN_00467e70, FUN_004683b0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb0d4` | `gaHudAiGearCounter` | `gaHudAiGearCounter` | FUN_004671b0, FUN_00467280 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb0e8` | `gaHudAiGPSNeedle` | `gaHudAiGPSNeedle` | FUN_004674d0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb144` | `gaHudAiOffCourse` | `gaHudAiOffCourse` | FUN_00468110 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb15c` | `gaHudAiPaceNotes` | `gaHudAiPaceNotes` | FUN_004682a0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb1e8` | `gaHudAiRaceComplete` | `gaHudAiRaceComplete` | FUN_00468aa0, FUN_00468b70 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb210` | `gaHudAiRaceProgress` | `gaHudAiRaceProgress` | FUN_00468f20, FUN_00469010 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb2b0` | `gaHudAiRaceProgressBar` | `gaHudAiRaceProgressBar` | FUN_00469570, FUN_00469640 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb2e4` | `gaHudAiSpeedCounter` | `gaHudAiSpeedCounter` | FUN_004699c0, FUN_00469a90, FUN_0046a740 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb300` | `gaHudAiSpeedDial` | `gaHudAiSpeedDial` | FUN_00469cd0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb3f8` | `gaHudAiSpeedNeedle` | `gaHudAiSpeedNeedle` | FUN_0046a1d0, FUN_0046a2a0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb40c` | `gaHudAiSpeedText` | `gaHudAiSpeedText` | FUN_0046a670 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb420` | `gaHudAiSplitTime` | `gaHudAiSplitTime` | FUN_0046a920, FUN_0046aa50 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb444` | `gaHudAiWrongWay` | `gaHudAiWrongWay` | FUN_0046ade0, FUN_0046aeb0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb454` | `gaHudLoader` | `gaHudLoader` | FUN_0046b150, FUN_0046b220 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb5bc` | `RaceName` | `Race/RaceName` | FUN_0046b500, FUN_00476fd0, FUN_004784b0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005eb774` | `Frontend/ShowEffects` | `Frontend/ShowEffects` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb7f0` | `QuickRace` | `Frontend/QuickRace/Car` | FUN_0046d580, FUN_0046d5b0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb808` | `Frontend/QuickRace/Track; QuickRace` | `Frontend/QuickRace/Track` | FUN_0046d5e0, FUN_0046d610 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb824` | `Frontend/QuickRace/Mode; QuickRace` | `Frontend/QuickRace/Mode` | FUN_0046d640, FUN_0046d670 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb83c` | `Frontend/QuickRace/Ghost; QuickRace` | `Frontend/QuickRace/Ghost` | FUN_0046d6a0, FUN_0046d6d0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb858` | `Frontend/QuickRace/NumOpponents; QuickRace` | `Frontend/QuickRace/NumOpponents` | FUN_0046d700, FUN_0046d730 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb878` | `Frontend/QuickRace/Difficulty; QuickRace` | `Frontend/QuickRace/Difficulty` | FUN_0046d760, FUN_0046d790 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb898` | `Frontend/QuickRace/CountdownDifficulty; QuickRace` | `Frontend/QuickRace/CountdownDifficulty` | FUN_0046d7c0, FUN_0046d7f0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb8c0` | `SplitScreen` | `Frontend/SplitScreen` | FUN_0046d820, FUN_0046d850 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005eb8d8` | `MusicVolume` | `Music/MusicVolume` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005eb92c` | `Frontend/SkipTitles` | `Frontend/SkipTitles` | FUN_0046dab0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ebc50` | `gaAiCloudSetUp` | `gaAiCloudSetUp` | FUN_0046f0e0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005ebcd8` | `Frontend/Active` | `FrontEnd/Active` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ebd94` | `ControllerCarParams` | `ControllerCarParams` | FUN_00470140, FUN_004e76d0, FUN_00515d20, FUN_00516690, FUN_00517230 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ebdcc` | `gaBootAICar` | `gaBootAICar` | FUN_00472c40 |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005ebde8` | `Race/Car/InputType` | `Race/Car/InputType` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 8.4.1 | `005ebdfc` | `Race/Car/PlayerType` | `Race/Car/PlayerType` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ebe38` | `gaCameraManagerAI` | `gaCameraManagerAI` | FUN_00473710 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ebe9c` | `gaCameraManagerParams; gaCameraManagerAI` | `Error : gaCameraManagerAI - gaCameraManagerParams Not Avaliable ` | FUN_00473c30 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ebee0` | `gaCameraManagerParams` | `gaCameraManagerParams` | FUN_00473c30, FUN_00473e40, FUN_004741b0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ec334` | `Camera1` | `Camera1/Previous` | FUN_00479970 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ec348` | `Camera1` | `Camera1/Next` | FUN_00479970 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ec358` | `Camera0` | `Camera0/Previous` | FUN_00479970 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ec36c` | `Camera0` | `Camera0/Next` | FUN_00479970 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ec474` | `OnePlayer` | `OnePlayer` | FUN_0047c3e0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ec728` | `SavePlayerState` | `SavePlayerState` | FUN_00488cc0, FUN_004e2770 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ec738` | `SaveOptions` | `SaveOptions` | FUN_00488cc0, FUN_004e2770 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ecaac` | `aiStaticCamera` | `aiStaticCamera` | FUN_004cbe40, FUN_004cbef0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ecb68` | `enUIFormattedTextAI` | `enUIFormattedTextAI` | FUN_004bc0f0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ecbd8` | `enUIText` | `enUIText` | FUN_004bd210 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ecc64` | `CameraID` | `CameraID` | FUN_004bdf80, FUN_004be460, FUN_004c0180, FUN_004cbef0, FUN_004cc2c0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ecdb4` | `aiRotateCamera` | `aiRotateCamera` | FUN_004c06e0, FUN_004c07b0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ed048` | `enUIMultiImageAI` | `enUIMultiImageAI` | FUN_004c3d80, FUN_004c3e30 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ed0d0` | `enUITileBox` | `enUITileBox` | FUN_004c4af0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ed1e4` | `enUIGradientBoxAI` | `enUIGradientBoxAI` | FUN_004c5c20, FUN_004c5ce0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ed230` | `enUIController` | `enUIController` | FUN_004c5f50 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ed260` | `enUIBrowser` | `enUIBrowser` | FUN_004c64d0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ed324` | `aiFollowMatrix` | `aiFollowMatrix` | FUN_004c76f0 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ed5d8` | `aiShadowBoot` | `aiShadowBoot` | FUN_004cae10 |
| CONFIRMED_BY_EXE_XREF | 8.4.1 | `005ed6d0` | `aiCameraZoom` | `aiCameraZoom` | FUN_004cc1b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `00698330` | `Vehicles/Bruno/car; Vehicles/Bruno` | `vehicles/Bruno/car` | FUN_004037f0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `00698388` | `Vehicles/Bruno/car; Vehicles/Bruno` | `vehicles/bruno/car` | FUN_00403ee0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069839c` | `Course/Italy1; Italy1` | `Course/Italy1/Italy1` | FUN_00403ee0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `00698504` | `RaceLine` | `RaceLine` | FUN_00406260, FUN_00406410, FUN_0047bc90, FUN_0047c290, FUN_0047cca0, FUN_0047d710 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `00698750` | `gaRaceSplitTimeAI` | `gaRaceSplitTimeAI` | FUN_004073c0, FUN_0047cca0, FUN_0047f2c0, FUN_00482740, FUN_00482e30 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `00698c2c` | `gaAiWaterfallSound` | `gaAiWaterfallSound` | FUN_0040a130, FUN_0040a3c0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `00698d04` | `RaceLine` | `Draw To RaceLine` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `00698d24` | `RaceLine` | `Draw RaceLine` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `00699bb0` | `gaIContAIManager` | `gaIContAIManager` | FUN_0042a860 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `00699bc4` | `gaIContAIManager` | `gaIContAiManager` | FUN_0042aaa0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `00699e0c` | `gaIContDriverParams` | `Error : gaIContDriverLookUp - gaIContDriverParams Not Avaliable ` | FUN_0042cb60 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `00699e50` | `gaIContDriverParams` | `gaIContDriverParams` | FUN_0042cb60, FUN_0042dd70, FUN_0042dfd0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a134` | `gaPhysicsManager` | `gaPhysicsManager` | FUN_0042ff60, FUN_0043cd00, FUN_004bc750, FUN_004bdb90, FUN_004be000 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `0069a4b4` | `multiPlayer/Console/console` | `multiPlayer/console/console` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a6d4` | `VehicleSetup4` | `VehicleSetup4` | FUN_00448a90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a720` | `VehicleSetup3` | `VehicleSetup3` | FUN_00448a90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a730` | `VehicleSetup2` | `VehicleSetup2` | FUN_00448a90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a7f4` | `QuickRace` | `QuickRace` | FUN_00448a90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a810` | `RaceRetry` | `RaceRetry` | FUN_00448a90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a870` | `MultiplayerSelect` | `MultiplayerSelect` | FUN_00448a90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a89c` | `AudioOptions` | `AudioOptions` | FUN_00448a90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a8d8` | `RaceResults` | `RaceResults` | FUN_00448a90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a904` | `VehicleSetup` | `VehicleSetup` | FUN_00448a90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a9e0` | `Frontend/Running` | `Frontend/Running` | FUN_00448dd0, FUN_004a1630, FUN_004a1660 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069a9f4` | `Frontend/OutputRaceData` | `Frontend/OutputRaceData` | FUN_00448dd0, FUN_004a1750, FUN_004a1780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069aa0c` | `Frontend/Active` | `Frontend/Active` | FUN_00448dd0, FUN_004a15d0, FUN_004a1600 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069aa1c` | `gaFrontendAI` | `gaFrontendAI` | FUN_00448dd0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069aac8` | `Italy1` | `Racetest/italy1` | FUN_0044a040 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069aae8` | `France1` | `Racetest/france1` | FUN_0044a040 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ab68` | `Player2` | `Controller/DeviceMap/Player2` | FUN_0044a360 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ab88` | `Player2` | `Controller/DeviceMapCopy/Player2` | FUN_0044a360, FUN_004665a0, FUN_00466a00, FUN_004a0490 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069abac` | `Player1` | `Controller/DeviceMap/Player1` | FUN_0044a360 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069abcc` | `Player1` | `Controller/DeviceMapCopy/Player1` | FUN_0044a360, FUN_004665a0, FUN_00466a00, FUN_004a0490 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ac40` | `gaFrontendArrowAI` | `gaFrontendArrowAI` | FUN_0044c390, FUN_0044c460 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ac70` | `enUITextButtonAI` | `enUITextButtonAI` | FUN_0044c560, FUN_004526d0, FUN_004572a0, FUN_00457e10, FUN_00512730 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ac84` | `gaFrontendBackgroundFaderAI` | `gaFrontendBackgroundFaderAI` | FUN_0044c6c0, FUN_0044c7c0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069acdc` | `gaFrontendButtonUnlockerAI` | `gaFrontendButtonUnlockerAI` | FUN_0044cb40, FUN_0044cc20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ad40` | `gaFrontendMultistateAI` | `gaFrontendMultistateAI` | FUN_0044cdc0, FUN_004503b0, FUN_00450500 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ad58` | `gaFrontendXYButtonAI` | `gaFrontendXYButtonAI` | FUN_0044cdc0, FUN_00457a70, FUN_00457bc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ad70` | `gaFrontendStandardButtonAI` | `gaFrontendStandardButtonAI` | FUN_0044cdc0, FUN_00456f70, FUN_004570c0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ad8c` | `gaFrontendCarMoverAI` | `gaFrontendCarMoverAI` | FUN_0044d000, FUN_0044d0d0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ade0` | `gaFrontendCarSpinnerAI` | `gaFrontendCarSpinnerAI` | FUN_0044d440 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `0069b570` | `Race/PauseMenu/Index` | `Race/PauseMenu/Index` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b588` | `Race/PauseMenu/List` | `Race/PauseMenu/List` | FUN_004511a0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b59c` | `Frontend/buttons/UpDownArrows` | `Frontend/buttons/UpDownArrows` | FUN_00451070, FUN_00452560 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b5bc` | `gaFrontendPauseMenuAI` | `gaFrontendPauseMenuAI` | FUN_00450f10, FUN_00451320 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b608` | `gaFrontendPopupAI` | `gaFrontendPopupAI` | FUN_004522e0, FUN_004527f0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b6c4` | `gaFrontendPulserAI` | `gaFrontendPulserAI` | FUN_00453e80, FUN_00453f60 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b91c` | `Italy3` | `RaceTest/Italy3` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b92c` | `Italy2` | `RaceTest/Italy2` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b93c` | `Italy1` | `RaceTest/Italy1` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b95c` | `IceCream` | `Icecream` | FUN_00454b10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b970` | `WildCat` | `Wildcat` | FUN_00454b10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b99c` | `SeatBuggy` | `SeatBuggy` | FUN_00454b10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b9d0` | `KiaSportage` | `Kiasportage` | FUN_00454b10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b9dc` | `NewRav` | `Newrav` | FUN_00454b10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069b9ec` | `RMonster` | `Rmonster` | FUN_00454b10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ba28` | `ChevyBlazer` | `Chevyblazer` | FUN_00454b10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ba4c` | `LandCruiser` | `Landcruiser` | FUN_00454b10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ba58` | `ItalyM1` | `RaceTest/ItalyM1` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ba6c` | `SpainS2` | `RaceTest/SpainS2` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ba80` | `TurkeyS1` | `RaceTest/TurkeyS1` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ba94` | `SpainM` | `RaceTest/SpainM` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069baa4` | `ItalyS3` | `RaceTest/ItalyS3` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bab8` | `FranceS1` | `RaceTest/FranceS1` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bacc` | `ItalyW1` | `RaceTest/ItalyW1` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bae0` | `FranceM` | `RaceTest/FranceM` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069baf4` | `SpainW` | `RaceTest/SpainW` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bb04` | `TurkeyM` | `RaceTest/TurkeyM` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bb18` | `ItalyM2` | `RaceTest/ItalyM2` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bb2c` | `ItalyS1` | `RaceTest/ItalyS1` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bb40` | `TurkeyW` | `RaceTest/TurkeyW` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bb54` | `SpainS1` | `RaceTest/SpainS1` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bb68` | `FranceW` | `RaceTest/FranceW` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bb7c` | `ItalyW2` | `RaceTest/ItalyW2` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bb90` | `TurkeyS2` | `RaceTest/TurkeyS2` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bba4` | `ItalyS2` | `RaceTest/ItalyS2` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bbb8` | `FranceS2` | `RaceTest/FranceS2` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bbcc` | `ItalyS4` | `RaceTest/ItalyS4` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bbe0` | `Turkey3` | `RaceTest/Turkey3` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bbf4` | `Turkey2` | `RaceTest/Turkey2` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bc08` | `Turkey1` | `RaceTest/Turkey1` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bc1c` | `Spain2` | `RaceTest/Spain2` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bc2c` | `Spain1` | `RaceTest/Spain1` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bc3c` | `France2` | `RaceTest/France2` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bc50` | `France1` | `RaceTest/France1` | FUN_004555e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bd14` | `gaFrontendTitleAI` | `gaFrontendTitleAI` | FUN_004577a0, FUN_00457870 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bd3c` | `Frontend/XYButton/Moving` | `Frontend/XYButton/Moving` | FUN_00457a70, FUN_004a1690, FUN_004a16c0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bd58` | `Frontend/XYButton/ForcePosition` | `Frontend/XYButton/ForcePosition` | FUN_00457a70, FUN_004a16f0, FUN_004a1720 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069be38` | `gaFEScreenAudioOptionsAI` | `gaFEScreenAudioOptionsAI` | FUN_00458930 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069be68` | `Frontend/AudioOptions/EngineVolume; AudioOptions` | `Frontend/AudioOptions/EngineVolume` | FUN_00458a80, FUN_00458dc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069be8c` | `Frontend/AudioOptions/SFXVolume; AudioOptions` | `Frontend/AudioOptions/SFXVolume` | FUN_00458a80, FUN_00458dc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069beac` | `Frontend/AudioOptions/MusicVolume; AudioOptions; MusicVolume` | `Frontend/AudioOptions/MusicVolume` | FUN_00458a80, FUN_00458dc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bed0` | `Frontend/AudioOptions/EngineVolumeText; Frontend/AudioOptions/EngineVolume; AudioOptions` | `Frontend/AudioOptions/EngineVolumeText` | FUN_00458dc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bef8` | `Frontend/AudioOptions/SFXVolumeText; Frontend/AudioOptions/SFXVolume; AudioOptions` | `Frontend/AudioOptions/SFXVolumeText` | FUN_00458dc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bf1c` | `Frontend/AudioOptions/MusicVolumeText; Frontend/AudioOptions/MusicVolume; MusicVolumeText; AudioOptions` | `Frontend/AudioOptions/MusicVolumeText` | FUN_00458dc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bf4c` | `Frontend/AudioOptions/MusicFader; AudioOptions` | `Frontend/AudioOptions/MusicFader` | FUN_00458fb0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bf70` | `Frontend/AudioOptions/SFXFader; AudioOptions` | `Frontend/AudioOptions/SFXFader` | FUN_00458fb0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bf90` | `Frontend/AudioOptions/EngineFader; AudioOptions` | `Frontend/AudioOptions/EngineFader` | FUN_00458fb0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bfcc` | `Frontend/Challenge/Challenge` | `Frontend/Challenge/Challenge` | FUN_004591c0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069bfec` | `Frontend/Challenge/ChallengeList; Frontend/Challenge/Challenge` | `Frontend/Challenge/ChallengeList` | FUN_004591c0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c010` | `Frontend/Challenge/ChallengeOpened; Frontend/Challenge/Challenge` | `Frontend/Challenge/ChallengeOpened` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c034` | `Frontend/Challenge/VersusText` | `Frontend/Challenge/VersusText` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c054` | `Frontend/Challenge/UnlockText2` | `Frontend/Challenge/UnlockText2` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c074` | `Frontend/Challenge/UnlockText1` | `Frontend/Challenge/UnlockText1` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c094` | `Frontend/Challenge/BestTime` | `Frontend/Challenge/BestTime` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c0b0` | `Frontend/Challenge/ChallengeStatus; Frontend/Challenge/Challenge` | `Frontend/Challenge/ChallengeStatus` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c0d4` | `Frontend/Challenge/ChallengeRightArrow; Frontend/Challenge/Challenge` | `Frontend/Challenge/ChallengeRightArrow` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c0fc` | `Frontend/Challenge/ChallengeLeftArrow; Frontend/Challenge/Challenge` | `Frontend/Challenge/ChallengeLeftArrow` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c124` | `Frontend/Challenge/TimeToBeat` | `Frontend/Challenge/TimeToBeat` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c15c` | `Frontend/Challenge/OpponentCar` | `Frontend/Challenge/OpponentCar` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c17c` | `Frontend/Challenge/PlayerCar` | `Frontend/Challenge/PlayerCar` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c19c` | `Frontend/Challenge/Car2Text; Car2Text` | `Frontend/Challenge/Car2Text` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c1b8` | `Frontend/Challenge/Car1Text; Car1Text` | `Frontend/Challenge/Car1Text` | FUN_00459780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c1f4` | `Frontend/CountryDetails/CountryText` | `Frontend/CountryDetails/CountryText` | FUN_0045a0b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c218` | `Frontend/CountryDetails/DescriptionText` | `Frontend/CountryDetails/DescriptionText` | FUN_0045a0b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c280` | `Frontend/CupSelect/Logo` | `Frontend/CupSelect/Logo` | FUN_0045adb0, FUN_0045b2d0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c298` | `Frontend/CupSelect/Class` | `Frontend/CupSelect/Class` | FUN_0045adb0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c2b4` | `Frontend/CupSelect/ClassList; Frontend/CupSelect/Class` | `Frontend/CupSelect/ClassList` | FUN_0045adb0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c2f4` | `Frontend/CupSelect/CupRightArrow` | `Frontend/CupSelect/CupRightArrow` | FUN_0045b2d0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c318` | `Frontend/CupSelect/CupLeftArrow` | `Frontend/CupSelect/CupLeftArrow` | FUN_0045b2d0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c338` | `Frontend/CupSelect/ClassRightArrow; Frontend/CupSelect/Class` | `Frontend/CupSelect/ClassRightArrow` | FUN_0045b2d0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c35c` | `Frontend/CupSelect/ClassLeftArrow; Frontend/CupSelect/Class` | `Frontend/CupSelect/ClassLeftArrow` | FUN_0045b2d0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c380` | `Frontend/CupSelect/LogoText; Frontend/CupSelect/Logo` | `Frontend/CupSelect/LogoText` | FUN_0045b2d0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c39c` | `Frontend/CupSelect/Cup3BestTime` | `Frontend/CupSelect/Cup3BestTime` | FUN_0045b420 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c3bc` | `Frontend/CupSelect/Cup2BestTime` | `Frontend/CupSelect/Cup2BestTime` | FUN_0045b420 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c3dc` | `Frontend/CupSelect/Cup1BestTime` | `Frontend/CupSelect/Cup1BestTime` | FUN_0045b420 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c41c` | `Frontend/CupSelect/Cup3Status` | `Frontend/CupSelect/Cup3Status` | FUN_0045b420 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c43c` | `Frontend/CupSelect/Cup2Status` | `Frontend/CupSelect/Cup2Status` | FUN_0045b420 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c45c` | `Frontend/CupSelect/Cup1Status` | `Frontend/CupSelect/Cup1Status` | FUN_0045b420 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c47c` | `Frontend/CupSelect/CupStatus` | `Frontend/CupSelect/CupStatus` | FUN_0045b420 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c4d4` | `Frontend/GameOptions/Gear2Type` | `Frontend/GameOptions/Gear2Type` | FUN_0045bfc0, FUN_0045c4c0, FUN_0045c5b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c4f4` | `Frontend/GameOptions/Gear2TypeList; Frontend/GameOptions/Gear2Type` | `Frontend/GameOptions/Gear2TypeList` | FUN_0045bfc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c518` | `Frontend/GameOptions/GearType` | `Frontend/GameOptions/GearType` | FUN_0045bfc0, FUN_0045c4c0, FUN_0045c5b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c538` | `Frontend/GameOptions/GearTypeList; Frontend/GameOptions/GearType` | `Frontend/GameOptions/GearTypeList` | FUN_0045bfc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c55c` | `Frontend/GameOptions/SpeedUnits` | `Frontend/GameOptions/SpeedUnits` | FUN_0045bfc0, FUN_0045c4c0, FUN_0045c5b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c590` | `Frontend/GameOptions/SpeedUnitsList; Frontend/GameOptions/SpeedUnits` | `Frontend/GameOptions/SpeedUnitsList` | FUN_0045bfc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c5dc` | `Frontend/GameOptions/Gear2RightArrow` | `Frontend/GameOptions/Gear2RightArrow` | FUN_0045c5b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c604` | `Frontend/GameOptions/Gear2LeftArrow` | `Frontend/GameOptions/Gear2LeftArrow` | FUN_0045c5b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c628` | `Frontend/GameOptions/GearRightArrow` | `Frontend/GameOptions/GearRightArrow` | FUN_0045c5b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c64c` | `Frontend/GameOptions/GearLeftArrow` | `Frontend/GameOptions/GearLeftArrow` | FUN_0045c5b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c670` | `Frontend/GameOptions/SpeedRightArrow` | `Frontend/GameOptions/SpeedRightArrow` | FUN_0045c5b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c698` | `Frontend/GameOptions/SpeedLeftArrow` | `Frontend/GameOptions/SpeedLeftArrow` | FUN_0045c5b0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `0069c76c` | `ParticleQuality` | `ParticleQuality` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `0069c78c` | `TextureDepth` | `TextureDepth` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `0069c79c` | `TextureQuality` | `TextureQuality` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c838` | `ParticleQuality` | `DirectX/Options/ParticleQuality` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c878` | `TextureDepth` | `DirectX/Options/TextureDepth` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c898` | `TextureQuality` | `DirectX/Options/TextureQuality` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c8d4` | `Frontend/GraphicsOptions/ReflectionsValue` | `Frontend/GraphicsOptions/ReflectionsValue` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c900` | `Frontend/GraphicsOptions/ReflectionsList` | `Frontend/GraphicsOptions/ReflectionsList` | FUN_0045d370 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c92c` | `Frontend/GraphicsOptions/ShadowQualityValue` | `Frontend/GraphicsOptions/ShadowQualityValue` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c958` | `Frontend/GraphicsOptions/ShadowQualityList` | `Frontend/GraphicsOptions/ShadowQualityList` | FUN_0045d370 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c984` | `Frontend/GraphicsOptions/SkyQualityValue` | `Frontend/GraphicsOptions/SkyQualityValue` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c9b0` | `Frontend/GraphicsOptions/SkyQualityList` | `Frontend/GraphicsOptions/SkyQualityList` | FUN_0045d370 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069c9d8` | `Frontend/GraphicsOptions/TyretrackQualityValue` | `Frontend/GraphicsOptions/TyretrackQualityValue` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ca08` | `Frontend/GraphicsOptions/TyretrackQualityList` | `Frontend/GraphicsOptions/TyretrackQualityList` | FUN_0045d370 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ca38` | `Frontend/GraphicsOptions/ParticleQualityValue` | `Frontend/GraphicsOptions/ParticleQualityValue` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ca68` | `Frontend/GraphicsOptions/ParticleQualityList` | `Frontend/GraphicsOptions/ParticleQualityList` | FUN_0045d370 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ca98` | `Frontend/GraphicsOptions/DetailPassesValue` | `Frontend/GraphicsOptions/DetailPassesValue` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cac4` | `Frontend/GraphicsOptions/DetailPassesList` | `Frontend/GraphicsOptions/DetailPassesList` | FUN_0045d370 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069caf0` | `Frontend/GraphicsOptions/TextureDepthValue` | `Frontend/GraphicsOptions/TextureDepthValue` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cb1c` | `Frontend/GraphicsOptions/TextureDepthList` | `Frontend/GraphicsOptions/TextureDepthList` | FUN_0045d370 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cb48` | `Frontend/GraphicsOptions/TextureQualityValue` | `Frontend/GraphicsOptions/TextureQualityValue` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cb78` | `Frontend/GraphicsOptions/TextureQualityList` | `Frontend/GraphicsOptions/TextureQualityList` | FUN_0045d370 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cba4` | `Frontend/GraphicsOptions/ViewDistanceValue` | `Frontend/GraphicsOptions/ViewDistanceValue` | FUN_0045e060, FUN_0045e400 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cbd0` | `Frontend/GraphicsOptions/ViewDistanceList` | `Frontend/GraphicsOptions/ViewDistanceList` | FUN_0045d370 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cc54` | `Frontend/LanguageScreen/LanguageText` | `Frontend/LanguageScreen/LanguageText` | FUN_0045ebc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cc7c` | `Frontend/Language/Portuguese` | `Frontend/Language/Portuguese` | FUN_0045ed50 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cc9c` | `Frontend/Language/Spanish` | `Frontend/Language/Spanish` | FUN_0045ed50 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ccb8` | `Frontend/Language/German` | `Frontend/Language/German` | FUN_0045ed50 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ccd4` | `Frontend/Language/French` | `Frontend/Language/French` | FUN_0045ed50 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ccf0` | `Frontend/Language/Italian` | `Frontend/Language/Italian` | FUN_0045ed50 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cd0c` | `Frontend/Language/English` | `Frontend/Language/English` | FUN_0045ed50 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cdf8` | `gaFEScreenMultiplayerSelectAI` | `gaFEScreenMultiplayerSelectAI` | FUN_00460110 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cea4` | `Frontend/NetworkGameSelected` | `Frontend/NetworkGameSelected` | FUN_00463740 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cf1c` | `Frontend/NG_JoinGame4` | `Frontend/NG_JoinGame4` | FUN_00463c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cf34` | `Frontend/NG_JoinGame3` | `Frontend/NG_JoinGame3` | FUN_00463c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cf4c` | `Frontend/NG_JoinGame2` | `Frontend/NG_JoinGame2` | FUN_00463c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069cf64` | `Frontend/NG_JoinGame1` | `Frontend/NG_JoinGame1` | FUN_00463c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d00c` | `Frontend/VehicleSelect/CarModel; CarModel` | `Frontend/VehicleSelect/CarModel` | FUN_004645e0, FUN_004729e0, FUN_00478c00 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `0069d02c` | `StartRace` | `StartRace` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `0069d044` | `ChangeRace` | `ChangeRace` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d050` | `Frontend/QuickRace/CountdownDifficultyLevelString; Frontend/QuickRace/CountdownDifficulty; QuickRace` | `Frontend/QuickRace/CountdownDifficultyLevelString` | FUN_00464a40, FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d084` | `Frontend/QuickRace/DifficultyLevelString; Frontend/QuickRace/Difficulty; QuickRace` | `Frontend/QuickRace/DifficultyLevelString` | FUN_00464a40, FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d0b0` | `Frontend/QuickRace/NumOpponentsString; Frontend/QuickRace/NumOpponents; QuickRace` | `Frontend/QuickRace/NumOpponentsString` | FUN_00464a40, FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d0d8` | `Frontend/QuickRace/GhostTypeString; Frontend/QuickRace/Ghost; QuickRace` | `Frontend/QuickRace/GhostTypeString` | FUN_00464a40, FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d0fc` | `Frontend/QuickRace/CurrentModeString; QuickRace` | `Frontend/QuickRace/CurrentModeString` | FUN_00464a40, FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d128` | `Frontend/QuickRace/FlagImageID; QuickRace` | `Frontend/QuickRace/FlagImageID` | FUN_00464a40, FUN_004657d0, FUN_00472480, FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d148` | `Frontend/QuickRace/LogoImageID; QuickRace` | `Frontend/QuickRace/LogoImageID` | FUN_00464a40, FUN_004657d0, FUN_00472480, FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d168` | `Frontend/QuickRace/CurrentRaceString; QuickRace` | `Frontend/QuickRace/CurrentRaceString` | FUN_00464a40, FUN_004657d0, FUN_00472480, FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d190` | `Frontend/QuickRace/CurrentVehicleString; QuickRace` | `Frontend/QuickRace/CurrentVehicleString` | FUN_00464a40, FUN_004657d0, FUN_00472480, FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d1b8` | `Frontend/QuickRace/CurrentManufacturerString; QuickRace` | `Frontend/QuickRace/CurrentManufacturerString` | FUN_00464a40, FUN_004657d0, FUN_00472480, FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d204` | `Frontend/NetworkOptions/CountdownDifficultyList; Frontend/NetworkOptions/CountdownDifficulty` | `Frontend/NetworkOptions/CountdownDifficultyList` | FUN_00465170 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d25c` | `Frontend/NetworkOptions/CheckpointList; Frontend/NetworkOptions/Checkpoint` | `Frontend/NetworkOptions/CheckpointList` | FUN_00465170 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d284` | `Frontend/NetworkOptions/ModeList; Frontend/NetworkOptions/Mode` | `Frontend/NetworkOptions/ModeList` | FUN_00465170 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d2a8` | `Frontend/NetworkOptions/Mode` | `Frontend/NetworkOptions/Mode` | FUN_004656b0, FUN_004657d0, FUN_00465aa0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d330` | `Frontend/NetworkOptions/CountdownDifficulty` | `Frontend/NetworkOptions/CountdownDifficulty` | FUN_00465aa0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d35c` | `Frontend/NetworkOptions/Checkpoint` | `Frontend/NetworkOptions/Checkpoint` | FUN_00465aa0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d3d4` | `Frontend/ControllerOptions/Player2List` | `Frontend/ControllerOptions/Player2List` | FUN_004666b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d3fc` | `Frontend/ControllerOptions/Player1List` | `Frontend/ControllerOptions/Player1List` | FUN_004666b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d434` | `Player1` | `Player1` | FUN_00466d70 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d6cc` | `Frontend/ControllerSetup/GearUpHackText` | `Frontend/ControllerSetup/GearUpHackText` | FUN_0046ad20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d730` | `Frontend/ControllerSetup/Subtitle` | `Frontend/ControllerSetup/Subtitle` | FUN_0046a750 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d770` | `Frontend/ControllerSetup/Type` | `Frontend/ControllerSetup/Type` | FUN_0046ac50, FUN_0046ad20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d7a0` | `Frontend/ControllerSetup/TypeList; Frontend/ControllerSetup/Type` | `Frontend/ControllerSetup/TypeList` | FUN_0046ad20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d948` | `Frontend/GraphicsCardOptions/FullscreenFlash` | `Frontend/GraphicsCardOptions/FullscreenFlash` | FUN_00470520 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d978` | `Frontend/GraphicsCardOptions/FullscreenIndex` | `Frontend/GraphicsCardOptions/FullscreenIndex` | FUN_00470520, FUN_00470830 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d9a8` | `Frontend/GraphicsCardOptions/FullscreenList` | `Frontend/GraphicsCardOptions/FullscreenList` | FUN_0046fa20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d9d4` | `Frontend/GraphicsCardOptions/DepthFlash` | `Frontend/GraphicsCardOptions/DepthFlash` | FUN_00470420 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069d9fc` | `Frontend/GraphicsCardOptions/DepthIndex` | `Frontend/GraphicsCardOptions/DepthIndex` | FUN_00470420, FUN_004708a0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069da24` | `Frontend/GraphicsCardOptions/DepthList` | `Frontend/GraphicsCardOptions/DepthList` | FUN_0046fa20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069da4c` | `Frontend/GraphicsCardOptions/ResFlash` | `Frontend/GraphicsCardOptions/ResFlash` | FUN_00470660 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069da74` | `Frontend/GraphicsCardOptions/ResIndex` | `Frontend/GraphicsCardOptions/ResIndex` | FUN_00470660, FUN_00470910 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069da9c` | `Frontend/GraphicsCardOptions/ResList` | `Frontend/GraphicsCardOptions/ResList` | FUN_0046fa20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069dac4` | `Frontend/GraphicsCardOptions/TNLFlash` | `Frontend/GraphicsCardOptions/TNLFlash` | FUN_004705e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069daec` | `Frontend/GraphicsCardOptions/TNLIndex` | `Frontend/GraphicsCardOptions/TNLIndex` | FUN_004705e0, FUN_00470980 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069db14` | `Frontend/GraphicsCardOptions/TNLList` | `Frontend/GraphicsCardOptions/TNLList` | FUN_0046fa20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069db3c` | `Frontend/GraphicsCardOptions/AdapterFlash` | `Frontend/GraphicsCardOptions/AdapterFlash` | FUN_00470350 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069db68` | `Frontend/GraphicsCardOptions/AdapterIndex` | `Frontend/GraphicsCardOptions/AdapterIndex` | FUN_00470350, FUN_004707c0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069db94` | `Frontend/GraphicsCardOptions/AdapterList` | `Frontend/GraphicsCardOptions/AdapterList` | FUN_0046fa20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069dc04` | `gaFEScreenPCGraphicsCardSetupAI` | `gaFEScreenPCGraphicsCardSetupAI` | FUN_0046f650 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069dc34` | `Frontend/GraphicsCardOptions/DepthPopup` | `Frontend/GraphicsCardOptions/DepthPopup` | FUN_0046fa20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069dc5c` | `Frontend/GraphicsCardOptions/ResPopup` | `Frontend/GraphicsCardOptions/ResPopup` | FUN_0046fa20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069dc84` | `Frontend/GraphicsCardOptions/TNLPopup` | `Frontend/GraphicsCardOptions/TNLPopup` | FUN_0046fa20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069dcac` | `Frontend/GraphicsCardOptions/AdapterPopup` | `Frontend/GraphicsCardOptions/AdapterPopup` | FUN_0046fa20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069dcd8` | `Frontend/GraphicsCardOptions/FullscreenPopup` | `Frontend/GraphicsCardOptions/FullscreenPopup` | FUN_0046fa20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069dea8` | `Frontend/Progress/Class` | `Frontend/Progress/Class` | FUN_00470d90, FUN_00471150, FUN_00471510, FUN_00471870 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069dec0` | `Frontend/Progress/ClassList; Frontend/Progress/Class` | `Frontend/Progress/ClassList` | FUN_00470d90, FUN_00471150, FUN_00471510, FUN_00471870 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069df78` | `Frontend/QuickModeSelect/CountdownDifficultyList; Frontend/QuickModeSelect/CountdownDifficulty` | `Frontend/QuickModeSelect/CountdownDifficultyList` | FUN_00471e20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069dfac` | `Frontend/QuickModeSelect/RaceDifficultyList; Frontend/QuickModeSelect/RaceDifficulty` | `Frontend/QuickModeSelect/RaceDifficultyList` | FUN_00471e20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069dfd8` | `Frontend/QuickModeSelect/NumOpponentsList; Frontend/QuickModeSelect/NumOpponents` | `Frontend/QuickModeSelect/NumOpponentsList` | FUN_00471e20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e004` | `Frontend/QuickModeSelect/ModeList; Frontend/QuickModeSelect/Mode` | `Frontend/QuickModeSelect/ModeList` | FUN_00471e20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e028` | `Frontend/QuickModeSelect/Mode` | `Frontend/QuickModeSelect/Mode` | FUN_00472390, FUN_00472480, FUN_00472770 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e048` | `Frontend/QuickModeSelect/CountdownDifficulty` | `Frontend/QuickModeSelect/CountdownDifficulty` | FUN_00472480, FUN_00472770 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e078` | `Frontend/QuickModeSelect/RaceDifficulty` | `Frontend/QuickModeSelect/RaceDifficulty` | FUN_00472480, FUN_00472770 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e0a0` | `Frontend/QuickModeSelect/NumOpponents` | `Frontend/QuickModeSelect/NumOpponents` | FUN_00472480, FUN_00472770 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e0c8` | `gaFEScreenQuickRaceAI` | `gaFEScreenQuickRaceAI` | FUN_004728c0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e0e0` | `Frontend/VehicleSelect/CarModel` | `Frontend/VehicleSelect/CarModel2` | FUN_004729e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e124` | `Frontend/QuickRace/CurrentVehicle2String; QuickRace` | `Frontend/QuickRace/CurrentVehicle2String` | FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e150` | `QuickRace` | `Frontend/QuickRace/CurrentManufacturer2String` | FUN_00472c10 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e180` | `gaFEScreenRaceDetailsAI` | `gaFEScreenRaceDetailsAI` | FUN_004735b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e198` | `VehicleSetup` | `Frontend/VehicleSetup/SaveSetup4` | FUN_00474af0, FUN_0047a1f0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e1bc` | `VehicleSetup` | `Frontend/VehicleSetup/SaveSetup3` | FUN_00474af0, FUN_00479a20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e1e0` | `VehicleSetup` | `Frontend/VehicleSetup/SaveSetup2` | FUN_00474af0, FUN_00479180 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e204` | `VehicleSetup` | `Frontend/VehicleSetup/SaveSetup1` | FUN_00474af0, FUN_0047a8a0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e228` | `Frontend/VehicleSetup/FrontSuspension/RideHeight; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/RideHeight` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e25c` | `Frontend/VehicleSetup/FrontSuspension/RideHeightMax; Frontend/VehicleSetup/FrontSuspension/RideHeight; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/RideHeightMax` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e290` | `Frontend/VehicleSetup/FrontSuspension/RideHeightMin; Frontend/VehicleSetup/FrontSuspension/RideHeight; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/RideHeightMin` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e2c4` | `Frontend/VehicleSetup/FrontSuspension/AntiRollStiffness; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/AntiRollStiffness` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e2fc` | `Frontend/VehicleSetup/FrontSuspension/AntiRollStiffnessMax; Frontend/VehicleSetup/FrontSuspension/AntiRollStiffness; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/AntiRollStiffnessMax` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e338` | `Frontend/VehicleSetup/FrontSuspension/AntiRollStiffnessMin; Frontend/VehicleSetup/FrontSuspension/AntiRollStiffness; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/AntiRollStiffnessMin` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e374` | `Frontend/VehicleSetup/FrontSuspension/DamperRate; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/DamperRate` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e3a8` | `Frontend/VehicleSetup/FrontSuspension/DamperRateMax; Frontend/VehicleSetup/FrontSuspension/DamperRate; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/DamperRateMax` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e3dc` | `Frontend/VehicleSetup/FrontSuspension/DamperRateMin; Frontend/VehicleSetup/FrontSuspension/DamperRate; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/DamperRateMin` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e410` | `Frontend/VehicleSetup/FrontSuspension/SpringStiffness; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/SpringStiffness` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e448` | `Frontend/VehicleSetup/FrontSuspension/SpringStiffnessMax; Frontend/VehicleSetup/FrontSuspension/SpringStiffness; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/SpringStiffnessMax` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e484` | `Frontend/VehicleSetup/FrontSuspension/SpringStiffnessMin; Frontend/VehicleSetup/FrontSuspension/SpringStiffness; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/SpringStiffnessMin` | FUN_004738e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e4c0` | `Frontend/VehicleSetup/RearSuspension/RideHeight; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/RideHeight` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e4f0` | `Frontend/VehicleSetup/RearSuspension/RideHeightMax; Frontend/VehicleSetup/RearSuspension/RideHeight; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/RideHeightMax` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e524` | `Frontend/VehicleSetup/RearSuspension/RideHeightMin; Frontend/VehicleSetup/RearSuspension/RideHeight; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/RideHeightMin` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e558` | `Frontend/VehicleSetup/RearSuspension/AntiRollStiffness; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/AntiRollStiffness` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e590` | `Frontend/VehicleSetup/RearSuspension/AntiRollStiffnessMax; Frontend/VehicleSetup/RearSuspension/AntiRollStiffness; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/AntiRollStiffnessMax` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e5cc` | `Frontend/VehicleSetup/RearSuspension/AntiRollStiffnessMin; Frontend/VehicleSetup/RearSuspension/AntiRollStiffness; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/AntiRollStiffnessMin` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e608` | `Frontend/VehicleSetup/RearSuspension/DamperRate; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/DamperRate` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e638` | `Frontend/VehicleSetup/RearSuspension/DamperRateMax; Frontend/VehicleSetup/RearSuspension/DamperRate; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/DamperRateMax` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e66c` | `Frontend/VehicleSetup/RearSuspension/DamperRateMin; Frontend/VehicleSetup/RearSuspension/DamperRate; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/DamperRateMin` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e6a0` | `Frontend/VehicleSetup/RearSuspension/SpringStiffness; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/SpringStiffness` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e6d8` | `Frontend/VehicleSetup/RearSuspension/SpringStiffnessMax; Frontend/VehicleSetup/RearSuspension/SpringStiffness; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/SpringStiffnessMax` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e710` | `Frontend/VehicleSetup/RearSuspension/SpringStiffnessMin; Frontend/VehicleSetup/RearSuspension/SpringStiffness; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/SpringStiffnessMin` | FUN_00473df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e748` | `Frontend/VehicleSetup/Engine/RearLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/RearLSDBias` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e774` | `Frontend/VehicleSetup/Engine/RearLSDBiasMax; Frontend/VehicleSetup/Engine/RearLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/RearLSDBiasMax` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e7a0` | `Frontend/VehicleSetup/Engine/RearLSDBiasMin; Frontend/VehicleSetup/Engine/RearLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/RearLSDBiasMin` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e7cc` | `Frontend/VehicleSetup/Engine/FrontLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/FrontLSDBias` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e7f8` | `Frontend/VehicleSetup/Engine/FrontLSDBiasMax; Frontend/VehicleSetup/Engine/FrontLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/FrontLSDBiasMax` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e828` | `Frontend/VehicleSetup/Engine/FrontLSDBiasMin; Frontend/VehicleSetup/Engine/FrontLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/FrontLSDBiasMin` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e858` | `Frontend/VehicleSetup/Engine/CentreLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/CentreLSDBias` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e884` | `Frontend/VehicleSetup/Engine/CentreLSDBiasMax; Frontend/VehicleSetup/Engine/CentreLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/CentreLSDBiasMax` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e8b4` | `Frontend/VehicleSetup/Engine/CentreLSDBiasMin; Frontend/VehicleSetup/Engine/CentreLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/CentreLSDBiasMin` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e8e4` | `Frontend/VehicleSetup/Engine/BrakeBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/BrakeBias` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e90c` | `Frontend/VehicleSetup/Engine/BrakeBiasMax; Frontend/VehicleSetup/Engine/BrakeBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/BrakeBiasMax` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e938` | `Frontend/VehicleSetup/Engine/BrakeBiasMin; Frontend/VehicleSetup/Engine/BrakeBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/BrakeBiasMin` | FUN_004742e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e964` | `Frontend/VehicleSetup/Gearbox/GearType; VehicleSetup` | `Frontend/VehicleSetup/Gearbox/GearType` | FUN_00474780, FUN_00474af0, FUN_0047a540 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e9a0` | `Frontend/VehicleSetup/Gearbox/GearRatio; VehicleSetup` | `Frontend/VehicleSetup/Gearbox/GearRatio` | FUN_00474780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e9c8` | `Frontend/VehicleSetup/Gearbox/GearRatioMax; Frontend/VehicleSetup/Gearbox/GearRatio; VehicleSetup` | `Frontend/VehicleSetup/Gearbox/GearRatioMax` | FUN_00474780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069e9f4` | `Frontend/VehicleSetup/Gearbox/GearRatioMin; Frontend/VehicleSetup/Gearbox/GearRatio; VehicleSetup` | `Frontend/VehicleSetup/Gearbox/GearRatioMin` | FUN_00474780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ea20` | `Frontend/VehicleSetup/Gearbox/GearRatioReal; Frontend/VehicleSetup/Gearbox/GearRatio; VehicleSetup` | `Frontend/VehicleSetup/Gearbox/GearRatioReal` | FUN_00474af0, FUN_0047a540 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ea4c` | `Frontend/VehicleSetup/Engine/RearLSDBiasReal; Frontend/VehicleSetup/Engine/RearLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/RearLSDBiasReal` | FUN_00474af0, FUN_00479c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ea7c` | `Frontend/VehicleSetup/Engine/FrontLSDBiasReal; Frontend/VehicleSetup/Engine/FrontLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/FrontLSDBiasReal` | FUN_00474af0, FUN_00479c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069eaac` | `Frontend/VehicleSetup/Engine/CentreLSDBiasReal; Frontend/VehicleSetup/Engine/CentreLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/CentreLSDBiasReal` | FUN_00474af0, FUN_00479c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069eadc` | `Frontend/VehicleSetup/Engine/BrakeBiasReal; Frontend/VehicleSetup/Engine/BrakeBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/BrakeBiasReal` | FUN_00474af0, FUN_00479c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069eb08` | `Frontend/VehicleSetup/RearSuspension/RideHeightReal; Frontend/VehicleSetup/RearSuspension/RideHeight; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/RideHeightReal` | FUN_00474af0, FUN_00479460 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069eb3c` | `Frontend/VehicleSetup/RearSuspension/AntiRollStiffnessReal; Frontend/VehicleSetup/RearSuspension/AntiRollStiffness; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/AntiRollStiffnessReal` | FUN_00474af0, FUN_00479460 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069eb78` | `Frontend/VehicleSetup/RearSuspension/DamperRateReal; Frontend/VehicleSetup/RearSuspension/DamperRate; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/DamperRateReal` | FUN_00474af0, FUN_00479460 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ebac` | `Frontend/VehicleSetup/RearSuspension/SpringStiffnessReal; Frontend/VehicleSetup/RearSuspension/SpringStiffness; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/SpringStiffnessReal` | FUN_00474af0, FUN_00479460 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ebe8` | `Frontend/VehicleSetup/FrontSuspension/RideHeightReal; Frontend/VehicleSetup/FrontSuspension/RideHeight; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/RideHeightReal` | FUN_00474af0, FUN_0047ab90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ec20` | `Frontend/VehicleSetup/FrontSuspension/AntiRollStiffnessReal; Frontend/VehicleSetup/FrontSuspension/AntiRollStiffness; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/AntiRollStiffnessReal` | FUN_00474af0, FUN_0047ab90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ec5c` | `Frontend/VehicleSetup/FrontSuspension/DamperRateReal; Frontend/VehicleSetup/FrontSuspension/DamperRate; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/DamperRateReal` | FUN_00474af0, FUN_0047ab90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ec94` | `Frontend/VehicleSetup/FrontSuspension/SpringStiffnessReal; Frontend/VehicleSetup/FrontSuspension/SpringStiffness; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/SpringStiffnessReal` | FUN_00474af0, FUN_0047ab90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ecd0` | `Frontend/RaceDetails/Race` | `Frontend/RaceDetails/Race` | FUN_00475120 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ed38` | `gaFEScreenRaceResultsAI` | `gaFEScreenRaceResultsAI` | FUN_004754e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ed50` | `RaceResults` | `Frontend/RaceResults/Car%d` | FUN_00475630 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ed6c` | `Frontend/RaceResults/ResultsType; RaceResults` | `Frontend/RaceResults/ResultsType` | FUN_00475630 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ed90` | `Frontend/RaceResults/PointsList; RaceResults` | `Frontend/RaceResults/PointsList` | FUN_00476090, FUN_00476150 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069edb0` | `Frontend/RaceResults/TimeList; RaceResults` | `Frontend/RaceResults/TimeList` | FUN_00476090, FUN_00476150 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069edd0` | `Frontend/RaceResults/NameList; RaceResults` | `Frontend/RaceResults/NameList` | FUN_00476090, FUN_00476150 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069edf0` | `Frontend/RaceResults/Position2List; RaceResults` | `Frontend/RaceResults/Position2List` | FUN_00476090, FUN_00476150 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ee14` | `Frontend/RaceResults/PositionList; RaceResults` | `Frontend/RaceResults/PositionList` | FUN_00476090, FUN_00476150 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ee38` | `gaFEScreenRaceRetryAI` | `gaFEScreenRaceRetryAI` | FUN_00476bd0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ef4c` | `gaFEScreenRaceSelectAI` | `gaFEScreenRaceSelectAI` | FUN_00477130 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069ef88` | `Frontend/RaceSelect/Rating` | `Frontend/RaceSelect/Rating` | FUN_00477650 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069efac` | `Frontend/RaceSelect/Distance` | `Frontend/RaceSelect/Distance` | FUN_00477650 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069efcc` | `Frontend/RaceSelect/BestTime` | `Frontend/RaceSelect/BestTime` | FUN_00477650 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f028` | `Frontend/RaceSelect/RightArrow` | `Frontend/RaceSelect/RightArrow` | FUN_00477650 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f048` | `Frontend/RaceSelect/LeftArrow` | `Frontend/RaceSelect/LeftArrow` | FUN_00477650 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f068` | `Frontend/RaceSelect/RaceName; Frontend/RaceSelect/Race; RaceName` | `Frontend/RaceSelect/RaceName` | FUN_00477650 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f0a8` | `Frontend/RaceSelect/RaceImage2; Frontend/RaceSelect/Race` | `Frontend/RaceSelect/RaceImage2` | FUN_00477650 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f0c8` | `Frontend/RaceSelect/RaceImage1; Frontend/RaceSelect/Race` | `Frontend/RaceSelect/RaceImage1` | FUN_00477650 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f100` | `Frontend/TitleScreen/PressSpaceText; Frontend/TitleScreen; PressSpaceText` | `Frontend/TitleScreen/PressSpaceText` | FUN_00477cf0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f124` | `Frontend/TitleScreen/ContinueText; Frontend/TitleScreen` | `Frontend/TitleScreen/ContinueText` | FUN_00477cf0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f148` | `Frontend/TitleScreen` | `Frontend/TitleScreen` | FUN_00477cf0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f1b0` | `gaFEScreenVehicleSelectAI` | `gaFEScreenVehicleSelectAI` | FUN_00478230 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f2a0` | `Frontend/VehicleSelect/Endurance` | `Frontend/VehicleSelect/Endurance` | FUN_00478c00 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f2c4` | `Frontend/VehicleSelect/Handling` | `Frontend/VehicleSelect/Handling` | FUN_00478c00 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f2e4` | `Frontend/VehicleSelect/Acceleration` | `Frontend/VehicleSelect/Acceleration` | FUN_00478c00 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f308` | `Frontend/VehicleSelect/Speed` | `Frontend/VehicleSelect/Speed` | FUN_00478c00 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f328` | `Frontend/VehicleSelect/ModelName` | `Frontend/VehicleSelect/ModelName` | FUN_00478c00 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f34c` | `Frontend/VehicleSelect/ManufacturerName` | `Frontend/VehicleSelect/ManufacturerName` | FUN_00478c00 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f374` | `gaFEScreenVehicleSetup2AI` | `gaFEScreenVehicleSetup2AI` | FUN_00479060 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f390` | `Frontend/VehicleSetup/RearSuspension/Screen; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/Screen` | FUN_00479180 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f3bc` | `Frontend/VehicleSetup/RearSuspension/ScreenList; Frontend/VehicleSetup/RearSuspension/Screen; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/ScreenList` | FUN_00479180 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `0069f3ec` | `VehicleSetup` | `Frontend/VehicleSetup/SaveSetup` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f40c` | `Frontend/VehicleSetup/RightArrow; VehicleSetup` | `Frontend/VehicleSetup/RightArrow` | FUN_00479460, FUN_00479c90, FUN_0047a540, FUN_0047ab90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f430` | `Frontend/VehicleSetup/LeftArrow; VehicleSetup` | `Frontend/VehicleSetup/LeftArrow` | FUN_00479460, FUN_00479c90, FUN_0047a540, FUN_0047ab90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f450` | `Frontend/VehicleSetup/RearSuspension/RideHeightText; Frontend/VehicleSetup/RearSuspension/RideHeight; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/RideHeightText` | FUN_00479460 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f48c` | `Frontend/VehicleSetup/RearSuspension/AntiRollStiffnessText; Frontend/VehicleSetup/RearSuspension/AntiRollStiffness; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/AntiRollStiffnessText` | FUN_00479460 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f4c8` | `Frontend/VehicleSetup/RearSuspension/DamperRateText; Frontend/VehicleSetup/RearSuspension/DamperRate; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/DamperRateText` | FUN_00479460 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f4fc` | `Frontend/VehicleSetup/RearSuspension/SpringStiffnessText; Frontend/VehicleSetup/RearSuspension/SpringStiffness; VehicleSetup` | `Frontend/VehicleSetup/RearSuspension/SpringStiffnessText` | FUN_00479460 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f540` | `Frontend/VehicleSetup/AntiRollStiffnessFader; VehicleSetup` | `Frontend/VehicleSetup/AntiRollStiffnessFader` | FUN_00479790, FUN_0047aec0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f570` | `Frontend/VehicleSetup/RideHeightFader; VehicleSetup` | `Frontend/VehicleSetup/RideHeightFader` | FUN_00479790, FUN_0047aec0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f598` | `Frontend/VehicleSetup/DamperRateFader; VehicleSetup` | `Frontend/VehicleSetup/DamperRateFader` | FUN_00479790, FUN_0047aec0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f5c0` | `Frontend/VehicleSetup/SpringStiffnessFader; VehicleSetup` | `Frontend/VehicleSetup/SpringStiffnessFader` | FUN_00479790, FUN_0047aec0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f5ec` | `gaFEScreenVehicleSetup3AI` | `gaFEScreenVehicleSetup3AI` | FUN_00479900 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f608` | `Frontend/VehicleSetup/General/Screen; VehicleSetup` | `Frontend/VehicleSetup/General/Screen` | FUN_00479a20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f630` | `Frontend/VehicleSetup/General/ScreenList; Frontend/VehicleSetup/General/Screen; VehicleSetup` | `Frontend/VehicleSetup/General/ScreenList` | FUN_00479a20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f65c` | `Frontend/VehicleSetup/Engine/RearLSDBiasText; Frontend/VehicleSetup/Engine/RearLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/RearLSDBiasText` | FUN_00479c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f68c` | `Frontend/VehicleSetup/Engine/FrontLSDBiasText; Frontend/VehicleSetup/Engine/FrontLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/FrontLSDBiasText` | FUN_00479c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f6bc` | `Frontend/VehicleSetup/Engine/CentreLSDBiasText; Frontend/VehicleSetup/Engine/CentreLSDBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/CentreLSDBiasText` | FUN_00479c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f6ec` | `Frontend/VehicleSetup/Engine/BrakeBiasText; Frontend/VehicleSetup/Engine/BrakeBias; VehicleSetup` | `Frontend/VehicleSetup/Engine/BrakeBiasText` | FUN_00479c90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f720` | `Frontend/VehicleSetup/RearLSDFader; VehicleSetup` | `Frontend/VehicleSetup/RearLSDFader` | FUN_00479f60 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f744` | `Frontend/VehicleSetup/FrontLSDFader; VehicleSetup` | `Frontend/VehicleSetup/FrontLSDFader` | FUN_00479f60 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f768` | `Frontend/VehicleSetup/CentreLSDFader; VehicleSetup` | `Frontend/VehicleSetup/CentreLSDFader` | FUN_00479f60 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f790` | `Frontend/VehicleSetup/BrakeBiasFader; VehicleSetup` | `Frontend/VehicleSetup/BrakeBiasFader` | FUN_00479f60 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f7b8` | `gaFEScreenVehicleSetup4AI` | `gaFEScreenVehicleSetup4AI` | FUN_0047a0d0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f7d4` | `Frontend/VehicleSetup/Gearbox/GearTypeList; Frontend/VehicleSetup/Gearbox/GearType; VehicleSetup` | `Frontend/VehicleSetup/Gearbox/GearTypeList` | FUN_0047a1f0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f800` | `Frontend/VehicleSetup/Gearbox/Screen; VehicleSetup` | `Frontend/VehicleSetup/Gearbox/Screen` | FUN_0047a1f0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f828` | `Frontend/VehicleSetup/Gearbox/ScreenList; Frontend/VehicleSetup/Gearbox/Screen; VehicleSetup` | `Frontend/VehicleSetup/Gearbox/ScreenList` | FUN_0047a1f0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `0069f854` | `Frontend/VehicleSetup/GearRatioFader; VehicleSetup` | `Frontend/VehicleSetup/GearRatioFader` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f87c` | `Frontend/VehicleSetup/GearRightArrow; VehicleSetup` | `Frontend/VehicleSetup/GearRightArrow` | FUN_0047a540 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f8a4` | `Frontend/VehicleSetup/GearLeftArrow; VehicleSetup` | `Frontend/VehicleSetup/GearLeftArrow` | FUN_0047a540 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f8c8` | `Frontend/VehicleSetup/Gearbox/GearRatioText; Frontend/VehicleSetup/Gearbox/GearRatio; VehicleSetup` | `Frontend/VehicleSetup/Gearbox/GearRatioText` | FUN_0047a540 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f8f4` | `gaFEScreenVehicleSetupAI` | `gaFEScreenVehicleSetupAI` | FUN_0047a780 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f910` | `Frontend/VehicleSetup/FrontSuspension/Screen; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/Screen` | FUN_0047a8a0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f940` | `Frontend/VehicleSetup/FrontSuspension/ScreenList; Frontend/VehicleSetup/FrontSuspension/Screen; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/ScreenList` | FUN_0047a8a0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f974` | `Frontend/VehicleSetup/FrontSuspension/RideHeightText; Frontend/VehicleSetup/FrontSuspension/RideHeight; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/RideHeightText` | FUN_0047ab90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f9ac` | `Frontend/VehicleSetup/FrontSuspension/AntiRollStiffnessText; Frontend/VehicleSetup/FrontSuspension/AntiRollStiffness; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/AntiRollStiffnessText` | FUN_0047ab90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069f9e8` | `Frontend/VehicleSetup/FrontSuspension/DamperRateText; Frontend/VehicleSetup/FrontSuspension/DamperRate; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/DamperRateText` | FUN_0047ab90 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `0069fa20` | `Frontend/VehicleSetup/FrontSuspension/SpringStiffnessText; Frontend/VehicleSetup/FrontSuspension/SpringStiffness; VehicleSetup` | `Frontend/VehicleSetup/FrontSuspension/SpringStiffnessText` | FUN_0047ab90 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006a5dc4` | `WildCat` | `BOWLER WILDCAT` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006a93e4` | `LandCruiser` | `TOYOTA LANDCRUISER` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006a94c4` | `WildCat` | `WILDCAT` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006a9500` | `LandCruiser` | `LANDCRUISER` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006a9e2c` | `PaceNotes` | `hud/pacenotes` | FUN_0047c1b0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006a9f54` | `Misc/Checkpoints/checkpoint` | `misc/checkpoints/checkpoint` | FUN_0047cca0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006a9fb8` | `TimeToFirstCheckpoint` | `TimeToFirstCheckpoint` | FUN_0047cca0, FUN_0047e030, FUN_00482590 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006a9fd0` | `gaRacePostFirstSplitTimeAI` | `gaRacePostFirstSplitTimeAI` | FUN_0047cca0, FUN_0047e030, FUN_004823e0, FUN_00482590 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006a9fec` | `StartSplitTime` | `StartSplitTime` | FUN_0047cca0, FUN_0047d710 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aa0fc` | `gaRaceFinishAI` | `gaRaceFinishAI` | FUN_0047f8a0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006aa120` | `TimeToFirstCheckpoint` | `Race/Countdown/TimeToFirstCheckpoint` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aa174` | `gaRaceFinishAreaAI` | `gaRaceFinishAreaAI` | FUN_004802e0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006aa188` | `gaRaceFinishAreaAI` | `gaRaceFinishAreaAI: No FinishArea markers found! ` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aa1d8` | `gaRaceLineAI` | `gaRaceLineAI` | FUN_00480730 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aa1e8` | `RaceLine` | `***Raceline not found in scene*** ` | FUN_004808a0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aa2a0` | `gaRacePaceNoteAI` | `gaRacePaceNoteAI` | FUN_00481e80, FUN_00482250 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aa310` | `Frontend/QuickRace/CountdownDifficulty; QuickRace` | `Frontend/QuickRace/CountdownDifficulty` | FUN_00482910, FUN_004a1c70, FUN_004a1ca0 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006aa3b0` | `SplitTimes` | `SplitTimes: Split Time %d initialised ` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006aa3d8` | `RaceLine` | `No raceline found - SplitTime percentage value not filled in ` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aa4c8` | `gaRaceStarterAI` | `gaRaceStarterAI` | FUN_00483e60 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aa63c` | `gaRaceTimerAI` | `gaRaceTimerAI` | FUN_00484df0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aa678` | `gaDefaultParamBrokerRegistration` | `gaDefaultParamBrokerRegistration` | FUN_00485550, FUN_00485610 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aa69c` | `CarModelDataFile` | `CarModelDataFile` | FUN_00485610, FUN_004856d0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aa6c0` | `gaDefaultTyreParamBrokerRegistration` | `gaDefaultTyreParamBrokerRegistration` | FUN_00486380, FUN_00486440 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab094` | `gaHudAiCarDamage` | `gaHudAiCarDamage` | FUN_00499f50, FUN_0049a070 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006ab11c` | `Damage/MAX_Tyre` | `Damage/MAX_Tyre` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006ab12c` | `Damage/MAX_Gear` | `Damage/MAX_Gear` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006ab13c` | `Damage/MAX_Suspension` | `Damage/MAX_Suspension` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006ab154` | `Damage/MAX_Engine` | `Damage/MAX_Engine` | no containing function resolved |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006ab168` | `Damage/MAX_SteeringWheel` | `Damage/MAX_SteeringWheel` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab1bc` | `gaHudAiGameTimer` | `gaHudAiGameTimer` | FUN_0049abd0, FUN_0049acd0, FUN_0049b3d0, FUN_0049bc20, FUN_0049c150 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab1dc` | `gaHudAiGearCounter` | `gaHudAiGearCounter` | FUN_0049af70, FUN_0049b040 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab1f0` | `gaHudAiGPSNeedle` | `gaHudAiGPSNeedle` | FUN_0049b280 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab24c` | `gaHudAiOffCourse` | `gaHudAiOffCourse` | FUN_0049beb0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab264` | `gaHudAiPaceNotes` | `gaHudAiPaceNotes` | FUN_0049c040 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab2f0` | `gaHudAiRaceComplete` | `gaHudAiRaceComplete` | FUN_0049c840, FUN_0049c910 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab318` | `gaHudAiRaceProgress` | `gaHudAiRaceProgress` | FUN_0049ccc0, FUN_0049cdb0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab3b8` | `gaHudAiRaceProgressBar` | `gaHudAiRaceProgressBar` | FUN_0049d310, FUN_0049d3e0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab410` | `gaHudAiSpeedCounter` | `gaHudAiSpeedCounter` | FUN_0049d920, FUN_0049d9f0, FUN_0049e6a0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab42c` | `gaHudAiSpeedDial` | `gaHudAiSpeedDial` | FUN_0049dc30 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab524` | `gaHudAiSpeedNeedle` | `gaHudAiSpeedNeedle` | FUN_0049e130, FUN_0049e200 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab538` | `gaHudAiSpeedText` | `gaHudAiSpeedText` | FUN_0049e5d0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab54c` | `gaHudAiSplitTime` | `gaHudAiSplitTime` | FUN_0049e880, FUN_0049e990 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab560` | `gaHudAiWrongWay` | `gaHudAiWrongWay` | FUN_0049ecb0, FUN_0049ed80 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab570` | `gaHudLoader` | `gaHudLoader` | FUN_0049f0a0, FUN_0049f170 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab5c8` | `gaHudRankAi` | `gaHudRankAi` | FUN_0049f380, FUN_0049f450 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab704` | `RaceName` | `Race/RaceName` | FUN_0049f870, FUN_004b0c90, FUN_004b2f50, FUN_004b4060 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006ab8d4` | `Frontend/ShowEffects` | `Frontend/ShowEffects` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab964` | `Frontend/QuickRace/Car1; QuickRace` | `Frontend/QuickRace/Car1` | FUN_004a19e0, FUN_004a1a40 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab97c` | `Frontend/QuickRace/Car0; QuickRace` | `Frontend/QuickRace/Car0` | FUN_004a19e0, FUN_004a1a40 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab994` | `Frontend/QuickRace/Track; QuickRace` | `Frontend/QuickRace/Track` | FUN_004a1a90, FUN_004a1ac0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab9b0` | `Frontend/QuickRace/Mode; QuickRace` | `Frontend/QuickRace/Mode` | FUN_004a1af0, FUN_004a1b20 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab9c8` | `Frontend/QuickRace/Ghost; QuickRace` | `Frontend/QuickRace/Ghost` | FUN_004a1b80 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ab9e4` | `Frontend/QuickRace/NumOpponents; QuickRace` | `Frontend/QuickRace/NumOpponents` | FUN_004a1bb0, FUN_004a1be0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aba04` | `Frontend/QuickRace/Difficulty; QuickRace` | `Frontend/QuickRace/Difficulty` | FUN_004a1c10, FUN_004a1c40 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aba44` | `SplitScreen` | `Frontend/SplitScreen` | FUN_004a1d30, FUN_004a1d60 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006aba7c` | `Frontend/SkipTitles` | `Frontend/SkipTitles` | FUN_004a1fc0 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006ac998` | `gaAiCloudSetUp` | `gaAiCloudSetUp` | FUN_004a4970 |
| CONFIRMED_BY_EXE_STRING_ONLY | 9.10.0 | `006aca20` | `Frontend/Active` | `FrontEnd/Active` | no containing function resolved |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006acb2c` | `ControllerCarParams` | `ControllerCarParams` | FUN_004a61f0, FUN_005558e0, FUN_005ff240 |
| CONFIRMED_BY_EXE_XREF | 9.10.0 | `006acba0` | `gaBootAICar` | `gaBootAICar` | FUN_004a9e00 |

## Interpretation boundaries

- Directory presence proves corpus membership, not runtime loading or gameplay use.
- A direct xref supports executable reachability from that literal; it does not establish the full consumer semantics without caller/callee and decompilation review.
- Config element and attribute names are semantic search anchors, not typed runtime field names until code paths corroborate them.
- Archive, extracted assets, and executable imports remain external and read-only.
