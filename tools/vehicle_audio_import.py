#!/usr/bin/env python3
"""Compile an explicit local custom-audio profile to private SDK resources."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye.addon_sdk.audio_profile import compile_audio
from master_rallye.addon_sdk.manifest import canonical_json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',type=Path,required=True);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('output already exists')
    # Compile and validate first; a malformed input cannot leave a partial asset.
    resources,report=compile_audio(json.loads(a.profile.read_text(encoding='utf-8')),a.source_root)
    a.output.mkdir(parents=True)
    for name,data in resources.items():
        dest=a.output/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    (a.output/'audio-build.json').write_bytes(canonical_json(report));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
