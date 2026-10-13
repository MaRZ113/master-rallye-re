"""Compact prop-ownership/HUD live evidence, no original assets or new DLL."""
import importlib.util
import json
from pathlib import Path

PORT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('prop_package_helpers',PORT/'overlay/package_reflection_handoff.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


def main():
    paths=[path for folder in ('docs/rigid-port1.2','docs/hud-port1')
           for path in (PORT/folder).rglob('*') if path.is_file() and path.suffix in ('.py','.json','.md','.x32dbg')]
    paths += [PORT/name for name in ('tools/rigid_lifecycle_probe.py','docs/rigid-port1/ps2-source-contract.json',
        'docs/rigid-port1/native-pc-lifecycle-20261013.json','overlay/package_prop_ownership.py',
        'overlay/package_reflection_handoff.py')]
    members={p.relative_name(path):p.read_required(path) for path in sorted(paths)}
    members['HANDOFF.md']=b'''# PS2-RIGID-PORT1.2 + HUD-PORT1 live semantic mapping

Independent gate reports: docs/rigid-port1.2/final-report.md and
docs/hud-port1/live-readiness.md under ps2-research/pc-port.
Physics is BLOCKED: no genuine original prop owner identified in99 protected
retail XMLs/user observation; private stream/cache/rollback/admission/teardown
contracts remain open. Shared vehicle collision control must not masquerade
as prop admission. New byte-backed destructor/copy/null-child facts narrow the
interface. No private spawn or physics simulation. Identity-filtered diagnostic
recipe counts only matches; it is conditional/not executed, not an activated
feature. Never substitute old vehicle pointers for an original prop.

HUD actual user F10+one external5996-byte RPM join yields unique SpeedDial
class/slot/packet candidate, two original UI draws, VB/texture generations and
source-consistent world placement. Bank0/plate vertex UV bytes, player and full
lifetime are still unproved. No HUD replacement or per-frame read was added.

Included: compact source/probe/live metadata, read-only helpers, tests, reports,
recipe and SHA manifest. Excluded: original EXE/XML/DX/PSM/GXI/hulls/meshes,
raw F10/RAM/logs and full renderer. Accepted existing DLLs unchanged and not
duplicated in this supplemental archive. Frozen source/build roots preserved.

Corpus-independent19 tests from extracted root, Python standard library:
  python -m unittest discover -s ps2-research/pc-port/docs/rigid-port1.2 -p test_prop_policy.py -v
  python ps2-research/pc-port/docs/hud-port1/live-semantic-tests.py
Original source/EXE and live user-owned process/F10 are external dependencies
for actual probe re-execution; no historical pointers accepted. No SDK/Blender
or native rebuild required for these tests. Repackaging needs the original
repository layout. Commands in the filtered prop recipe are future examples,
not observed prop admission. HUD one-shot was executed and is scoped separately.
SHA256SUMS.txt covers all other members. No deployment, code/data mutation,
original-file modification or push. Debugger recipes assign only debugger vars.
'''
    members['SHA256SUMS.txt']=''.join(f'{p.sha256(data)}  {name}\n' for name,data in sorted(members.items())).encode()
    data=p.archive_bytes(members)
    if data!=p.archive_bytes(members):raise RuntimeError('Nondeterministic archive')
    p.verify_archive(data,members)
    output=PORT/'dist/PS2-RIGID-PORT1.2-HUD-LIVE-handoff.zip';output.write_bytes(data)
    output.with_suffix('.zip.sha256').write_text(f'{p.sha256(data)}  {output.name}\n')
    print(json.dumps({'archive':str(output),'sha256':p.sha256(data),'members':len(members),'bytes':len(data),
                      'crc_sha_determinism':'PASS'},indent=2))


if __name__=='__main__':main()
