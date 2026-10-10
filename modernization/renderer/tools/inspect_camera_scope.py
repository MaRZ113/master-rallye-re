"""Read-only, exact-retail camera lifetime evidence for R-CAM1-A3/A3b.

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

# A3b: exact bytes selected from reviewed instruction boundaries; A3 anchors retained.
SITES += (
    (0x00653288, 'PerCameraPreparation', '8b168bceff520ce83c0be9ff8b04b88b16508bceff5224', None),
    (0x006532A4, 'PerCameraNativeViewportWrites', '8b04b88b4cbc208b54bc3083c07889088b4cbc408950048b54bc5089480889500c', None),
    (0x006532EE, 'RebindCameraZero', 'e8dd0ae9ff8b008b4c24148b542418', 0x004E3DD0),
    (0x006532FD, 'FullFrameNativeViewportWrites', '89587889587c899080000000898884000000', None),
    (0x00653329, 'EndFrameVirtualCall', 'ff5218', None),
    (0x0065332C, 'SchedulerEpilogue_RET4', '5f5e5d5b83c450c20400', None),
    (0x006922E0, 'RendererVtableEndFrame', '80cd5600', None),
    (0x0056CD89, 'EndFrameDisabledPath', '8a86b000000084c00f84b6010000', None),
    (0x0056CE23, 'ConditionalLateDebugCamera', 'e8b88ef7ff8b480833db3bcb741c8b7c2410', 0x004E5CE0),
    (0x0056CE38, 'EndFrameLateCameraBuilderCall', 'e86346ffff', 0x005614A0),
    (0x0056CE3D, 'EndFramePassSelectedCameraToDebug', '8b4f048b560c51528d4e10e833ca0100', None),
    (0x00589952, 'DebugWorldCameraConsumer', 'e819020000', 0x00589B70),
    (0x0056CE60, 'EndFrameNativeEndScene', 'ff918c000000', None),
    (0x0056CE90, 'EndFramePresentCall', 'e83be2feff', 0x0055B0D0),
    (0x0056CE95, 'PostPresentTimerCalls', 'e886ec01008bc8e8cfe90100', 0x0058BB20),
    (0x0056CF43, 'EndFrameNormalEpilogue_RET0', '5f5e5d5b83c410c3', None),
    (0x0056CF4B, 'EndFrameAlternateEpilogue_RET0', 'ddd85f5e5d5b83c410c3', None),
    (0x005B015A, 'CountdownSkipsScheduler', '85ff75118b442410', None),
    (0x005B0166, 'MainLoopSchedulerCall', 'e8152f0a00', 0x00653080),
    (0x005B016B, 'ImmediateCallerContinuation', 'ff44241484db0f84b7fdffff6a00ff1520f2680050ff1544f16800e9a3fdffff', None),
    (0x005AFF55, 'MainLoopMessagePumpCall', 'e8e6f209008bc8e85ff2090084c0', 0x0064F240),
    (0x005AFF5C, 'MainLoopDispatchMessages', 'e85ff20900', 0x0064F1C0),
    (0x004F2A02, 'CameraProducerSnapAndHistoryWrites', '385e04740c558d4e38e85024f1ff885e04399ec8000000740f558d4e38e83c24f1ffff8ec8000000', None),
    (0x0048E6E5, 'RaceLimitsRenameCall', 'e806730600', 0x004F59F0),
    (0x0048E706, 'RaceLimitsAIConstructorCall', 'e865f10300', 0x004CD870),
    (0x0048E717, 'RaceLimitsAIInitialAttachCall', 'e834720600', 0x004F5950),
    (0x004F59FC, 'ActorRenameUnregisters', 'e84f8c0100', 0x0050E650),
    (0x004F5A13, 'ActorRenameRegisters', 'e8388a0100', 0x0050E450),
    (0x0050E45B, 'RegistryIndexesActorNameID', '8b685c33c93be9896c240c', None),
    (0x004F5975, 'AttachStoresAIThenInitializes', '894cbe0474198b1156ff5214', None),
    (0x004F5840, 'ActorRetirementFlagAndQueue', '8a01a80275320c025688018d7118', None),
    (0x004CD926, 'LimitsDestructorRewritesDerivedVtable', 'c7062c156900', None),
    (0x004CD931, 'LimitsDestructorFreesParticipantArray', 'e8ca720e00', 0x005B4C00),
    (0x004CD999, 'LimitsDestructorWritesBaseVtable', 'c70690f468005ec3', None),
    (0x0048E855, 'RaceStarterChoosesPhaseOneOrTwo', '83f80a0f9dc141408be9', None),
    (0x0048E953, 'RaceStarterUsesParticipantPhasePath', '68700f6b00', None),
    (0x0048E991, 'RaceStarterWritesParticipantPhase', '5552e828a504008bc8e861960400', None),
    (0x005223D0, 'SceneRequestStoresRequestedID', '894604', None),
    (0x0052241E, 'SceneRequestStartsCountdown', 'c7460c03000000', None),
    (0x0052243A, 'SceneLoadJobVtable', 'c706101b6900', None),
    (0x0052D633, 'SceneJobUnloadCall', 'e8484effff', 0x00522480),
    (0x0052D6A4, 'SceneJobCommitCall', 'e8d74fffff', 0x00522680),
    (0x005B0083, 'MainUpdateDispatchesLoadJobs', 'e8d8a5f9ff8b108bc8ff12', 0x0054A660),
    (0x005FC967, 'JobRequestQueuesWithoutImmediateDispatch', '894e1c751083c610e8ecdcf4ff83c01c8b4008eb0b83c610e8dcdcf4ff83c01c', None),
    (0x0054A3FE, 'JobFileOpenFailureBranch', '84c0745d', None),
    (0x0054A45F, 'JobFileOpenFailureCallback', '8bcee8ea250b00', None),
    (0x005FCA82, 'JobFileOpenFailureVirtualCallback', '8b07ff50045f5ec3', None),
    (0x005FCB19, 'JobSuccessVirtualExecute', '8b07ff500c5f5ec20c00', None),
    (0x00691B10, 'SceneJobVtableCallbacks', '60245200e0d5520000d6520020d65200', None),
    (0x006E42A0, 'RaceLimitsInternedNameText', '526163654c696d69747300', None),
    (0x006B0F70, 'ParticipantRaceStatePathText', '526163652f43617225642f526163655374617465', None),
)


def verify_sites(blob, pe, sites=SITES):
    # Follow the existing scanner's byte/RVA/relative-CALL discipline.
    if pe.image_base != 0x400000:
        raise ValueError('Unsupported image base')
    rows = []
    for va, role, signature, target in sites:
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


def scope_evidence():
    """Bounded native call graph, not an executable mutation certificate."""
    def site(va, role, **extra):
        return dict(va=hx(va), rva=hx(va - 0x400000), role=role,
                    evidence_grade='CONFIRMED_BY_EXE', **extra)

    return dict(
        native_reader_extent='CLOSED_FOR_REVIEWED_SINGLE_CAMERA_SCHEDULER_PATH',
        executable_mutation_approved=False, native_bridge_tested=False,
        begin=site(0x006532DD, 'before original traversal; existing GameFov owner'),
        end=site(0x0065332C, 'after EndFrame, before scheduler epilogue'),
        completion_interception=site(0x005B0166, 'five-byte CALL to scheduler',
                                     target_va='0x00653080', return_va='0x005B016B',
                                     installed=False),
        candidates=[
            site(0x006532E2, 'post-traversal', decision='REJECTED',
                 reason='FinalizeCamera, particles and EndFrame still consume the camera'),
            site(0x006532E9, 'post-FinalizeCamera', decision='REJECTED',
                 reason='EndFrame still builds VIEW and passes CameraFrame to debug rendering'),
            site(0x0065332C, 'post-EndFrame', decision='STATIC_NATIVE_ENDPOINT',
                 reason='remaining scheduler epilogue and immediate caller have no CameraFrame consumption'),
        ],
        readers=[
            site(0x00509680, 'entity traversal and CPU visibility'),
            site(0x0056E40A, 'FinalizeCamera VIEW builder'),
            site(0x0056410E, 'particles use Current Pose'),
            site(0x0056CE38, 'conditional EndFrame VIEW builder'),
            site(0x0056CE48, 'EndFrame passes selected CameraFrame to debug renderer'),
            site(0x00589952, 'world debug renderer passes CameraFrame onward'),
        ],
        order=['begin', 'traversal', 'finalize', 'particles_if_enabled',
               'camera_zero_rebind', 'late_builder_if_debug', 'debug_if_enabled',
               'EndScene', 'Present', 'timer_accounting', 'end',
               'scheduler_return', 'caller_counters', 'message_pump', 'next_update'],
        owned_field_candidates=[dict(offset='0x08', size=48, role='CPU side planes'),
                                dict(offset='0x38', size=64, role='Previous Pose'),
                                dict(offset='0x88', size=64, role='Current Pose')],
        excluded_fields=['source +0x00', 'flags +0x04', 'viewport +0x78..0x87', 'snap +0xC8'],
        native_writers=[site(0x006532A4, 'per-camera viewport'),
                        site(0x006532FD, 'camera-zero full-frame viewport'),
                        site(0x004F2A02, 'producer history/snap outside render scope')],
        pre_render_dependencies=[site(0x004F62CE, 'per-camera entity sort',
                                     conclusion='position-based ordering; not proven visibility rejection'),
                                 site(0x004F65B0, 'camera-position cache update',
                                      conclusion='cache consumer role unresolved; no LOD claim')],
        implementation_obligations=[
            'exact retail, one camera, live race owner, thread and device validation',
            'atomic nonoverlapping pre-submit/completion ownership and actual x86 ABI fixture',
            'retain effective fields through late consumers; preserve viewport writes',
            'coordinate existing Present/Reset GameFov.finish_frame with pose owner',
            'guard cancellation/restoration on driver reentry, focus, Reset and owner changes',
            'validate cache invalidation and ordering when camera moves independently',
        ])


def race_evidence():
    return dict(
        validated=False, production_predicate_implemented=False,
        registry=dict(manager_global_va='0x006F96FC', manager_global_rva='0x002F96FC',
                      name='RaceLimits', name_va='0x006E42A0', name_rva='0x002E42A0',
                      owner_name_offset='0x5C', registry_offset='0x1C',
                      register_va='0x0050E450', unregister_va='0x0050E650',
                      rename_va='0x004F59F0', ai_slot_offset='0x04',
                      evidence_grade='CONFIRMED_BY_EXE'),
        limits_ai=dict(vtable_va='0x0069152C', vtable_rva='0x0029152C',
                       initialize_va='0x004CDF00', update_va='0x004CD9B0',
                       destructor_va='0x004CD920', count_offset='0x2C',
                       participant_arrays=['0x20', '0x24', '0x30', '0x34', '0x38', '0x3C', '0x40'],
                       evidence_grade='CONFIRMED_BY_EXE'),
        retirement=dict(owner_flag_offset='0x00', mask=2, queue_node_offset='0x18',
                        retire_va='0x004F5840', destroy_va='0x004F5780',
                        warning='queued retirement precedes unregister; destructor frees arrays without zeroing pointers',
                        evidence_grade='CONFIRMED_BY_EXE'),
        phase=dict(path='Race/Car%d/RaceState', path_va='0x006B0F70',
                   producer_va='0x0048E820', observed_native_writes=[0, 1, 2, 3],
                   phase_two_rule='RaceStarter previous counter >= 10 and +0x10 false',
                   active_race_certificate=False, evidence_grade='CONFIRMED_BY_EXE'),
        scene_jobs=dict(manager_global_va='0x006F9D28', manager_global_rva='0x002F9D28',
                        manager_vtable_va='0x006921A4', job_vtable_va='0x00691B10',
                        request_va='0x00522330', execute_va='0x0052D620',
                        dispatch_va='0x005B008C',
                        file_open_failure_va='0x0054A45F',
                        missing_fact='Read-only active-race admission must distinguish the current successful '
                                     'scene/owner epoch from a pending or failed same-scene request retaining '
                                     'the old registered RaceLimits and RaceState.',
                        evidence_grade='CONFIRMED_BY_EXE'),
        rejected_oracles=['camera address', 'Source90', 'Frontend/Running=false',
                          'scene request ID', 'scene countdown == 0', 'RaceStarterAI presence',
                          'gaLimitsAI vtable alone', 'participant array pointer readability',
                          'RaceState == 2 alone', 'BeenInRace', 'empty pending-job list alone'],
        required_context_inputs=['committed France1 ownership', 'Race/Type', 'Race/NumPlayers',
                                 'Race/NumNetworkPlayers', 'Race/FinishingType', 'AttractMode',
                                 'NetworkSyncActive', 'GhostPlayback', 'PlaybackReplay'],
        context_input_status='Existing research/captures supply context; no validated combined live predicate',
        read_policy='bounded guarded storage reads; resolve existing interned text IDs; never call growing Broker getters')


def inspect(blob):
    digest = hashlib.sha256(blob).hexdigest()
    if digest != TARGET_SHA:
        raise ValueError('Not pristine retail: ' + digest)
    pe = PE(blob)
    scope = scope_evidence()
    race = race_evidence()
    return dict(schema_version=2, phase='R-CAM1-A3b', read_only=True,
                build=dict(sha256=digest, size=len(blob), image_base=hx(pe.image_base)),
                sites=verify_sites(blob, pe),
                status='BLOCKED_ON_LIVE_RACE_OWNERSHIP',
                traversal=dict(owner_va='0x00509680', owner_rva='0x00109680',
                               ecx='per-camera entity-list owner', stack_arguments=2,
                               callee_cleanup_bytes=8, opaque_return_preservation_required=True,
                               evidence_grade='CONFIRMED_BY_EXE',
                               scope_complete=False, native_bridge_tested=False),
                scope=scope, race_gate=race,
                missing_fact=race['scene_jobs']['missing_fact'],
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
