"""Isolated game host for SDK candidates: hardlinked immutable data, copied mutable files.

Mirrors the owner's game folder except loader wrappers the SDK launcher refuses
(dinput8.dll etc.) and development folders. Large data files are hardlinked
(no extra disk space); configuration/state files (.ini/.xml/.log/.txt) are
copied so the host can never write through to the owner's originals.
"""
import argparse, os, shutil
from pathlib import Path

GAME_ITEMS = ['MRallye.exe', 'MRallye.ico', 'StartMR.exe', 'Readme.txt', 'Data.sma', 'd3d8.dll',
              'Data', 'DataAudio', 'DataGame', 'DataGx', 'DataScene', 'DataVideo', 'Ghosts',
              'MRRRenderer', 'PS2Grass', 'PS2Hud', 'PS2Vehicles']
COPIED_SUFFIXES = {'.ini', '.xml', '.log', '.txt', '.cfg', '.json', '.xml#'}


def place(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() in COPIED_SUFFIXES or src.name.endswith('#'):
        shutil.copy2(src, dst)
    else:
        os.link(src, dst)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', required=True); p.add_argument('--output', required=True)
    a = p.parse_args(); game = Path(a.game); out = Path(a.output)
    if out.exists():
        raise SystemExit('fresh host folder required')
    out.mkdir(parents=True)
    for item in GAME_ITEMS:
        src = game / item
        if src.is_file():
            place(src, out / item)
        elif src.is_dir():
            for f in src.rglob('*'):
                if f.is_file():
                    place(f, out / f.relative_to(game))
    for f in game.iterdir():   # top-level renderer/port configuration
        if f.is_file() and f.suffix.lower() == '.ini' and not f.name.lower().startswith('mrallyerandomizer') and 'extra' not in f.name.lower():
            shutil.copy2(f, out / f.name)
    print(out)


if __name__ == '__main__':
    main()
