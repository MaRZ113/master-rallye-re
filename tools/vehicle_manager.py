"""Vehicle Manager v1: install, remove and order vehicles of an installed roster without touching any loader.

docs/vehicle-manager/DESIGN.md phase 3, docs/vehicle-manager/VEHICLE_MANAGER.md (usage). Everything lives in the game's
MRMods/Vehicles folder; the game, its Data.sma, MRallye.exe and both proxy DLLs are never modified.

  MRMods/Vehicles/manager/base/      the reference roster (roster.mrvr v2 + resources + variants), imported once
  MRMods/Vehicles/manager/packages/  installed vehicle packages (*.mrcar)
  MRMods/Vehicles/manager/roster.json  the owner's selection: per-class order, removed IDs, enabled packages
  MRMods/Vehicles/active/            what the dinput8 VehicleRoster module installs (rebuilt by `apply`)

Native vehicles (physical IDs) come from the base roster: they can be reordered inside their class, and SDK vehicles
(ID > 24) can be removed and restored. A removed ID is a tombstone: never reused, a save that references it falls back
to ID0 (loader save guard). Retail IDs 0..24 can only be reordered. Adding a new native vehicle needs a new base from
the Vehicle SDK registry builder (`import-base`); `apply` keeps the selection where IDs still exist.

Packages (.mrcar, ZIP): kind "variant" = an alternative model of a family shown as an extra MODEL choice (DEMO): its
resource folder, display names and the family whose physics it clones. They need no native change.

`apply` rebuilds active/ from the base in a fresh active.new/ (class tables, class counts, selection publisher bound,
Vehicle Select widgets, MRLP loader profile, variants, physics clones), verifies it and swaps it in atomically
(previous kept as active.prev/). `stock` disables the roster (game runs stock, saves fall back safely).
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, re, shutil, struct, sys, time, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from roster_v4 import Rvp, Image, CLASSES, CLASS_COUNT_OPS, reorder_scene   # noqa: E402
from roster_loader_profile import (build_profile, to_v2, strip_v2, read_profile_masks, parse_roster,  # noqa: E402
                                   class_map, fnv64, HEADER)

RETAIL_SHA = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
SCHEMA = "mr-vehicle-manager/1"
PACKAGE_SCHEMA = "mr-vehicle-package/1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Manager:
    def __init__(self, game: Path):
        self.game = game.resolve()
        self.mods = self.game / "MRMods" / "Vehicles"
        self.root = self.mods / "manager"
        self.base = self.root / "base"
        self.packages = self.root / "packages"
        self.selection_path = self.root / "roster.json"

    # ---- base ---------------------------------------------------------------------------------------------
    def import_base(self, source: Path | None = None, force: bool = False, names: Path | None = None) -> dict:
        """Snapshot an installed roster (default: the current active/) as the reference base."""
        source = (source or self.mods / "active").resolve()
        roster = (source / "roster.mrvr").read_bytes()
        if struct.unpack_from("<I", roster, 4)[0] != 2:
            raise ValueError("the base must be a roster.mrvr v2 (tools/roster_loader_profile.py)")
        if self.base.exists():
            if not force:
                raise ValueError("a base already exists; use --force to replace it (the selection is kept)")
            shutil.rmtree(self.base)
        shutil.copytree(source, self.base, ignore=shutil.ignore_patterns("variants.ini"))
        self.packages.mkdir(parents=True, exist_ok=True)
        # Variants of the source become packages, so they can be removed and re-installed individually.
        variants = parse_variants(source / "variants.ini") if (source / "variants.ini").is_file() else []
        made = []
        for v in variants:
            folder = self.base / "resources/DataGx/Vehicles" / v["folder"]
            if not folder.is_dir():
                continue
            name = f"{v['base']}-{v['label'] if 'label' in v else 'DEMO'}".lower()
            path = self.packages / f"{name}.mrcar"
            write_variant_package(path, v, folder)
            shutil.rmtree(folder)                         # the package owns these files now
            made.append(path.name)
        for xml in ("DataGame/vehicles.xml", "DataGame/Modifications.xml"):   # physics clones belong to packages too
            p = self.base / "resources" / xml
            text = p.read_bytes().decode("latin-1")
            for v in variants:
                text = drop_block(text, v["folder"])
            p.write_bytes(text.encode("latin-1"))
        if names:                                        # {id: label} or a presentation spec with markers[id, family]
            raw = json.loads(names.read_text(encoding="utf-8"))
            table = {str(m["id"]): m["family"] for m in raw["markers"]} if "markers" in raw else {str(k): v for k, v in raw.items()}
            (self.base / "names.json").write_text(json.dumps(table, indent=1) + "\n", encoding="utf-8")
        sel = self.selection()
        sel["packages"] = sorted(set(sel.get("packages", [])) | set(made))
        self.save_selection(sel)
        return {"base": str(self.base), "records": self.native()["count"], "packages_created": made}

    def native(self) -> dict:
        roster = (self.base / "roster.mrvr").read_bytes()
        r = parse_roster(strip_v2(roster))
        count, classes = class_map(r)
        order = {c: [] for c in CLASSES}
        d, payload, base = r["descriptor"], r["payload"], r["ext_address"]
        counts = struct.unpack_from("<3I", payload, d[7] - base)
        tables = struct.unpack_from("<3I", payload, d[8] - base)
        for i, c in enumerate(CLASSES):
            order[c] = list(struct.unpack_from(f"<{counts[i]}I", payload, tables[i] - base))
        names_path = self.base / "names.json"
        names = json.loads(names_path.read_text(encoding="utf-8")) if names_path.is_file() else {}
        return {"count": count, "classes": order, "masks": read_profile_masks(roster), "names": {int(k): v for k, v in names.items()}}

    # ---- selection ------------------------------------------------------------------------------------------
    def selection(self) -> dict:
        if self.selection_path.is_file():
            return json.loads(self.selection_path.read_text(encoding="utf-8"))
        return {"schema": SCHEMA, "classes": None, "removed": [], "packages": []}

    def save_selection(self, sel: dict):
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.selection_path.with_suffix(".json.new")
        tmp.write_text(json.dumps(sel, indent=1) + "\n", encoding="utf-8")
        os.replace(tmp, self.selection_path)

    def plan(self) -> dict:
        """Effective class order: the base order, the owner's order where given, removed IDs left out."""
        native = self.native()
        sel = self.selection()
        removed = set(sel.get("removed", []))
        out = {}
        for c in CLASSES:
            base = native["classes"][c]
            wanted = (sel.get("classes") or {}).get(c) or base
            order = [i for i in wanted if i in base] + [i for i in base if i not in wanted]
            out[c] = [i for i in order if i not in removed]
        return out

    def set_order(self, cls: str, ids: list[int]):
        native = self.native()["classes"][cls]
        if sorted(ids) != sorted(i for i in native if i in ids) or len(set(ids)) != len(ids) or set(ids) - set(native):
            raise ValueError(f"{cls}: only IDs of this class, each once")
        sel = self.selection()
        sel["classes"] = sel.get("classes") or {}
        sel["classes"][cls] = ids + [i for i in self.plan()[cls] if i not in ids]
        self.save_selection(sel)

    def move(self, vid: int, delta: int):
        plan = self.plan()
        cls = next(c for c in CLASSES if vid in plan[c])
        order = plan[cls]
        i = order.index(vid)
        j = max(0, min(len(order) - 1, i + delta))
        order.insert(j, order.pop(i))
        self.set_order(cls, order)

    def remove(self, vid: int):
        if vid <= 24:
            raise ValueError("retail vehicles (ID 0..24) can be reordered, not removed")
        plan = self.plan()
        cls = next((c for c in CLASSES if vid in plan[c]), None)
        if cls is None:
            raise ValueError(f"ID {vid} is not offered by the roster")
        if len(plan[cls]) <= 1:
            raise ValueError(f"{cls} would become empty")
        sel = self.selection()
        sel["removed"] = sorted(set(sel.get("removed", [])) | {vid})
        self.save_selection(sel)

    def restore(self, vid: int):
        sel = self.selection()
        sel["removed"] = [i for i in sel.get("removed", []) if i != vid]
        self.save_selection(sel)

    # ---- packages -------------------------------------------------------------------------------------------
    def list_packages(self) -> list[dict]:
        out = []
        enabled = set(self.selection().get("packages", []))
        for p in sorted(self.packages.glob("*.mrcar")) if self.packages.is_dir() else []:
            m = read_package(p)[0]
            out.append({"file": p.name, "enabled": p.name in enabled, **{k: m[k] for k in ("kind", "name", "base", "folder", "manufacturer", "model")}})
        return out

    def install(self, package: Path) -> str:
        manifest, files = read_package(package)          # validates
        self.packages.mkdir(parents=True, exist_ok=True)
        target = self.packages / package.name
        if target.resolve() != package.resolve():
            shutil.copyfile(package, target)
        sel = self.selection()
        sel["packages"] = sorted(set(sel.get("packages", [])) | {target.name})
        self.save_selection(sel)
        return target.name

    def uninstall(self, name: str, delete: bool = False):
        sel = self.selection()
        sel["packages"] = [p for p in sel.get("packages", []) if p != name]
        self.save_selection(sel)
        if delete and (self.packages / name).is_file():
            (self.packages / name).unlink()

    # ---- apply -------------------------------------------------------------------------------------------------
    def apply(self) -> dict:
        exe = (self.game / "MRallye.exe").read_bytes()
        if sha(exe) != RETAIL_SHA:
            raise ValueError("MRallye.exe is not the retail executable this roster is built for")
        core = (self.game / "MRallyeRandomizerRuntime.dll").read_bytes()
        native = self.native()
        plan = self.plan()
        roster_v2 = (self.base / "roster.mrvr").read_bytes()
        v1 = rebuild_classes(strip_v2(roster_v2), native["classes"], plan, exe)
        masks = {pid: m for pid, m in native["masks"].items()}
        profile, summary = build_profile(v1, exe, core, masks=masks)
        roster = to_v2(v1, profile)

        staging, active, previous = self.mods / "active.new", self.mods / "active", self.mods / "active.prev"
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(self.base, staging)
        (staging / "roster.mrvr").write_bytes(roster)
        res = staging / "resources"
        scene = res / "DataScene/FrontendScreens/VehicleSelect.xml"
        if plan != native["classes"]:
            text = scene.read_bytes().decode("latin-1")
            scene.write_bytes(reorder_scene(text, native["classes"], plan).encode("latin-1"))
        # Packages: variant folders, physics clones, variants.ini.
        ini = ["; Written by the Vehicle Manager (tools/vehicle_manager.py); edit the selection there."]
        enabled = self.selection().get("packages", [])
        vehicles_xml = res / "DataGame/vehicles.xml"
        mods_xml = res / "DataGame/Modifications.xml"
        vtext, mtext = vehicles_xml.read_bytes().decode("latin-1"), mods_xml.read_bytes().decode("latin-1")
        n = 0
        for name in enabled:
            path = self.packages / name
            if not path.is_file():
                continue
            m, files = read_package(path)
            for rel, data in files.items():
                out = res / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(data)
            vtext = clone_block(vtext, m["physics_block"], m["folder"])
            mtext = clone_block(mtext, m["physics_block"], m["folder"])
            ini += [f"[Variant{n}]", f"Base={m['base']}", f"Folder={m['folder']}", f"Manufacturer={m['manufacturer']}",
                    f"Model={m['model']}"]
            for role, data in m["_art"].items():
                ini.append(f"{ART_KEYS[role]}={append_art(res, role, data, self.game)}")
            ini.append(f"; package {name}")
            n += 1
        vehicles_xml.write_bytes(vtext.encode("latin-1"))
        mods_xml.write_bytes(mtext.encode("latin-1"))
        (staging / "variants.ini").write_bytes(("\r\n".join(ini) + "\r\n").encode("ascii"))
        catalog_path = staging / "catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.is_file() else {}
        catalog.update({"schema": "mr-vehicle-roster/1", "label": "Vehicle Manager", "classes": plan,
                        "removed": sorted(set(sum(native["classes"].values(), [])) - set(sum(plan.values(), []))),
                        "packages": enabled, "roster_mrvr_sha256": sha(roster),
                        "resources": [{"path": p.relative_to(res).as_posix(), "sha256": sha(p.read_bytes()), "size": p.stat().st_size}
                                      for p in sorted(res.rglob("*")) if p.is_file()],
                        "active_derivation": {"tool": "tools/vehicle_manager.py apply", "base_roster_sha256": sha(roster_v2)}})
        catalog_path.write_text(json.dumps(catalog, indent=1) + "\n", encoding="utf-8")
        verify_active(staging)
        swap(staging, active, previous)
        return {"active": str(active), "classes": plan, "variants": n, "loader_profile": {k: summary[k] for k in ("checks", "registry_count", "sdk_vehicles")}}

    def stock(self) -> str:
        active, disabled = self.mods / "active", self.mods / "active.disabled"
        if not active.exists():
            return "already stock"
        if disabled.exists():
            shutil.rmtree(disabled)
        retry(os.replace, active, disabled)
        return f"roster disabled ({disabled}); `apply` installs it again"


