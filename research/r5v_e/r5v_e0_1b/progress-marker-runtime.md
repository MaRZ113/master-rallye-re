# Progress marker runtime evidence

The prior E0.1a ID25 selector test is the only runtime diagnostic relevant to this phase: SmallCarSheet 0→29 changed the top-left and Results icons to Forklift frame 29, while the bottom progress marker remained aquamarine. Trooper gameplay remained normal.

Static retail HUD XML binds `ProgressCar0..7` to `hud-template` image bank frame 3. The asset is a generic white-car silhouette. Retail `FUN_004A74A0` independently reads `Race/CarN/Colour` and applies four components as a render-object tint. The ghost branch uses white RGB and half alpha.

The exact producer of `Race/Car0/Colour`, its normal runtime float values, and whether it represents Player1, a race participant, a controller, or a vehicle remain unresolved. Therefore there is no isolated color candidate and no color runtime test package. The previous aquamarine observation does not identify the producer.

Status: **consumer and generic artwork proven; upstream color semantics UNKNOWN; runtime color diagnostic BLOCKED**.
