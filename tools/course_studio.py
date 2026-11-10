"""Open/validate/stage a Course using the same transaction as Blender."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from master_rallye.course_studio import CourseStudio, encoded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--resource-root', type=Path)
    parser.add_argument('--race-id', type=int)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--template-race-id', type=int)
    parser.add_argument('--name')
    parser.add_argument('--compose-template', type=Path)
    args = parser.parse_args()
    session = CourseStudio(args.source, resource_root=args.resource_root, race_id=args.race_id)
    if args.output:
        catalog = json.loads(args.catalog.read_text()) if args.catalog else None
        report = session.export(args.output, registry=catalog, template_race_id=args.template_race_id, name=args.name)
        if args.compose_template:
            config = json.loads(args.compose_template.read_text())
            config['course_manifest'] = str(args.output.resolve() / 'courses.json')
            config['resource_overrides'] = json.loads((args.output / 'resource-overrides.json').read_text())
            (args.output / 'compose.json').write_bytes(encoded(config))
        print(json.dumps({'status': report['status'], 'files': len(report['files']), 'output': str(args.output.resolve())}, indent=2))
    else:
        findings = session.validate()
        print(json.dumps([asdict(f) for f in findings], indent=2))
        return int(any(f.severity == 'ERROR' for f in findings))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
