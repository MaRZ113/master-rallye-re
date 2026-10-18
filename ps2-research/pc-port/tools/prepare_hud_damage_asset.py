"""Extract the original PS2 HUD damage atlases (HUD/HUD-DAMAGE_000.GXI, _001.GXI) into ignored private storage.

PS2 gaHudAiCarDamage / gaHudAiCarDamage1 draw HUD-DAMAGE.PSB images 0..5 from these two 64x64 pages;
evidence: ps2-research/hud-dump1/findings.md (GS dumps, EE 1414e8/142b90).
"""
from pathlib import Path
import importlib.util, hashlib, sys

PORT = Path(__file__).resolve().parents[1]
PAGES = {  # TNG payload identity (ps2-research/ui/texture-metadata.json)
    'HUD-DAMAGE_000.GXI': '1b11baddf6e0d414cad52f485ac79a9be1841ea012d964267381d6228c2820c6',
    'HUD-DAMAGE_001.GXI': 'cb58cda5f89fdeb98958b6b6e5375489ebc81a32048dd586a13cf930e965ca45',
}
SIZE = 8 + 64 * 64 * 4


def main(print_only=False):
    spec = importlib.util.spec_from_file_location('asset_common', PORT/'docs/full-coverage/vehicles/audit.py')
    a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
    a.w.verify_inputs(a.PS2)
    manifest, _ = a.t.load_pak(a.PS2/'TNG.PAK')
    for name, sha in PAGES.items():
        suffix = chr(92) + 'HUD' + chr(92) + name
        entry = next(e for e in manifest['entries'] if e['kind'] == 'file' and e['path'].upper().endswith(suffix))
        raw, _ = a.t.read_payload(entry, a.PS2/'TNG.000')
        digest = hashlib.sha256(raw).hexdigest()
        alpha = max(raw[8+3::4]) if len(raw) == SIZE else None
        if print_only:
            print(entry['path'], len(raw), digest, raw[:8].hex(), 'max_alpha', alpha); continue
        if len(raw) != SIZE or (sha and digest != sha):
            raise ValueError('Canonical HUD damage page identity failed: ' + name)
        target = PORT/'.assets/hud'/('PS2HudDamage' + name[-7:-4] + '.gxi')
        if target.is_symlink() or target.parent.is_symlink():
            raise ValueError('Private output link rejected')
        if target.exists() and target.read_bytes() != raw:
            raise ValueError('Existing unique asset preserved')
        target.write_bytes(raw); print(target.name, digest)


if __name__ == '__main__':
    main('--print' in sys.argv)
