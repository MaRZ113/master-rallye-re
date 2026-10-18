# HUD-DIAG2: PC child UI entities (opponent list, MPH/KPH text)

## Why

`PS2HudHidePcOnly=1` did not hide two PC elements:

* **"KPH"/"MPH".** F10 frame 15820/5594 attributes its K/P/H glyph draws to the UI entity 0x2ba0ab0. That
  entity does not resolve to `SpeedVelocityText`.
* **The opponent list.** The PC `gaHudTimeDiffsAi` (vtable 0x691058, init 0x4ab040) creates 3 unnamed child
  entities (0x4aad60: entity 0x78 + en2d 0x90, name id +0x5c = 0) and keeps them at AI +0xc/+0x10/+0x14. The
  egg-name registry cannot name them.

The link from an egg to its AI objects (and so to the AI's child entities) is not recovered statically. The
working hypothesis is the four intrusive lists at entity +0x18/+0x24/+0x30/+0x3c set up by the entity
constructor 0x4f5670.

## What it logs

With `Diagnostics=1` and a certified race HUD, each new UI-draw entity is logged once (at most 96 per race):

```
{"type":"ps2_hud_entity","entity":..,"id":..,"name":..,"x":..,"y":..,"bytes":<0x80 bytes>,
 "lists":[[node,owner,owner_vtable]...] x4}
```

The record is read-only and draws nothing.

## Runtime run

1. Replace `d3d8.dll`.
2. Keep `Diagnostics=1`.
3. Do one Practice race and one race with AI opponents, 10-20 s each. No F10 is needed.
4. Send the newest `MRRRenderer/logs/session-*.jsonl`.
