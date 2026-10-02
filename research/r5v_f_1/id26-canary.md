# ID26 independent-record red canary

The earlier ID26 Landcruiser profile copied donor ID0's visible properties,
so identical behavior did not prove that late race code reads the new record
independently. The cleanup candidate changes only ID26's proven
`VehicleRecord.race_colour_rgba` tail:

```text
record +0x24: R = 1.0  (0x3F800000)
record +0x28: G = 0.0  (0x00000000)
record +0x2C: B = 0.0  (0x00000000)
record +0x30: A = 1.0  (0x3F800000)
```

R5V-E0.1d.2 established the four-float producer/consumer path from the
VehicleRecord tail to `Race/CarN/Colour` and the HUD progress marker; the user
reported a red ID25 control test. This cleanup candidate supplies red through
the original full VehicleRecord initializer for ID26. It uses no XML tint,
consumer bypass or raw record copy. The original ID0 initialization is not
patched; its stock colour remains the control.

## P1 check, after P0 FULL PASS only

1. Select ID26 and inspect the player progress marker: it should be red.
2. Return to the frontend, select original donor ID0 and inspect its marker:
   it should retain the stock donor colour.
3. Confirm ID25/Trooper remains selectable and unaffected.

Only this A/B result closes `ID26 physical record = independently
runtime-confirmed`. The cleanup candidate has not been run in the game.
