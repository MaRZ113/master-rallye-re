"""Exact vehicle texture dependencies and conservative staging/ZIP-compatible SMA."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from contextlib import contextmanager
from pathlib import PurePosixPath
from pathlib import Path
from typing import Iterator

from .assets import AssetResolver
from .dx import parse_dx

RESOURCE_NAMES=("car.dx","complete.dx","wheel.dx")
SMA_ALLOWED_ROOTS=frozenset({"DataGx","DataGame","DataScene"})


class _SmaZipCompatibilityView:
    """Read-only file view translating the retail SMA EOCD marker for zipfile."""
    def __init__(self, source: Path):
        self._file=Path(source).open("rb")
        self.name=str(source)
        self.mode="rb"
        try:
            self._eocd_offset=self._find_custom_eocd()
        except Exception:
            self._file.close()
            raise

    def _find_custom_eocd(self) -> int:
        self._file.seek(0,2)
        size=self._file.tell()
        tail_size=min(size,22+65535)
        self._file.seek(size-tail_size)
        tail=self._file.read(tail_size)
        signature=b"SM\x05\x06"
        offset=tail.rfind(signature)
        if offset < 0 or offset+22 > len(tail):
            raise ValueError(f"not a recognized ZIP-compatible Data.sma: {self.name}")
        comment_length=int.from_bytes(tail[offset+20:offset+22],"little")
        if offset+22+comment_length != len(tail):
            raise ValueError(f"invalid retail SMA end-of-central-directory record: {self.name}")
        return size-tail_size+offset

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._file.seek(offset,whence)

    def tell(self) -> int:
        return self._file.tell()

    def read(self, size: int = -1) -> bytes:
        start=self._file.tell()
        data=self._file.read(size)
        if start <= self._eocd_offset < start+len(data):
            mutable=bytearray(data)
            position=self._eocd_offset-start
            mutable[position:position+2]=b"PK"
            return bytes(mutable)
        return data

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def close(self) -> None:
        self._file.close()


@contextmanager
def _open_sma_archive(source: Path) -> Iterator[zipfile.ZipFile]:
    """Open standard generated SMA ZIPs and retail archives with the `SM` EOCD."""
    source=Path(source)
    compatibility_view=None
    try:
        try:
            archive=zipfile.ZipFile(source)
        except zipfile.BadZipFile:
            compatibility_view=_SmaZipCompatibilityView(source)
            archive=zipfile.ZipFile(compatibility_view)
        with archive as opened:
            yield opened
    except zipfile.BadZipFile as exc:
        raise ValueError(f"not a ZIP-compatible Data.sma archive: {source}") from exc
    finally:
        if compatibility_view is not None:
            compatibility_view.close()


def normalize_sma_member_name(name: str) -> tuple[str, bool]:
    """Validate one ZIP-style SMA path and return its slash form and dir flag."""
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError(f"unsafe SMA archive entry: {name!r}")
    is_directory=name.endswith("/")
    raw=name[:-1] if is_directory else name
    parts=raw.split("/")
    if (
        not parts
        or any(part in {"", ".", ".."} or ":" in part for part in parts)
        or PurePosixPath(raw).is_absolute()
        or parts[0].casefold() not in {root.casefold() for root in SMA_ALLOWED_ROOTS}
    ):
        raise ValueError(f"unsafe or extra-root archive entry: {name}")
    return "/".join(parts),is_directory


def index_sma_members(source: Path) -> tuple[str, ...]:
    """List safe file members in a ZIP-compatible Data.sma without extraction."""
    source=Path(source)
    with _open_sma_archive(source) as archive:
        result=[]
        seen=set()
        for info in archive.infolist():
            name,is_directory=normalize_sma_member_name(info.filename)
            if name in seen:
                raise ValueError(f"duplicate SMA archive member name: {name}")
            seen.add(name)
            if not is_directory:
                result.append(name)
        return tuple(result)


def read_sma_member(source: Path, requested_name: str) -> bytes:
    """Read one safe SMA member by case-insensitive Windows path."""
    requested,_=normalize_sma_member_name(requested_name)
    folded=requested.casefold()
    with _open_sma_archive(Path(source)) as archive:
        matches=[]
        seen=set()
        for info in archive.infolist():
            name,is_directory=normalize_sma_member_name(info.filename)
            if name in seen:
                raise ValueError(f"duplicate SMA archive member name: {name}")
            seen.add(name)
            if not is_directory and name.casefold()==folded:
                matches.append(info)
        if not matches:
            raise FileNotFoundError(f"SMA member not found: {requested}")
        if len(matches)>1:
            raise ValueError(f"ambiguous case-insensitive SMA member: {requested}")
        with archive.open(matches[0]) as handle:
            return handle.read()


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
    with _open_sma_archive(source) as archive:
        names=archive.namelist()
        if archive.testzip() is not None:
            raise ValueError("corrupt SMA archive")
        seen=set()
        for info in archive.infolist():
            name,_=normalize_sma_member_name(info.filename)
            if name in seen:
                raise ValueError("duplicate SMA archive member names")
            seen.add(name)
        archive.extractall(output)
    return {"source_sha256":sha256(source),"output":str(output),"member_count":len(names),"status":"STRUCTURALLY_VALID"}
