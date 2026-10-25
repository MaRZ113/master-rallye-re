"""Inspect explicitly selected mechanical draws; optionally write a rest-pose copy."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from master_rallye.addon_sdk.visual_fitment import diagnose_mechanics, translate_mechanics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--corrected-model', type=Path, help='new private file; static translation only')
    a = p.parse_args()
    if a.output.exists() or (a.corrected_model and a.corrected_model.exists()):
        raise ValueError('output exists; use fresh report/model paths')
    if a.output.resolve() == a.model.resolve() or (a.corrected_model and a.corrected_model.resolve() == a.model.resolve()):
        raise ValueError('source model must remain immutable')
    if a.corrected_model and a.corrected_model.resolve() == a.output.resolve():
        raise ValueError('report and corrected model need distinct output paths')
    raw = a.model.read_bytes()
    definition = json.loads(a.profile.read_text())
    if a.corrected_model:
        corrected, report = translate_mechanics(raw, definition)
        a.corrected_model.parent.mkdir(parents=True, exist_ok=True)
        a.corrected_model.write_bytes(corrected)
    else:
        report = diagnose_mechanics(raw, definition)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'groups': len(report['groups']),
                      'max_hub_difference_m': max(g['hub_difference_m'] for g in report['groups']),
                      'runtime_qualified': False}))


if __name__ == '__main__':
    main()