# ---- native class tables ---------------------------------------------------------------------------------------
def rebuild_classes(v1: bytes, old: dict, new: dict, exe: bytes) -> bytes:
    """Reorder / retire inside the classes of a roster.mrvr v1 (same checks as tools/roster_v4.py transform)."""
    if old == new:
        return v1
    r = parse_roster(v1)
    rvp_off, rvp_size, ext_off, ext_size = struct.unpack_from("<IIII", v1, 144)
    rvp = Rvp(v1[rvp_off:rvp_off + rvp_size])
    img = Image(v1[ext_off:ext_off + ext_size], rvp, r["writable"], exe)
    d = r["descriptor"]
    count, counts_va, ptrs_va, rc_va, rl_va = d[3], d[7], d[8], d[9], d[10]
    ptrs = struct.unpack("<3I", img.read(ptrs_va, 12))
    for i, c in enumerate(CLASSES):
        if set(new[c]) - set(old[c]) or len(set(new[c])) != len(new[c]) or not new[c]:
            raise ValueError(f"{c}: only in-class reordering and retirement are supported")
        img.write(ptrs[i], struct.pack(f"<{len(new[c])}I", *new[c]) + bytes(4 * (len(old[c]) - len(new[c]))))
    img.write(counts_va, struct.pack("<3I", *[len(new[c]) for c in CLASSES]))
    reverse = {p: (i, n) for i, c in enumerate(CLASSES) for n, p in enumerate(new[c])}
    img.write(rc_va, struct.pack(f"<{count}I", *[reverse.get(p, (0, 0))[0] for p in range(count)]))
    img.write(rl_va, struct.pack(f"<{count}I", *[reverse.get(p, (0, 0))[1] for p in range(count)]))
    for c, (va, prefix) in CLASS_COUNT_OPS.items():
        current = img.read(va, len(prefix) + 1)
        if current is None or current[:len(prefix)] != prefix or current[-1] != len(old[c]):
            raise ValueError(f"class count owner of {c} differs at {va:#x}")
        img.write(va + len(prefix), bytes([len(new[c])]))
    bound = max(len(old[c]) for c in CLASSES)
    hits = [m.start() for m in re.finditer(rb"\x81\xfe" + struct.pack("<I", bound) + rb"\x0f\x8c", bytes(img.payload))]
    if len(hits) != 1:
        raise ValueError("selection publisher bound not found exactly once")
    img.payload[hits[0] + 2:hits[0] + 6] = struct.pack("<I", max(len(new[c]) for c in CLASSES))
    new_rvp = rvp.build()
    if len(new_rvp) != rvp_size or len(img.payload) != ext_size:
        raise ValueError("class edits must not change the transaction layout")
    body = v1[HEADER:rvp_off] + new_rvp + v1[rvp_off + rvp_size:ext_off] + bytes(img.payload) + v1[ext_off + ext_size:]
    header = bytearray(v1[:HEADER])
    struct.pack_into("<Q", header, 160, fnv64(body))
    return bytes(header) + body


