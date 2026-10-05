"""Use an audited external Observatory with an exact R-AI research profile.

The external distribution remains unchanged. Its capture/UI implementations
are reused; every native memory location and command ID retains retail layout.
All generated settings/captures stay in this checkout's ignored output.
"""
from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import sys
from pathlib import Path

from r_ai1_mixed_class import (CANDIDATE_SHA256, GENERAL_SHA256, REPOSITORY, ignored_output,
                              sha256, verify_candidate, verify_general)
from r_ai1_hardening import BASE_SHA256, MIXED_SHA256, verify as verify_hardening
from r_ai2_capacity import CANDIDATE_SHA256 as FIVE_CAR_SHA256, verify as verify_five_car
from r_ai1_2_randomizer import PROFILE_SHA256 as AI12_SHA256, verify as verify_ai12
from r_ai1_2a_preview import PROFILE_SHA256 as AI12A_SHA256, verify as verify_ai12a
from research_build_profiles import (MERC_SHA256, PRISTINE_SHA256, identify,
                                     resolve_build)

OBSERVATORY_FILES = {
    "broker_observatory.py": "d1a07eab330ef3d8b825ef3320b458d20ced11df99d75250a72e9c7701c4ba7d",
    "dev_command_trigger.py": "6da763eb605e7bb397f39ef78d909bfc5952e869f59eca6650bb710847c37cbe",
    "mr_observe.py": "ad3c1ec4b6209cb4a3a1d9ed19b3e1f2ed19ccb4b6c3ecb8a2beeebfbf91cbb8",
    "observatory_version.py": "43d54f1ac1922c40cc68ac301a9dade645a66db3d0b3f9f72e68a2844cfe4526",
}


def verify_distribution(directory: Path) -> None:
    for name, expected in OBSERVATORY_FILES.items():
        if sha256((directory / name).read_bytes()) != expected:
            raise ValueError(f"Observatory implementation changed: {name}; audit required")


def _research_module(directory: Path, name: str):
    """Adapt only basename filters in the hash-pinned public implementation.

    This is an in-memory INTERNAL derivative; no public files/artifact change.
    Every process is still checked against one exact executable hash and size.
    """
    path=directory/(name+'.py')
    raw=path.read_bytes()
    if OBSERVATORY_FILES.get(path.name)!=sha256(raw):
        raise ValueError('Unknown Observatory implementation at import: '+path.name)
    tree=ast.parse(raw.decode('utf-8'),filename=str(path))
    class Basenames(ast.NodeTransformer):
        count=0
        def visit_Compare(self,node):
            self.generic_visit(node)
            if (len(node.ops)==1 and len(node.comparators)==1
                and isinstance(node.comparators[0],ast.Constant)
                and node.comparators[0].value=='mrallye.exe'
                and isinstance(node.left,ast.Call) and isinstance(node.left.func,ast.Attribute)
                and node.left.func.attr=='casefold'):
                if isinstance(node.ops[0],ast.Eq):node.ops[0]=ast.In()
                elif isinstance(node.ops[0],ast.NotEq):node.ops[0]=ast.NotIn()
                else:raise ValueError('Unexpected audited basename comparison')
                node.comparators[0]=ast.Tuple(elts=[ast.Constant('mrallye.exe'),
                    ast.Constant('mrallye_merc.exe'), ast.Constant('mrallye_mercv2.exe')],ctx=ast.Load())
                self.count+=1
            return node
    transform=Basenames();tree=transform.visit(tree)
    if transform.count!=2:raise ValueError('Audited basename filter count changed')
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    try:exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),module.__dict__)
    except BaseException:
        sys.modules.pop(name,None);raise
    return module


