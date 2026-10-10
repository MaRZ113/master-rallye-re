"""Read-only, exact-retail camera lifetime evidence for R-CAM1-A3.

This verifies static instruction anchors. It does not certify a hook ABI,
activate Freecam, or infer live race ownership from stale scene metadata.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from inspect_fov_culling import TARGET_SHA, hx
from verify_proxy import PE

ROOT = Path(__file__).resolve().parents[1]
SITES = (
    (0x00509680, 'TraversalFullBody_RET8',
     '5356578bd9e896a2fcff8b38e83fa7fdff8b7424108b178bcf8b04b050ff52248d04768b7483048d1c833bf3741d558b6c24188b06f6000275098b1755508bcfff52108b76043bf375e95d5f5e5bc20800', None),
    (0x006532D1, 'TraversalThenFinalizeCamera',
     '8b40203bfb0f94c151578bc8e89e63ebff8b168bceff5220473bfd', None),
    (0x006922E8, 'RendererVtableFinalizeCamera', '50e25600', None),
    (0x0056E405, 'FinalizeCameraBuildViewThenParticles',
     '8b48386a00e89130ffff8b430c8b4d3050e89558ffff', None),
    (0x0056E40A, 'PostTraversalCameraBuilderCall', 'e89130ffff', 0x005614A0),
    (0x00564061, 'ParticlesReadSelectedCamera', '8b40388b4e248d54245c8b5804', None),
    (0x0056410E, 'ParticlesUseCurrentPose', '81c388000000', None),
    (0x00564185, 'ParticlesPassCurrentPoseToBillboardBuilder', '5355568bcfe831000000', None),
    (0x005614B5, 'CameraBuilderConditionalCacheExit',
     '8a470884c0740c3b1d749a6e000f846c050000', None),
    (0x006E9A74, 'CameraBuilderComparisonInitialValue', 'ffffffff', None),
    (0x005224EA, 'SceneUnloadClearsEntities', 'e8213efdff8bc8e8fa3bfdff', None),
    (0x00522680, 'CommitRequestedSceneOnSuccess',
     '8a4424045684c08bf174098b460489065ec20400', None),
    (0x00522694, 'CommitDefaultSceneOnFailure',
     '6864446e008d4c240ce8dedefaff8b4c2408890e5e', None),
    (0x005B008E, 'SceneCounterDecrementInUpdate',
     'e8ad26f7ff8b780c85ff740b8d5fffe89e26f7ff89580c', None),
    (0x0048E939, 'RaceStarterRetiresActorAt23Updates',
     '837f0c1775098b4c2458e8f86e0600', None),
    (0x004CD8C0, 'LimitsAIConstructorVtable', 'c7062c156900', None),
    (0x00449353, 'FrontendDestructorWritesRunningFalse',
     '6a00c744241400000000e89e5306008bc8e837480600', None),
)


def verify_sites(blob, pe):
    # Follow the existing scanner's byte/RVA/relative-CALL discipline.
    if pe.image_base != 0x400000:
        raise ValueError('Unsupported image base')
    rows = []
    for va, role, signature, target in SITES:
        expected = bytes.fromhex(signature)
        actual = blob[pe.offset(va - pe.image_base, len(expected)):][:len(expected)]
        if actual != expected:
            raise ValueError('Signature mismatch at ' + hx(va))
        if target is not None:
            if actual[0] != 0xE8 or va + 5 + struct.unpack('<i', actual[1:5])[0] != target:
                raise ValueError('Relative CALL target mismatch')
        rows.append(dict(va=hx(va), rva=hx(va - pe.image_base), role=role,
                         expected_bytes=signature, call_target=hx(target) if target else None,
                         evidence_grade='CONFIRMED_BY_EXE', source='hash-locked pristine bytes'))
    return rows


def inspect(blob):
    digest = hashlib.sha256(blob).hexdigest()
    if digest != TARGET_SHA:
        raise ValueError('Not pristine retail: ' + digest)
    pe = PE(blob)
    return dict(schema_version=1, read_only=True,
                build=dict(sha256=digest, size=len(blob), image_base=hx(pe.image_base)),
                sites=verify_sites(blob, pe),
                status='BLOCKED_ON_POST_TRAVERSAL_RESTORE',
                traversal=dict(owner_va='0x00509680', owner_rva='0x00109680',
                               ecx='per-camera entity-list owner', stack_arguments=2,
                               callee_cleanup_bytes=8, opaque_return_preservation_required=True,
                               evidence_grade='CONFIRMED_BY_EXE',
                               scope_complete=False, native_bridge_tested=False),
                missing_fact='An immediate native-pose restore must preserve the effective camera '
                             'for FinalizeCamera: particles read selected CameraFrame.pose directly '
                             'after the traversal has returned, independently of the D3D VIEW cache.',
                race_gate=dict(validated=False,
                               rejected_oracles=['camera address', 'Source90', 'Frontend/Running=false',
                                                 'scene request ID', 'scene countdown == 0', 'RaceStarterAI presence'],
                               candidate='registered RaceLimits actor / gaLimitsAI with validated live phase ownership'),
                freecam=dict(implemented=False, camera_pose_writes=False,
                             runtime_status='NOT_READY_FOR_FIRST_FLIGHT'))


def output_path(value):
    path = Path(value).resolve()
    if path.suffix != '.json' or not any(path.is_relative_to(ROOT / p) for p in ('research', '.analysis', 'scratch-camera')):
        raise ValueError('Output must be renderer research or ignored scratch JSON')
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('binary', type=Path)
    ap.add_argument('--output', type=output_path)
    args = ap.parse_args()
    result = json.dumps(inspect(args.binary.read_bytes()), indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding='utf-8', newline='\n')
    else:
        print(result, end='')


if __name__ == '__main__':
    main()