# Frame banks the variant artwork is appended to: (bank, template frame giving size/format, variants.ini key).
ART_BANKS = {"carsheet": ("DataGx/Frontend/VehicleSelect/carsheet", 3), "smallcarsheet": ("DataGx/Frontend/RaceResults/smallcarsheet", 9)}
ART_KEYS = {"carsheet": "CarSheetFrame", "smallcarsheet": "SmallFrame"}


def game_file(res: Path, game: Path, rel: str) -> bytes:
    """A file as the game resolves it: roster overlay, loose game file, then Data.sma."""
    for root in (res, game):
        if (root / rel).is_file():
            return (root / rel).read_bytes()
    import zlib
    from vehicle_roster_build import archive_index, norm
    blob, members = archive_index(game / "Data.sma")
    method, start, cs, _us = members[norm(rel)]
    raw = blob[start:start + cs]
    return raw if method == 0 else zlib.decompress(raw, -15)


def append_art(res: Path, role: str, data: bytes, game: Path) -> int:
    """Append one frame to a staged bank (template frame size/format, car contained like SDK icons); returns its index."""
    sys.path.insert(0, str(HERE.parents[1] / "master-rallye-re-v-cap" / "src"))
    from master_rallye.addon_sdk.ui_assets import parse_bank, append_frame, fit_rgba
    from master_rallye.dxt import parse_dxt_bytes, decode_rgba_pixels, encode_dxt_pixels
    bank_rel, template = ART_BANKS[role]
    folder = res / bank_rel.rsplit("/", 1)[0]
    bank_path = res / (bank_rel + ".dxb")
    bank, name = append_frame(bank_path.read_bytes(), template)
    tname = parse_bank(bank)["names"][template]
    tmpl = parse_dxt_bytes(game_file(res, game, bank_rel.rsplit("/", 1)[0] + "/" + tname + ".dxt"))
    art = parse_dxt_bytes(data)
    rgba = decode_rgba_pixels(art)
    if (art.width, art.height) != (tmpl.width, tmpl.height):
        rgba = bytes(fit_rgba((art.width, art.height, rgba), tmpl.width, tmpl.height, 1))
    (folder / (name + ".dxt")).write_bytes(encode_dxt_pixels(tmpl, rgba, tmpl.width, tmpl.height))
    bank_path.write_bytes(bank)
    return parse_bank(bank)["count"] - 1


