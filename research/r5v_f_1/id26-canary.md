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

## Owner-reported runtime result

The F.2 master prompt reports that ID26's progress marker was red in the
cleanup candidate, confirming that the race path consumed the red values from
VehicleRecord[26]. The report does not include a runtime observation of ID0's
marker. Static candidate operations leave ID0 initialization untouched, but
that is not a substitute for an A/B runtime comparison. The F.2 prompt says
the ID0 recheck is useful and does not block the Mercedes source audit.
