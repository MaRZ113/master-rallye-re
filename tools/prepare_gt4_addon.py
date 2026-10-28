"""Bridge an imported GT4 scene candidate into the existing Vehicle SDK.

Creates a fresh private donor authoring tree and editable addon project. Does
not install, allocate new engine capacity, launch the game, or copy GT assets
into the repository's tracked source directories.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.project import initialize_project
from master_rallye.addon_sdk.ui_assets import BANKS
from master_rallye.scene_dx_writer import validate_scene_dx
from generate_vehicle_ui_previews import render_sources


def prepare(candidate,donor,profile,output,*,ui_from=None):
    from master_rallye.addon_sdk.import_project import prepare as shared_prepare
    return shared_prepare(candidate,donor,profile,output,ui_from=ui_from,render_ui=render_sources)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--donor',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--ui-from',type=Path);a=p.parse_args()
    print(prepare(a.candidate.resolve(),a.donor.resolve(),a.profile.resolve(),a.output.resolve(),ui_from=a.ui_from.resolve() if a.ui_from else None))