def load_profile(directory: Path, candidate: Path):
    data = candidate.read_bytes()
    image_hash = sha256(data)
    family_profile = None
    if image_hash == CANDIDATE_SHA256:
        verifier, phase = verify_candidate, "r-ai1"
    elif image_hash == GENERAL_SHA256:
        verifier, phase = verify_general, "r-ai1-1"
    elif image_hash in (BASE_SHA256, MIXED_SHA256):
        verifier, phase = verify_hardening, "r-ai1-1/hardening"
    elif image_hash == FIVE_CAR_SHA256:
        verifier, phase = verify_five_car, "r-ai2"
    elif image_hash in AI12_SHA256.values():
        five = image_hash == AI12_SHA256[True]
        verifier, phase = lambda data: verify_ai12(data, five), "r-ai1-2"
    elif image_hash in AI12A_SHA256.values():
        five = image_hash == AI12A_SHA256[True]
        verifier, phase = lambda data: verify_ai12a(data, five), "r-ai1-2a"
    elif image_hash in (MERC_SHA256,PRISTINE_SHA256):
        family_profile = resolve_build(data)
        manifest, phase = family_profile, "r-obs2-compatible-builds"
    else:
        try:
            family_profile = resolve_build(data)
        except ValueError as exc:
            raise ValueError("Unknown research image; executable is not a registered exact profile or audited Broker-family build: " + str(exc)) from exc
        manifest, phase = family_profile, "r-obs2-compatible-builds"
    if family_profile is None:
        manifest = verifier(data)
    directory = directory.resolve()
    verify_distribution(directory)
    for name in ("broker_observatory", "dev_command_trigger", "mr_observe", "observatory_version"):
        if name in sys.modules:
            raise ValueError("Observatory already loaded; use a fresh process for this exact profile")
    sys.dont_write_bytecode = True  # Do not create external __pycache__ research artifacts.
    sys.path.insert(0, str(directory))
    if manifest.get("compatibility_family"):
        _research_module(directory,'broker_observatory')
        observe=_research_module(directory,'mr_observe')
    else:
        observe = importlib.import_module("mr_observe")
    core, commands = observe.core, observe.commands
    if manifest.get("compatibility_family"):
        layout=manifest['observatory']
        for field,key in (('RETAIL_IMAGE_BASE','image_base'),('ACTIVE_LOG_SINK_RVA','active_log_sink_rva'),
                          ('DEBUG_SINK_VTABLE_RVA','debug_sink_vtable_rva'),('DEBUG_SINK_OBJECT_SIZE','debug_sink_object_size')):
            if getattr(core,field)!=layout[key]:raise ValueError('Audited reader layout changed: '+field)
    # Exact audited implementation, exact candidate, retail image size/base/RVAs.
    core.RETAIL_SHA256 = commands.RETAIL_SHA256 = image_hash
    if manifest.get("broker_dump_variant") in ("native_hardened","native_stock"):
        original_parse = core.parse_dump_bytes
        def parse_dump_bytes(raw, source=None):
            provenance = dict(source or {})
            if provenance.get("image_sha256") == image_hash:
                provenance.update(build_profile=manifest.get('profile_id', manifest.get('profile')),
                                  exact_profile_id=manifest.get('exact_profile_id'),
                                  profile_origin=manifest.get('profile_origin', 'committed_exact'),
                                  compatibility_family=manifest.get('compatibility_family'),
                                  audit_version=manifest.get('audit_version'),
                                  audit_fingerprint=manifest.get('audit_fingerprint'),
                                  vehicle_registry_profile=manifest.get('vehicle_registry_profile', 'unknown'),
                                  capabilities=manifest.get('capabilities', {}),
                                  broker_dump_variant=manifest.get('broker_dump_variant', 'unknown'),
                                  native_dump_post_results_safe=manifest.get('native_dump_post_results_safe'),
                                  legacy_loading_attract_present=manifest.get('legacy_loading_attract_present'))
                provenance.setdefault('exe_sha256', image_hash)
                provenance.setdefault('exe_size', len(data))
            return original_parse(raw, provenance)
        core.parse_dump_bytes = parse_dump_bytes
    original_verify = observe.verify_executable
    def verify_executable(path):
        if manifest.get("compatibility_family"):
            from research_build_profiles import resolve_build
            try:
                current = Path(path).read_bytes()
                current_profile = resolve_build(current)
            except (OSError, ValueError) as exc:
                raise observe.UserError("Executable failed the Broker compatibility-family audit.", str(exc)) from exc
            if current_profile['sha256'] != image_hash or current_profile['audit_fingerprint'] != manifest['audit_fingerprint']:
                raise observe.UserError("Executable changed after compatibility audit.", "Re-run with the current file.")
            return
        try:
            original_verify(path)  # Retains basename, size, exact hash and file gates.
        except observe.UserError as exc:
            raise observe.UserError("Research Observatory requires the exact audited executable profile.",
                                    f"Expected SHA256: {image_hash}") from exc
        verifier(path.read_bytes())  # Research patch inverse OR exact audited original profile.
    observe.verify_executable = verify_executable
    observe.PORTABLE = True
    observe.REPO = REPOSITORY / f".research-output/{phase}/observatory"
    observe.DATA_ROOT = observe.REPO / "observatory-data"
    observe.DEFAULT_CAPTURE_ROOT = observe.DATA_ROOT / "captures"
    observe.DEFAULT_CONFIG = observe.DATA_ROOT / "config.json"
    original_root = observe.capture_root_for
    observe.capture_root_for = lambda args, config: ignored_output(original_root(args, config))
    original_save = observe.save_config
    observe.save_config = lambda path, config: original_save(ignored_output(path), config)
    original_launcher = observe.setup_launcher
    observe.setup_launcher = lambda output, exe: original_launcher(ignored_output(output), exe)
    observe.RESEARCH_BUILD_PROFILE=manifest.get('profile_id', manifest.get('profile'))
    observe.RESEARCH_BUILD_PROVENANCE={
        'sha256': image_hash,
        'exact_profile_id': manifest.get('exact_profile_id'),
        'profile_origin': manifest.get('profile_origin', 'committed_exact'),
        'compatibility_family': manifest.get('compatibility_family'),
        'audit_version': manifest.get('audit_version'),
        'audit_fingerprint': manifest.get('audit_fingerprint'),
        'vehicle_registry_profile': manifest.get('vehicle_registry_profile', 'unknown'),
        'capabilities': manifest.get('capabilities', {}),
    }
    return observe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observatory", required=True, type=Path)
    parser.add_argument("--candidate", "--exe", dest="candidate", required=True, type=Path)
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    arguments = args.arguments
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    observe = load_profile(args.observatory, args.candidate)
    provenance = observe.RESEARCH_BUILD_PROVENANCE
    print("Build SHA256:", observe.core.RETAIL_SHA256)
    print("Exact profile:", provenance['exact_profile_id'] or 'locally-audited')
    print("Compatibility family:", provenance['compatibility_family'] or 'exact-research-profile')
    print("Vehicle registry:", provenance['vehicle_registry_profile'])
    print("Native Dump:", provenance['capabilities'].get('native_dump', 'research-profile-specific'))
    print("Post-Results Dump safe:", provenance['capabilities'].get('post_results_native_dump_safe', 'see exact research profile'))
    if provenance['compatibility_family'] and provenance['capabilities'].get('post_results_native_dump_safe') is False:
        print('Research guidance: first active-race capture only; do not invoke native Dump after Results.')
    return observe.main(["--exe", str(args.candidate.resolve()), *arguments])


if __name__ == "__main__":
    raise SystemExit(main())
