"""Extract the original PS2 ground detail noise (CommonTextures/NOISE.GXI) into ignored private storage.

PS2 ground shader (mode 4) subtracts this texture in a second GS pass (DECAL, ALPHA Cd-Cs);
evidence: ps2-research/course-light1/findings.md (GS dumps Turkey2/France1).
"""
from pathlib import Path
import importlib.util, hashlib, sys

PORT = Path(__file__).resolve().parents[1]
SHA = 'a9311356c962bb241fcdd5fd806b8733e513e62c637537109bf669ce9a482e92'
SIZE = 8 + 128 * 128 * 4


def main(print_only=False):
    spec = importlib.util.spec_from_file_location('asset_common', PORT/'docs/full-coverage/vehicles/audit.py')
    a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
    a.w.verify_inputs(a.PS2)
    manifest, _ = a.t.load_pak(a.PS2/'TNG.PAK')
    suffix = '\\COMMONTEXTURES\\NOISE.GXI'
    entry = next(e for e in manifest['entries'] if e['kind'] == 'file' and e['path'].upper().endswith(suffix))
    raw, _ = a.t.read_payload(entry, a.PS2/'TNG.000')
    digest = hashlib.sha256(raw).hexdigest()
    if print_only:
        print(entry['path'], len(raw), digest, raw[:8].hex()); return
    if len(raw) != SIZE or digest != SHA:
        raise ValueError('Canonical ground noise identity failed')
    target = PORT/'.assets/reflection/PS2GroundNoise.gxi'
    if target.is_symlink() or target.parent.is_symlink():
        raise ValueError('Private output link rejected')
    if target.exists() and target.read_bytes() != raw:
        raise ValueError('Existing unique asset preserved')
    target.write_bytes(raw); print(digest)


if __name__ == '__main__':
    main('--print' in sys.argv)
