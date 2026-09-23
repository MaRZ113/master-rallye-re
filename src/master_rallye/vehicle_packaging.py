"""Exact vehicle texture dependencies and conservative staging/ZIP-compatible SMA."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from .assets import AssetResolver
from .dx import parse_dx

RESOURCE_NAMES=("car.dx","complete.dx","wheel.dx")


def sha256(path: Path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def vehicle_dependencies(vehicle_dir: Path):
    vehicle_dir=Path(vehicle_dir).resolve()
    resolver=AssetResolver(vehicle_dir)
    resources=[]
    bindings=[]
    for name in RESOURCE_NAMES:
        path=vehicle_dir/name
        if not path.is_file():
            resources.append({"resource":name,"status":"ABSENT"})
            continue
        model=parse_dx(path)
        if not model.diagnostics.validated:
            raise ValueError(f"invalid DX resource: {path}")
        resources.append({"resource":name,"status":"PARSED","sha256":sha256(path),"draw_count":len(model.physical_draws)})
        for draw in model.physical_draws:
            for slot in draw.texture_slots:
                if slot.value.casefold()=="null":
                    continue
                resolved=resolver.resolve_texture(slot.value)
                bindings.append({
                    "resource":name,"draw":draw.draw_index,"slot":slot.slot,
                    "texture_name":slot.value,
                    "resolution":"RESOLVED" if resolved else "UNRESOLVED",
                    "source_path":str(resolved) if resolved else None,
                })
    counts={}
    for binding in bindings:
        key=binding["texture_name"].casefold()
        counts[key]=counts.get(key,0)+1
    for binding in bindings:
        binding["user_count"]=counts[binding["texture_name"].casefold()]
    return {"vehicle":vehicle_dir.name,"vehicle_directory":str(vehicle_dir),"resources":resources,"bindings":bindings,"unresolved_count":sum(x["resolution"]=="UNRESOLVED" for x in bindings)}


def texture_users(vehicle_dir: Path, name: str):
    manifest=vehicle_dependencies(vehicle_dir)
    requested=Path(name).stem.casefold()
    matching=[x for x in manifest["bindings"] if Path(x["texture_name"]).stem.casefold()==requested]
    return {"texture":name,"vehicle":manifest["vehicle"],"users":matching,"count":len(matching)}


def bundle_vehicle(vehicle_dir: Path, replacements: dict[str,Path], output: Path):
    vehicle_dir=Path(vehicle_dir).resolve()
    output=Path(output).resolve()
    if output==vehicle_dir or vehicle_dir in output.parents:
        raise ValueError("staging output must not be inside source vehicle directory")
    dependencies=vehicle_dependencies(vehicle_dir)
    if dependencies["unresolved_count"]:
        raise ValueError(f"{dependencies['unresolved_count']} unresolved texture bindings")
    if output.exists() and any(output.iterdir()):
        raise ValueError("staging output must be empty")
    known={path.name.casefold():path for path in vehicle_dir.iterdir() if path.is_file()}
    target=output/"DataGx"/"Vehicles"/vehicle_dir.name
    files=[]
    try:
        for name, replacement in sorted(replacements.items()):
            source=known.get(name.casefold())
            if source is None:
                raise ValueError(f"replacement name is not an existing vehicle file: {name}")
            replacement=Path(replacement).resolve()
            if replacement==source:
                raise ValueError(f"replacement is source file: {name}")
            if replacement.suffix.casefold()!=source.suffix.casefold():
                raise ValueError(f"replacement type differs: {name}")
            classification="UNSUPPORTED"
            if source.suffix.casefold()==".dx":
                import math
                from .r4e_writer import patch_dx_attributes
                old=parse_dx(source); new=parse_dx(replacement)
                if not new.diagnostics.validated or old.vertex_count!=new.vertex_count or old.local_indices!=new.local_indices or len(old.physical_draws)!=len(new.physical_draws):
                    raise ValueError(f"unsafe DX replacement: {name}")
                alpha={}
                env={}
                for index,(before,after) in enumerate(zip(old.physical_draws,new.physical_draws)):
                    if before.flags_0x20[0]!=after.flags_0x20[0]:
                        alpha[index]=bool(after.flags_0x20[0])
                    if bool(before.unknown_0x24&4)!=bool(after.unknown_0x24&4):
                        env[index]=bool(after.unknown_0x24&4)
                expected=patch_dx_attributes(
                    source.read_bytes(),
                    positions=new.vertices.positions,
                    normals=[value if all(math.isfinite(x) for x in value) else None for value in new.vertices.normals],
                    uv_sets=[item.values for item in new.uv_sets],
                    colors=new.vertices.colors,
                    material_alpha=alpha,material_env=env,
                )
                if expected.data!=replacement.read_bytes():
                    raise ValueError(f"DX replacement contains non-authorized bytes: {name}")
                classification=expected.classification
            elif source.suffix.casefold()==".dxt":
                from .dxt import parse_dxt
                before=parse_dxt(source); after=parse_dxt(replacement)
                if before.header!=after.header or len(before.bgra)!=len(after.bgra):
                    raise ValueError(f"DXT header/size changed: {name}")
                classification="TEXTURE_CONTENT_ONLY" if before.bgra!=after.bgra else "NO_CHANGE"
            else:
                raise ValueError(f"unsupported replacement type: {name}")
            target.mkdir(parents=True,exist_ok=True)
            destination=target/source.name
            shutil.copyfile(replacement,destination)
            files.append({"name":source.name,"status":"modified","classification":classification,"source_sha256":sha256(source),"replacement_sha256":sha256(destination),"archive_path":destination.relative_to(output).as_posix()})
        report={
            "vehicle":vehicle_dir.name,
            "staging_root":str(output),
            "files":files,
            "classification":("NO_CHANGE" if not files or all(x["classification"]=="NO_CHANGE" for x in files) else files[0]["classification"] if len(files)==1 else "MULTIPLE_SAFE_CHANGES"),
            "dependencies":dependencies,
            "required_dependency_names":sorted({x["texture_name"] for x in dependencies["bindings"]},key=str.casefold),
            "unmodified_dependencies":"referenced in manifest; not copied",
            "sidecar_status":"optional tooling metadata; not runtime-required",
        }
        output.mkdir(parents=True,exist_ok=True)
        (output/"manifest.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        return report
    except Exception:
        # Retain any partial staging output for inspection; never touch source.
        raise


def _archive_members(root: Path):
    if not root.is_dir():
        raise ValueError("SMA input root is not a directory")
    allowed={"DataGx","DataGame","DataScene"}
    present={p.name for p in root.iterdir() if p.is_dir()}
    if not present or not present<=allowed:
        raise ValueError("SMA root must directly contain DataGx and/or DataGame, without an extra directory")
    for file in sorted(root.rglob("*"),key=lambda p:p.as_posix().casefold()):
        if file.is_file() and file.name not in {"manifest.json","master_rallye_data_sma_tree.txt"}:
            relative=file.relative_to(root).as_posix()
            if relative.split("/")[0] not in allowed:
                raise ValueError(f"unexpected archive-root file: {relative}")
            yield file,relative


def pack_sma(root: Path, output: Path, overrides: dict[str,Path] | None = None):
    root=Path(root).resolve(); output=Path(output).resolve()
    if output.exists():
        raise ValueError("refusing to overwrite existing SMA")
    if root in output.parents or output==root:
        raise ValueError("output archive must be outside input tree")
    members=list(_archive_members(root))
    overrides={key.replace("\\","/"):Path(value).resolve() for key,value in (overrides or {}).items()}
    known={name for _,name in members}
    if set(overrides)-known:
        raise ValueError(f"SMA overrides not present in source tree: {sorted(set(overrides)-known)}")
    if not members:
        raise ValueError("SMA tree contains no files")
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as archive:
        for path,name in members:
            info=zipfile.ZipInfo(name,(2020,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644<<16
            archive.writestr(info,(overrides.get(name,path)).read_bytes())
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or archive.namelist()!=[name for _,name in members]:
            raise ValueError("SMA structural validation failed")
        for path,name in members:
            if hashlib.sha256(archive.read(name)).digest()!=hashlib.sha256((overrides.get(name,path)).read_bytes()).digest():
                raise ValueError(f"SMA member mismatch: {name}")
    return {"output":str(output),"sha256":sha256(output),"member_count":len(members),"override_count":len(overrides),"status":"STRUCTURALLY_VALID","runtime_status":"RUNTIME_CONFIRMATION_PENDING"}


def unpack_sma(source: Path, output: Path):
    source=Path(source).resolve(); output=Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("unpack output must be empty")
    if output==source:
        raise ValueError("refusing to overwrite source archive")
    with zipfile.ZipFile(source) as archive:
        names=archive.namelist()
        if archive.testzip() is not None:
            raise ValueError("corrupt SMA archive")
        if len(names)!=len(set(names)):
            raise ValueError("duplicate SMA archive member names")
        for info in archive.infolist():
            name=info.filename
            parts=Path(name).parts
            if not parts or parts[0] not in {"DataGx","DataGame","DataScene"} or ".." in parts or any(":" in part for part in parts) or Path(name).is_absolute() or "\\" in name:
                raise ValueError(f"unsafe or extra-root archive entry: {name}")
        archive.extractall(output)
    return {"source_sha256":sha256(source),"output":str(output),"member_count":len(names),"status":"STRUCTURALLY_VALID"}
