"""Use the SDK's original-table validator; emit metadata, never game assets."""
import argparse
import hashlib
import json
import sys
from pathlib import Path


def audit(xml_path, sdk_root):
    sdk_root = Path(sdk_root).resolve()
    sys.path.insert(0, str(sdk_root/'src'))
    from master_rallye.addon_sdk.vehicle_setup import tyre_table
    raw = Path(xml_path).read_bytes()
    families = {}
    for name in ('tarmac', 'harddirt', 'gravel', 'grass', 'mud'):
        table = tyre_table(raw, name)
        families[name] = {'records': 5, 'fields': len(table['fields']),
                          'table_sha256': table['table_sha256']}
    return {'schema': 'extra-options-tire-audit/1', 'source_sha256': hashlib.sha256(raw).hexdigest(),
            'families': families, 'stock': 'native passthrough; no generic replacement',
            'runtime_consumption': 'NOT TESTED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml', type=Path, required=True)
    parser.add_argument('--sdk-root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.xml, args.sdk_root), indent=2))