# ---- packages ---------------------------------------------------------------------------------------------------
def parse_variants(path: Path) -> list[dict]:
    out, cur = [], None
    for line in path.read_text(encoding="ascii", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("[Variant"):
            cur = {}; out.append(cur)
        elif cur is not None and "=" in line and not line.startswith(";"):
            k, v = line.split("=", 1); cur[k.strip().lower()] = v.strip()
    return [v for v in out if v.get("base") and v.get("folder")]


def physics_block_of(base_family: str) -> str:
    # vehicles.xml block names of retail families (folder -> block); everything else uses the folder name.
    return {"megane": "Megane", "landcruiser": "Landcruiser", "newrav": "Newrav", "tata": "Tata"}.get(base_family.lower(), base_family)


def write_variant_package(path: Path, v: dict, folder: Path):
    manifest = {"schema": PACKAGE_SCHEMA, "kind": "variant", "name": f"{v['base']} DEMO", "base": v["base"],
                "physics_block": physics_block_of(v["base"]), "folder": v["folder"], "label": "DEMO",
                "manufacturer": v.get("manufacturer", ""), "model": v.get("model", ""), "files": []}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.iterdir()):
            if f.is_file():
                rel = f"DataGx/Vehicles/{v['folder']}/{f.name}"
                data = f.read_bytes()
                z.writestr("files/" + rel, data)
                manifest["files"].append({"path": rel, "sha256": sha(data)})
        z.writestr("manifest.json", json.dumps(manifest, indent=1))


