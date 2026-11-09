"""Use the existing Vehicle SDK private host packager for the combined registry."""
import argparse
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]


def package(candidate,extra,renderer_host):
    candidate=Path(candidate).resolve()
    if not candidate.is_relative_to((ROOT/'.research-output/course-cap2').resolve()):raise ValueError('Private COURSE-CAP2 candidate required')
    config=json.loads((candidate/'build-input.json').read_text())
    vehicle=Path(config['vehicle_source'])
    sys.path[:0]=[str(vehicle/'tools'),str(vehicle/'src')]
    from package_vehicle_registry_candidate import package as existing_package
    return existing_package(candidate,extra,renderer_host,registered_ai=True,research_root=ROOT/'.research-output')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['candidate','extra','renderer-host']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(package(a.candidate,a.extra,a.renderer_host),indent=2))
