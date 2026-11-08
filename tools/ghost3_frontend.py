#!/usr/bin/env python3
"""GHOST1 G3: add the demo-style GhostMode panel to the retail QuickModeSelect.xml.

The retail screen keeps three mode panels (Egg Group = mode + 2: Solo 2, SingleRace 3,
Countdown 4). G3 appends mode 3 "GHOST" (text 0x3E:1) with a GhostMode panel in Egg
Group 5, built from the retail SingleRaceMode widgets so it matches the retail layout:

* Mode       (button 10, up/down 11) - shared ModeList/Mode/ModeText keys;
* GhostType  (button 11, up/down 10) - Frontend/QuickModeSelect/GhostList, /Ghost, /GhostText,
  label = text group 28 index 2 ("GHOST TYPE", localised in the EXE);
* ModeText / GhostTypeText display eggs;
* GhostLeftArrow2-2 / GhostRightArrow2-2: GHOST TYPE row arrows (clones of the difficulty-row
  arrows, status keys Frontend/QuickModeSelect/LeftArrowGhost / RightArrowGhost set by cave focus).

Button 10 = 3*mode+1, the focus value written by the patched 0x47A1C2 update.
The output is a loose override for DataScene/FrontendScreens/QuickModeSelect.xml.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def egg(block: str, name: str) -> str:
    m = re.search(r'( *)<Egg Name="%s">.*?\n\1</Egg>\n' % re.escape(name), block, re.S)
    if not m:
        raise SystemExit(f"egg {name} not found")
    return m.group(0)


def setv(text: str, name: str, value: str) -> str:
    pat = r'(<Value Name="%s" Type="[^"]+" Value=")[^"]*(")' % re.escape(name)
    new, n = re.subn(pat, lambda m: m.group(1) + value + m.group(2), text)
    if n == 0:
        raise SystemExit(f"value {name} not found")
    return new


def build(src: str) -> str:
    m = re.search(r'( *)<List Name="SingleRaceMode">\n(.*?)\n\1</List>\n', src, re.S)
    if not m:
        raise SystemExit("SingleRaceMode list not found")
    indent, body = m.group(1), m.group(2) + "\n"
    if '<List Name="GhostMode">' in src:
        raise SystemExit("GhostMode already present")

    mode = egg(body, "Mode")
    mode = setv(mode, "Egg Group", "5")
    mode = setv(mode, "Button ID", "10")
    mode = setv(mode, "Up Path", "11")
    mode = setv(mode, "Down Path", "11")

    mode_text = setv(egg(body, "ModeText"), "Egg Group", "5")

    ghost = egg(body, "Difficulty").replace('<Egg Name="Difficulty">', '<Egg Name="GhostType">')
    ghost = setv(ghost, "Egg Group", "5")
    ghost = setv(ghost, "Text ID Index#", "2")
    ghost = setv(ghost, "Button ID", "11")
    ghost = setv(ghost, "Up Path", "10")
    ghost = setv(ghost, "Down Path", "10")
    ghost = setv(ghost, "StringList*", "Frontend/QuickModeSelect/GhostList")
    ghost = setv(ghost, "Value*", "Frontend/QuickModeSelect/Ghost")
    ghost = setv(ghost, "CurrentText*", "Frontend/QuickModeSelect/GhostText")

    ghost_text = egg(body, "DifficultyText").replace('<Egg Name="DifficultyText">', '<Egg Name="GhostTypeText">')
    ghost_text = setv(ghost_text, "Egg Group", "5")
    ghost_text = setv(ghost_text, "Text*", "Frontend/QuickModeSelect/GhostText")

    arrows = ""
    for name, key in (("LeftArrow2-2", "LeftArrowGhost"), ("RightArrow2-2", "RightArrowGhost")):
        arrow = egg(body, name).replace(f'<Egg Name="{name}">', f'<Egg Name="Ghost{name}">')
        arrow = setv(arrow, "Egg Group", "5")
        arrow = setv(arrow, "Arrow Status*", f"Frontend/QuickModeSelect/{key}")
        arrows += arrow
    panel = f'{indent}<List Name="GhostMode">\n{ghost}{ghost_text}{mode}{mode_text}{arrows}{indent}</List>\n'
    anchor = f'{indent}<List Name="QuickModeSelect">'
    if anchor not in src:
        raise SystemExit("QuickModeSelect list not found")
    return src.replace(anchor, panel + anchor, 1)


def main_args(source: Path, output: Path) -> None:
    raw = source.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("latin-1").replace("\r\n", "\n")
    out = build(text).replace("\n", newline)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(out.encode("latin-1"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", type=Path, help="retail DataScene/FrontendScreens/QuickModeSelect.xml")
    ap.add_argument("output", type=Path)
    a = ap.parse_args()
    main_args(a.source, a.output)


if __name__ == "__main__":
    main()