def read_package(path: Path):
    with zipfile.ZipFile(path) as z:
        m = json.loads(z.read("manifest.json"))
        if m.get("schema") != PACKAGE_SCHEMA or m.get("kind") != "variant":
            raise ValueError(f"{path.name}: unsupported package (schema/kind)")
        folder = m["folder"]
        if not re.fullmatch(r"[A-Za-z0-9_]{1,48}", folder) or not re.fullmatch(r"[A-Za-z0-9_]{1,48}", m["physics_block"]):
            raise ValueError(f"{path.name}: invalid folder name")
        files = {}
        for item in m["files"]:
            rel = item["path"]
            if not rel.startswith(f"DataGx/Vehicles/{folder}/") or ".." in rel or "\\" in rel:
                raise ValueError(f"{path.name}: file outside its folder: {rel}")
            data = z.read("files/" + rel)
            if sha(data) != item["sha256"]:
                raise ValueError(f"{path.name}: {rel} hash mismatch")
            files[rel] = data
        if f"DataGx/Vehicles/{folder}/car.dx" not in files or f"DataGx/Vehicles/{folder}/complete.dx" not in files:
            raise ValueError(f"{path.name}: car.dx and complete.dx are required")
        # Optional artwork (any DXT size): Vehicle Select CarSheet and race SIDE/Results small icon of the variant.
        art = {}
        for role, item in (m.get("art") or {}).items():
            if role not in ART_BANKS or not re.fullmatch(r"art/[A-Za-z0-9_.-]{1,64}\.dxt", item["path"]):
                raise ValueError(f"{path.name}: invalid art entry {role}")
            data = z.read(item["path"])
            if sha(data) != item["sha256"]:
                raise ValueError(f"{path.name}: {item['path']} hash mismatch")
            art[role] = data
        m["_art"] = art
        return m, files


