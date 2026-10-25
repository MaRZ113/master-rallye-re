"""Report real DX/DXT working sets and a bounded native-cache LRU prediction."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from master_rallye.addon_sdk.texture_budget import texture_working_set, simulate_texture_cache


def analyze(root, background_bytes):
    report = texture_working_set(root)
    sizes = {s: t['cache_bytes'] for s, t in report['textures'].items()}
    if background_bytes:
        sizes['<background-reserve>'] = background_bytes
    for model in report['models'].values():
        seq = (['<background-reserve>'] if background_bytes else []) + model['request_sequence']
        model['lru_prediction'] = simulate_texture_cache(sizes, seq)
    report['background_reserve_bytes'] = background_bytes
    report['prediction_boundary'] = 'DX serialized binding order with an explicit synthetic background reserve; not actual game draw order or measured FPS'
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('assets', type=Path)
    p.add_argument('--background-bytes', type=int, default=8 * 1024 * 1024)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.background_bytes < 0:
        p.error('background reserve must be nonnegative')
    report = analyze(a.assets, a.background_bytes)
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('cache_bytes', 'unique_textures', 'background_reserve_bytes')}, indent=2))
