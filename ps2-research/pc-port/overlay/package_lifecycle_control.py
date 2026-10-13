"""Supplemental bounded runtime-control handoff; no rebuild or game artifacts."""
import importlib.util
import json
from pathlib import Path

PORT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('lifecycle_package_helpers',PORT/'overlay/package_reflection_handoff.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


def main():
    paths=[path for folder in ('docs/rigid-port1.1','docs/hud-port1')
           for path in (PORT/folder).rglob('*') if path.is_file() and path.suffix in ('.py','.json','.md')]
    paths += [PORT/name for name in ('tools/rigid_lifecycle_probe.py','tools/rigid_lifecycle_review.py',
        'tests/test_rigid_lifecycle_probe.py','docs/rigid-port1/native-logpoints.x32dbg',
        'docs/rigid-port1/native-pc-lifecycle-20261013.json','docs/rigid-port1/ps2-source-contract.json',
        'overlay/package_lifecycle_control.py','overlay/package_reflection_handoff.py')]
    members={p.relative_name(path):p.read_required(path) for path in sorted(paths)}
    members['HANDOFF.md']=b'''# PS2-RIGID-PORT1.1 + HUD-PORT1 mapping checkpoint

Read docs/rigid-port1.1/final-report.md, implementation-decision.md and
runtime-recipe.md under ps2-research/pc-port. Two actual user-driven runtime
controls,1194 passive snapshots,126 capped debugger observations. Six exact
clone/body pointer joins, observed thread7588 and15 update->cache-clear pairs.
This is NOT a physical tumbleweed implementation. Private stream/cache,
original prop admission, rollback and target destructor ownership remain open.
HUD SpeedDial native class/vtable is proved; live packet/texture/geometry
ownership is still missing. No replacement enabled, no per-frame HUD reads.

Sources/tests/compact evidence/recipe only; no original game binaries, raw
memory/debug logs, textures, meshes or new DLL. Existing accepted proxy build
is preserved and unchanged. No native rebuild or new build root was needed.
No automatic installation, process injection/native engine calls or push.
x32dbg's user-operated INT3 logpoints were diagnostic instrumentation, not
original EXE edits; their caps and missing target teardown are explicit.

From this extracted archive root, Python standard library is sufficient:
  python -m unittest discover -s ps2-research/pc-port/docs/rigid-port1.1 -p test_lifecycle_review.py -v
  python -m unittest discover -s ps2-research/pc-port/tests -p test_rigid_lifecycle_probe.py -v
Those19 tests are synthetic/corpus-independent; they are not physics passes.
For replay of the offline summaries, the original ignored JSONL/debugger text
is required at the documented external local paths. Source hashes are included.
For a new passive control: Windows, explicit current PID, exact retail EXE,
user course/restart/exit participation. No Ghidra/REA/SDK needed for these tests.
The package helper is included for provenance; repackaging needs the original
worktree/layout and is not a runnable archive-only renderer build.
SHA256SUMS.txt covers every other member. Frozen source/accepted DLL hashes
and exact verification results are in validation.json. No pixel/physics parity.
'''
    members['SHA256SUMS.txt']=''.join(f'{p.sha256(data)}  {name}\n' for name,data in sorted(members.items())).encode()
    data=p.archive_bytes(members)
    if data!=p.archive_bytes(members):raise RuntimeError('Archive is nondeterministic')
    p.verify_archive(data,members)
    output=PORT/'dist/PS2-RIGID-PORT1.1-HUD-PORT1-handoff.zip'
    output.write_bytes(data)
    output.with_suffix('.zip.sha256').write_text(f'{p.sha256(data)}  {output.name}\n')
    print(json.dumps({'archive':str(output),'sha256':p.sha256(data),'members':len(members),
                      'bytes':len(data),'manifest_and_crc':'PASS'},indent=2))


if __name__=='__main__':main()
