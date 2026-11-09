#!/usr/bin/env python3
"""Build the x64 Windows J.1 launcher for one verified runtime bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import struct
import tempfile
from typing import Any, Callable

import addon_runtime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / ".research-output/vehicles/sdk/j1/launcher-release"


class LauncherBuildError(RuntimeError):
    pass


def _capacity_descriptor(profile, extension, data):
    from master_rallye.addon_sdk.capacity_profile import validate_profile
    try:
        capacity = validate_profile(profile['capacity_profile'])
    except (KeyError, ValueError, TypeError) as exc:
        raise LauncherBuildError('invalid capacity profile: '+str(exc)) from exc
    if set(capacity['classes']) != {'T1', 'T2', 'T3'}:
        raise LauncherBuildError('runtime capacity supports existing three classes only')
    count = capacity['record_count']
    roster = profile.get('sdk_roster_layout')
    if roster != {'record_count': count, 'addon_ids': list(range(26, count))}:
        raise LauncherBuildError('capacity roster does not preserve the SDK33 identity range')
    size, allocation, base = extension.get('size'), extension.get('allocation_size'), extension.get('address')
    if (type(size) is not int or type(allocation) is not int or base != 0x10000000
            or size <= 0 or allocation < size or allocation % 65536
            or allocation + profile.get('course_registry_layout',capacity['layout'])['allocation_size'] > capacity['memory_budget_bytes']
            or base + allocation > 0x7fffffff):
        raise LauncherBuildError('capacity arena exceeds aligned configured memory budget')
    address = profile.get('vehicle_registry_descriptor')
    if type(address) is not int or address % 4 or not base <= address <= base+size-44:
        raise LauncherBuildError('capacity descriptor is outside native payload')
    if not isinstance(data, bytes) or len(data) != size:
        raise LauncherBuildError('capacity descriptor requires verified native payload bytes')
    if hashlib.sha256(data).hexdigest() != extension.get('sha256'):
        raise LauncherBuildError('capacity payload SHA256 differs from sealed extension')
    fields = struct.unpack_from('<11I', data, address-base)
    if fields[:7] != (int.from_bytes(b'MRVC','little'), 1, 44, count, 52, 3, 0x45a3c0):
        raise LauncherBuildError('capacity descriptor ABI or registry identity mismatch')
    def words(at, n):
        if at % 4 or not base <= at or at+n*4 > base+size:
            raise LauncherBuildError('capacity descriptor table outside native payload')
        return struct.unpack_from('<'+str(n)+'I', data, at-base)
    counts = tuple(len(capacity['classes'][c]) for c in ('T1','T2','T3'))
    if words(fields[7],3) != counts:
        raise LauncherBuildError('capacity descriptor class counts mismatch')
    reverse = {}
    for cls, ptr in enumerate(words(fields[8],3)):
        ids = capacity['classes']['T'+str(cls+1)]
        if words(ptr,len(ids)) != tuple(ids):
            raise LauncherBuildError('capacity descriptor selection mapping mismatch')
        reverse.update({ident:(cls,slot) for slot,ident in enumerate(ids)})
    if words(fields[9], count) != tuple(reverse[i][0] for i in range(count)) or words(fields[10], count) != tuple(reverse[i][1] for i in range(count)):
        raise LauncherBuildError('capacity descriptor reverse mappings mismatch')
    return fields


def _course_descriptor(profile, extension, data):
    """MRCR v1 is additive; MRVC v1 retains its original 44-byte ABI."""
    address = profile.get('course_registry_descriptor')
    base, size = extension['address'], extension['size']
    layout = profile.get('course_registry_layout', {})
    if type(address) is not int or address % 4 or not base <= address <= base+size-64:
        raise LauncherBuildError('course descriptor outside verified native arena')
    fields = struct.unpack_from('<16I',data,address-base)
    n = layout.get('race_count'); v = profile['capacity_profile']['record_count']
    if type(n) is not int or n<39 or fields[:9] != (int.from_bytes(b'MRCR','little'),1,64,n,44,v,4+v*52,4+v*52+n*44,0x45a3c0):
        raise LauncherBuildError('course descriptor/shared layout mismatch')
    if layout.get('allocation_size') != fields[7]:
        raise LauncherBuildError('course allocation budget differs')
    def words(at,n):
        if at%4 or not base<=at or at+n*4>base+size:raise LauncherBuildError('course table outside sealed arena')
        return struct.unpack_from('<'+str(n)+'I',data,at-base)
    counts=words(fields[9],8);pointers=words(fields[10],8)
    forward=[words(ptr,count) for ptr,count in zip(pointers,counts)]
    reverse=[None]*n
    for g,rows in enumerate(forward):
        for local,race in enumerate(rows):
            if race>=n or reverse[race] is not None:raise LauncherBuildError('course menu is not bijective')
            reverse[race]=(g,local)
    if None in reverse or words(fields[11],n)!=tuple(x[0] for x in reverse) or words(fields[12],n)!=tuple(x[1] for x in reverse):
        raise LauncherBuildError('course forward/reverse maps differ')
    suffixes=words(fields[13],n);keys=set()
    if any(suffixes[:39]):raise LauncherBuildError('stock progress must retain native table ownership')
    for address in suffixes[39:]:
        if not base<=address<base+size:raise LauncherBuildError('new progress key outside native payload')
        at=address-base;end=data.find(b'\0',at,min(at+256,len(data)))
        key=data[at:end] if end>=0 else b''
        if not key.startswith(b'CourseRegistryV1/') or key in keys:raise LauncherBuildError('invalid/duplicate namespaced progress key')
        keys.add(key)
    if fields[15]<6 or fields[15]>size//8:raise LauncherBuildError('invalid competition dispatch table')
    ptr=fields[14]
    originals=[(10,11,12),(13,14,15),(16,17,18),(19,20,21),(22,23,24),(36,37,38)]
    for schedule in range(fields[15]):
        count=words(ptr,1)[0]
        if not 1<=count<=n:raise LauncherBuildError('invalid schedule size')
        stages=words(ptr+4,count)
        if len(set(stages))!=count or any(i>=n for i in stages):raise LauncherBuildError('invalid explicit stage list')
        if schedule<6 and stages!=originals[schedule]:raise LauncherBuildError('original competition schedule changed')
        ptr+=4+count*4
    return fields


def _header(profile: dict[str, Any], patch_manifest: dict[str, Any], extension_bytes: bytes | None = None) -> bytes:
    values = {
        "MR_RETAIL_SHA256": profile["retail_exe"]["sha256"],
        "MR_ADDON_PLAN_SHA256": profile["addon_plan_sha256"],
        "MR_PATCH_MANIFEST_SHA256": profile["native_patch_manifest_sha256"],
        "MR_PATCH_OPS_SHA256": profile["native_patch_operations_sha256"],
        "MR_RESOURCE_MANIFEST_SHA256": profile["resource_manifest_sha256"],
        "MR_RESOURCE_INDEX_SHA256": profile["resource_index_sha256"],
        "MR_REFERENCE_IMAGE_SHA256": profile["reconstructed_reference_file_sha256"],
    }
    for key, value in values.items():
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise LauncherBuildError(f"invalid trusted-profile value: {key}")
    operation_count = len(patch_manifest.get("operations", []))
    resource_count = profile.get("resource_count")
    if type(operation_count) is not int or not 1 <= operation_count <= 512:
        raise LauncherBuildError("native operation count is outside launcher bounds")
    if type(resource_count) is not int or resource_count <= 0:
        raise LauncherBuildError("invalid trusted resource count")
    rows = ["#pragma once", "// Generated from the independently verified J.1 bundle."]
    rows.extend(f'#define {key} "{value}"' for key, value in sorted(values.items()))
    rows.extend((f"#define MR_PATCH_OPERATION_COUNT {operation_count}u",
                 f"#define MR_RESOURCE_COUNT {resource_count}u"))
    extension = profile.get('native_extension')
    if profile.get('profile')=='sdk-configurable-vehicle-registry' and not isinstance(extension,dict):
        raise LauncherBuildError('capacity profile requires native extension')
    if extension is not None:
        allocation=extension.get('allocation_size')
        configurable=profile.get('profile')=='sdk-configurable-vehicle-registry'
        if configurable:
            descriptor=_capacity_descriptor(profile,extension,extension_bytes)
            contract=profile.get('competition_contract_sha256','')
            if contract and (not isinstance(contract,str) or len(contract)!=64 or any(c not in '0123456789abcdef' for c in contract)):
                raise LauncherBuildError('invalid competition identity/dependency fingerprint')
            rows.append('#define MR_COMPETITION_CONTRACT_SHA256 "'+contract+'"')
            rows.extend((f"#define MR_VEHICLE_REGISTRY_DESCRIPTOR {profile['vehicle_registry_descriptor']}u",
                         '#define MR_VEHICLE_REGISTRY_FIELDS {'+', '.join(str(n)+'u' for n in descriptor)+'}'))
            if profile.get('course_registry_descriptor'):
                course = _course_descriptor(profile,extension,extension_bytes)
                rows.extend((f"#define MR_COURSE_REGISTRY_DESCRIPTOR {profile['course_registry_descriptor']}u",
                             '#define MR_COURSE_REGISTRY_FIELDS {'+', '.join(str(n)+'u' for n in course)+'}'))
        large_damage=(allocation==131072 and profile.get('profile')=='sdk-native-damage-coverage-alpha'
                      and type(extension.get('size')) is int and extension['size']>65536)
        roster=profile.get('sdk_roster_layout',{})
        admitted_counts={'sdk-multi-addon-roster':(29,30),'sdk-multi-addon-roster-experimental-31':(31,),'sdk-multi-addon-roster-experimental-32':(32,),'sdk-multi-addon-roster-experimental-33':(33,)}
        combined=(allocation==(524288 if profile.get('profile')=='sdk-multi-addon-roster-experimental-33' else 262144) and profile.get('profile')in admitted_counts
                  and isinstance(roster,dict) and set(roster)=={'record_count','addon_ids'}
                  and type(roster['record_count']) is int and roster['record_count'] in admitted_counts.get(profile.get('profile'),())
                  and roster['addon_ids']==list(range(26,roster['record_count'])))
        if (set(extension)-{'writable_ranges'} != {'address','size','sha256','allocation_size'}
                or extension['address'] != 0x10000000
                or type(extension['size']) is not int or not 1 <= extension['size'] <= (allocation if combined or configurable else 131072 if large_damage else 65536)
                or (allocation!=65536 and not large_damage and not combined and not configurable)
                or not isinstance(extension['sha256'], str) or len(extension['sha256']) != 64
                or any(c not in '0123456789abcdef' for c in extension['sha256'])):
            raise LauncherBuildError('unsupported private native extension layout')
        ranges=extension.get('writable_ranges',[])
        if not isinstance(ranges,list) or (not configurable and len(ranges)>1):
            raise LauncherBuildError('unsupported native writable ranges')
        range_end=0
        for region in sorted(ranges,key=lambda r:r.get('offset',-1) if isinstance(r,dict) else -1):
            if (not isinstance(region,dict) or set(region)!={'offset','size'}
                or type(region['offset']) is not int or type(region['size']) is not int
                or region['offset']<4096 or region['offset']%4096 or region['size']!=4096
                or region['offset']+region['size']>extension['size'] or region['offset']<range_end):
                raise LauncherBuildError('invalid bounded native data page')
            range_end=region['offset']+region['size']
        if configurable:
            rows.extend((f"#define MR_EXTENSION_RW_COUNT {len(ranges)}u", '#define MR_EXTENSION_RW_RANGES {{'+', '.join('{'+str(r['offset'])+'u, '+str(r['size'])+'u}' for r in ranges)+'}}'))
            classes=struct.unpack_from('<'+str(descriptor[3])+'I',extension_bytes,descriptor[9]-extension['address'])
            retired=profile.get('retired_vehicle_ids',[])
            if not isinstance(retired,list) or any(type(i)is not int or not 0<=i<descriptor[3] for i in retired) or len(set(retired))!=len(retired):
                raise LauncherBuildError('invalid retired physical ID catalog')
            rows.extend(('#define MR_VEHICLE_REGISTRY_CLASSES {'+', '.join(str(c)+'u' for c in classes)+'}', '#define MR_VEHICLE_RETIRED_IDS {'+', '.join(str(i)+'u' for i in retired)+'}'))
        if ranges:
            rows.extend((f"#define MR_EXTENSION_RW_OFFSET {ranges[0]['offset']}u",f"#define MR_EXTENSION_RW_SIZE {ranges[0]['size']}u"))
        rows.extend((f"#define MR_EXTENSION_SIZE {extension['size']}u",
                     f"#define MR_EXTENSION_ADDRESS {extension['address']}u",
                     f"#define MR_EXTENSION_ALLOCATION_SIZE {extension['allocation_size']}u",
                     f"#define MR_EXTENSION_SHA256 \"{extension['sha256']}\""))
    return ("\n".join(rows) + "\n").encode("ascii")


def build_launcher(*, bundle: Path, output: Path = DEFAULT_OUTPUT,
                   retail_exe: Path | None = None,
                   generator: str = "Visual Studio 18 2026",
                   bundle_verifier: Callable[[], dict[str, Any]] | None = None,
                   sdk_binding_input: bool = False,
                   research_root: Path | None = None) -> dict[str, Any]:
    if os.name != "nt":
        raise LauncherBuildError("the native launcher can only be built on Windows")
    bundle = Path(bundle)
    retail_exe = Path(retail_exe or addon_runtime.DEFAULT_RETAIL_EXE).resolve()
    verified = (bundle_verifier() if bundle_verifier is not None
                else addon_runtime.verify_bundle(bundle, retail_exe=retail_exe))
    if research_root is None:
        output = addon_runtime._under_research_output(Path(output))
    else:
        research_root = Path(research_root).resolve()
        output = Path(output).resolve()
        if research_root.name != '.research-output' or not output.is_relative_to(research_root) or output.exists():
            raise LauncherBuildError('fresh private research output required')
    profile = json.loads((bundle / "runtime-profile.json").read_text(encoding="utf-8"))
    patch_manifest = json.loads((bundle / "native-patch-manifest.json").read_text(encoding="utf-8"))
    allowed_statuses = {"PASS_STATIC_RUNTIME_BUNDLE", "PASS_STATIC_COLLECTION_RUNTIME_BUNDLE"}
    if verified.get("status") not in allowed_statuses or verified.get("runtime_qualified") is not False:
        raise LauncherBuildError("bundle is not a statically verified, unqualified runtime candidate")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
    # MSVC/CMake's nested TryCompile paths exceed MAX_PATH in ordinary deep
    # Workshop projects. Keep compiler scratch short; publish atomically into
    # the original fresh output tree after successful validation.
    scratch = tempfile.TemporaryDirectory(prefix='mrl-')
    try:
        include_dir = Path(scratch.name) / "generated"
        include_dir.mkdir()
        (include_dir / "trusted_profile.hpp").write_bytes(_header(profile, patch_manifest, (bundle/'native-extension.bin').read_bytes() if profile.get('profile')=='sdk-configurable-vehicle-registry' else None))
        shutil.copytree(include_dir, stage / 'generated')
        build_dir = Path(scratch.name) / "build"
        configure = ["cmake", "-S", str(PROJECT_ROOT / "runtime_launcher"), "-B", str(build_dir),
                     "-G", generator, "-A", "x64", f"-DPROFILE_INCLUDE_DIR={include_dir}",
                     f"-DMR_ENABLE_SDK_BINDING_INPUT={'ON' if sdk_binding_input else 'OFF'}"]
        subprocess.run(configure, check=True)
        subprocess.run(["cmake", "--build", str(build_dir), "--config", "Release",
                        "--target", "mr-runtime-launcher"], check=True)
        candidates = list(build_dir.rglob("mr-runtime-launcher.exe"))
        if len(candidates) != 1 or not candidates[0].is_file():
            raise LauncherBuildError("CMake did not produce exactly one launcher executable")
        launcher = stage / "mr-runtime-launcher.exe"
        shutil.copyfile(candidates[0], launcher)
        data = launcher.read_bytes()
        if len(data) < 4096 or data[:2] != b"MZ":
            raise LauncherBuildError("built launcher does not look like a Windows executable")
        metadata = {
            "schema_version": 1,
            "artifact_kind": "native external runtime launcher build",
            "status": "STATIC_BUILD_ONLY_NOT_RUNTIME_QUALIFIED",
            "architecture": "x64 launcher / x86 target process",
            "sdk_binding_input_abi": 1 if sdk_binding_input else None,
            "generator": generator,
            "launcher_sha256": hashlib.sha256(data).hexdigest(),
            "launcher_size": len(data),
            "bundle_profile": profile["profile"],
            "bundle_verified_status": verified["status"],
            "retail_exe_sha256": profile["retail_exe"]["sha256"],
            "addon_plan_sha256": profile["addon_plan_sha256"],
            "native_patch_manifest_sha256": profile["native_patch_manifest_sha256"],
            "resource_manifest_sha256": profile["resource_manifest_sha256"],
            "resource_index_sha256": profile["resource_index_sha256"],
            "runtime_qualified": False,
        }
        (stage / "launcher-build.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(stage, output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    finally:
        scratch.cleanup()
    return json.loads((output / "launcher-build.json").read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the native x64 J.1 suspended-process launcher")
    parser.add_argument("--bundle", type=Path, default=addon_runtime.DEFAULT_OUTPUT)
    parser.add_argument("--retail-exe", type=Path, default=addon_runtime.DEFAULT_RETAIL_EXE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--generator", default="Visual Studio 18 2026")
    parser.add_argument("--sdk-binding-input", action="store_true", help="Build the private SDK-binding input ABI test launcher")
    args = parser.parse_args(argv)
    try:
        result = build_launcher(bundle=args.bundle, output=args.output,
                                retail_exe=args.retail_exe, generator=args.generator,
                                sdk_binding_input=args.sdk_binding_input)
    except (LauncherBuildError, addon_runtime.RuntimeIntegrationError, OSError,
            subprocess.CalledProcessError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