def drop_block(text: str, family: str) -> str:
    eol = "\r\n" if "\r\n" in text else "\n"
    return eol.join(l for l in text.split(eol) if f'Name="Vehicles/{family}/' not in l)


def clone_block(text: str, base: str, variant: str) -> str:
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = [l for l in text.split(eol) if f'Name="Vehicles/{variant}/' not in l]
    src = [i for i, l in enumerate(lines) if f'Name="Vehicles/{base}/' in l]
    if not src:
        raise ValueError(f"no Vehicles/{base}/ block to clone")
    clones = [lines[i].replace(f'Name="Vehicles/{base}/', f'Name="Vehicles/{variant}/', 1) for i in src]
    return eol.join(lines[:src[-1] + 1] + clones + lines[src[-1] + 1:])


# ---- verification / swap ------------------------------------------------------------------------------------------
def verify_active(folder: Path):
    roster = (folder / "roster.mrvr").read_bytes()
    if roster[:4] != b"MRVR" or struct.unpack_from("<I", roster, 4)[0] != 2:
        raise ValueError("active roster is not MRVR v2")
    if fnv64(roster[HEADER:]) != struct.unpack_from("<Q", roster, 160)[0]:
        raise ValueError("active roster digest mismatch")
    for v in parse_variants(folder / "variants.ini"):
        for role in ("car.dx", "complete.dx", "wheel.dx"):
            if not (folder / "resources/DataGx/Vehicles" / v["folder"] / role).is_file():
                raise ValueError(f"variant {v['folder']} lacks {role}")


def retry(action, *args):
    for attempt in range(4):
        try:
            return action(*args)
        except PermissionError:
            if attempt == 3:
                raise
            time.sleep(0.5)


def swap(staging: Path, active: Path, previous: Path):
    if previous.exists():
        retry(shutil.rmtree, previous)
    if active.exists():
        retry(os.replace, active, previous)
    retry(os.replace, staging, active)


# ---- CLI ----------------------------------------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--game", type=Path, required=True, help="game folder (MRallye.exe, MRMods/Vehicles)")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("import-base"); b.add_argument("--source", type=Path); b.add_argument("--force", action="store_true")
    b.add_argument("--names", type=Path, help="labels: JSON {id: name} or docs/vehicle-manager/presentation-fix-01.json")
    sub.add_parser("list")
    o = sub.add_parser("order"); o.add_argument("cls", choices=CLASSES); o.add_argument("ids", help="comma-separated physical IDs")
    for name in ("remove", "restore"):
        sub.add_parser(name).add_argument("id", type=int)
    mv = sub.add_parser("move"); mv.add_argument("id", type=int); mv.add_argument("delta", type=int)
    i = sub.add_parser("install"); i.add_argument("package", type=Path)
    u = sub.add_parser("uninstall"); u.add_argument("name"); u.add_argument("--delete", action="store_true")
    sub.add_parser("apply"); sub.add_parser("stock"); sub.add_parser("gui")
    a = p.parse_args(argv)
    m = Manager(a.game)
    if a.cmd == "gui":
        from vehicle_manager_gui import run
        return run(m)
    result = {
        "import-base": lambda: m.import_base(a.source, a.force, a.names),
        "list": lambda: {"classes": m.plan(), "removed": m.selection().get("removed", []), "packages": m.list_packages()},
        "order": lambda: m.set_order(a.cls, [int(x) for x in a.ids.split(",")]) or m.plan(),
        "remove": lambda: m.remove(a.id) or m.plan(),
        "restore": lambda: m.restore(a.id) or m.plan(),
        "move": lambda: m.move(a.id, a.delta) or m.plan(),
        "install": lambda: m.install(a.package),
        "uninstall": lambda: m.uninstall(a.name, a.delete) or m.list_packages(),
        "apply": m.apply,
        "stock": m.stock,
    }[a.cmd]()
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
