"""Private GT3/GT4 Sound Bank Lab. Original assets are always opened read-only.

Only parser source, schemas, documentation and synthetic fixtures may be shared.
Generated catalogs contain private database contents and must stay private.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from master_rallye.addon_sdk.gt4_spec import DatabaseTable
from gt4_audio_extract import parse_engn, extract as extract_engine, sha256, pitch_core_evidence, decode_spu, pcm_wav
from gt_sound_jam import inspect as inspect_instrument, extract as extract_instrument, resolve_events
from gt3_audio_inspect import events

SCHEMA = "gt-sound-bank-lab/1"
VARIANTS = ("engine", "normal0", "normal1", "normal2", "normal3", "turbo0", "turbo1", "turbo2", "turbo3")


def file_identity(path):
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": h.hexdigest()}


def read_bounded(path, limit=16 * 1024 * 1024):
    path = Path(path)
    if not path.is_file() or not 1 <= path.stat().st_size <= limit:
        raise ValueError("source file missing or exceeds byte budget: " + str(path))
    raw = path.read_bytes()
    if len(raw) > limit:
        raise ValueError("source changed beyond byte budget")
    return raw


def private_output(path, source_roots=()):
    """Reject source-tree destinations, link ancestors and overwrites."""
    path = Path(path).absolute()
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink() or getattr(ancestor, "is_junction", lambda: False)():
            raise ValueError("output link/reparse ancestor forbidden")
    dest = path.resolve()
    for root in source_roots:
        root = Path(root).resolve()
        if dest == root or dest.is_relative_to(root):
            raise ValueError("output must be outside original source tree")
    if dest.exists():
        raise ValueError("new private output required; refusing overwrite")
    return dest


def save_json(path, value, source_roots=()):
    path = private_output(path, source_roots)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def label_records(raw):
    if not 16 <= len(raw) <= 64 * 1024 * 1024 or raw[:4] != b"GTID":
        raise ValueError("bounded GTID required")
    count = struct.unpack_from("<I", raw, 4)[0]
    base = 16 + count * 8
    if count > 100000 or base > len(raw):
        raise ValueError("GTID record budget")
    result = []; names = set()
    for i in range(count):
        relative, row = struct.unpack_from("<II", raw, 16 + i * 8)
        at = base + relative
        if at + 2 > len(raw):
            raise ValueError("GTID pointer outside strings")
        n = struct.unpack_from("<H", raw, at)[0]
        if not 2 <= n <= 4096 or at + 2 + n > len(raw):
            raise ValueError("GTID string bounds")
        text = raw[at + 2:at + 2 + n]
        if text[-1] or b"\0" in text[:-1]:
            raise ValueError("invalid GTID string")
        name = text[:-1].decode("ascii")
        if name in names:
            raise ValueError("duplicate GTID label")
        names.add(name)
        result.append({"label": name, "row_id": row, "label_record_offset": 16 + i * 8})
    return result


class SourceTable:
    """Reuse the existing row decoder, retaining repeated physical row IDs.

    Qualified flags 2/3 have the same compression bit as 0/1 in local PDTools
    Table.cs. In-memory ordinal IDs avoid collapsing repeated variation IDs.
    Source digests and file offsets always refer to the unchanged source bytes.
    """
    def __init__(self, path, size, grouped=False):
        self.path = Path(path)
        self.raw = read_bounded(path, 64 * 1024 * 1024)
        if len(self.raw) < 16 or self.raw[:4] != b"GTDB":
            raise ValueError("GTDB required")
        flags, alignment, count, row_size = struct.unpack_from("<HHII", self.raw, 4)
        if flags not in ((0, 1, 2, 3) if grouped else (0, 1)) or row_size != size or count > 100000 or 16 + 8 * count > len(self.raw):
            raise ValueError("unqualified GT4 table layout: " + self.path.name)
        self.source_rows = [struct.unpack_from("<II", self.raw, 16 + 8 * i) for i in range(count)]
        adapted = bytearray(self.raw)
        struct.pack_into("<H", adapted, 4, flags & 1)
        for i in range(count):
            struct.pack_into("<I", adapted, 16 + i * 8, i)
        self.decoder = DatabaseTable(bytes(adapted))
        self.indices = defaultdict(list)
        for i, (rid, offset) in enumerate(self.source_rows):
            self.indices[rid].append(i)
        if not grouped and any(len(v) != 1 for v in self.indices.values()):
            raise ValueError("ambiguous GT4 row ID")
        self.cache = {}
        self.identity = {"path": str(self.path.resolve()), "sha256": sha256(self.raw), "bytes": len(self.raw),
                         "flags": flags, "alignment": alignment, "row_size": row_size, "physical_rows": count}

    def row(self, row_id, occurrence=0):
        if row_id not in self.indices or not 0 <= occurrence < len(self.indices[row_id]):
            raise ValueError("GT4 referenced row absent")
        index = self.indices[row_id][occurrence]
        if index not in self.cache:
            self.cache[index] = self.decoder.row(index)
        raw = self.cache[index]
        return raw, {"row_id": row_id, "occurrence": occurrence, "index_record_offset": 16 + index * 8,
                     "encoded_row_offset": self.decoder.data_at + self.source_rows[index][1],
                     "decoded_row_sha256": sha256(raw), "table_sha256": self.identity["sha256"]}


def source_strings(raw):
    if len(raw) < 16 or raw[:4] != b"GTST" or struct.unpack_from("<I", raw, 8)[0] != 1:
        raise ValueError("qualified little-endian GTST required")
    count = struct.unpack_from("<I", raw, 4)[0]
    base = 16 + 4 * count
    if count > 100000 or base > len(raw):
        raise ValueError("GTST count budget")
    result = []
    for i in range(count):
        at = base + struct.unpack_from("<I", raw, 16 + i * 4)[0]
        if at + 2 > len(raw):
            raise ValueError("GTST string pointer")
        n = struct.unpack_from("<H", raw, at)[0]
        if not 1 <= n <= 4096 or at + 2 + n > len(raw):
            raise ValueError("GTST string length")
        data = raw[at + 2:at + 2 + n]
        if data[-1] or b"\0" in data[:-1]:
            raise ValueError("GTST termination")
        result.append(data[:-1].decode("utf-8"))
    return result


def car_parts(raw, tables):
    """Original GT4 CARS part keys, including upgrades; never label matching."""
    if not 8 <= len(raw) <= 1024 * 1024:
        raise ValueError("bounded CARS part list required")
    count, reserved = struct.unpack_from("<II", raw)
    if reserved or count > 4096 or 8 + count * 16 != len(raw):
        raise ValueError("unqualified CARS part-list layout")
    result = []
    names = {12: ("ENGINE", 78), 13: ("NATUNE", 8), 14: ("TURBINEKIT", 8), 20: ("MUFFLER", 6)}
    for i in range(count):
        at = 8 + 16 * i
        key, tid, category, pad = struct.unpack_from("<4i", raw, at)
        if key == tid == -1 and 0 <= category <= 255 and pad == 0:
            result.append({"table_id": -1, "row_id": -1, "category_byte": category,
                           "parts_record_offset": at, "status": "ABSENT_SOURCE_KEY", "bank_selection": None})
            continue
        if key < 0 or not 1 <= tid <= 40 or not 0 <= category <= 255 or pad:
            raise ValueError("unqualified CARS part record")
        if tid not in names:
            continue
        name, category_at = names[tid]
        if key not in tables[name].indices:
            result.append({"table": name, "table_id": tid, "row_id": key,
                           "category_byte": category, "parts_record_offset": at,
                           "status": "UNRESOLVED_SOURCE_ROW", "bank_selection": None})
            continue
        row, evidence = tables[name].row(key)
        if row[category_at] != category:
            result.append({"table": name, "table_id": tid, "row_id": key,
                           "category_byte": category, "parts_record_offset": at,
                           "part_row_category_byte": row[category_at], "source": evidence,
                           "status": "SOURCE_CATEGORY_DISAGREEMENT", "bank_selection": None})
            continue
        result.append({"table": name, "table_id": tid, "row_id": key,
                       "category_byte": category, "parts_record_offset": at, "source": evidence,
                       "status": "SOURCE_PART_KEY_VERIFIED", "bank_selection": None})
    return result


def gt4_catalog(root):
    """Complete source-key map for this qualified US2560 layout; no WAV data."""
    root = Path(root).resolve()
    folder = root / "specdb/GT4_PREMIUM_US2560"
    sizes = {"GENERIC_CAR": 24, "DEFAULT_PARTS": 208, "ENGINE": 113,
             "NATUNE": 11, "TURBINEKIT": 18, "MUFFLER": 7}
    tables = {name: SourceTable(folder / (name + ".dbt"), size) for name, size in sizes.items()}
    expected_ids = {"GENERIC_CAR": 0, "DEFAULT_PARTS": 36, "ENGINE": 12, "NATUNE": 13, "TURBINEKIT": 14, "MUFFLER": 20}
    for name, table in tables.items():
        idi = read_bounded(folder / (name + ".idi"))
        if len(idi) < 16 or idi[:4] != b"GTID" or struct.unpack_from("<I", idi, 12)[0] != expected_ids[name]:
            raise ValueError("unqualified original table ID: " + name)
        table.identity.update(table_id=expected_ids[name], labels_sha256=sha256(idi))
    labels_raw = read_bounded(folder / "GENERIC_CAR.idi")
    labels = label_records(labels_raw)
    sound_engines = defaultdict(list)
    for rid in tables["ENGINE"].indices:
        raw, _ = tables["ENGINE"].row(rid)
        sound_engines[struct.unpack_from("<H", raw, 24)[0]].append(rid)
    cv = SourceTable(folder / "CAR_VARIATION_american.dbt", 8, grouped=True)
    variations = SourceTable(folder / "VARIATIONamerican.dbt", 52, grouped=True)
    strings_raw = read_bounded(folder / "american_StrDB.sdb")
    strings = source_strings(strings_raw)
    sources = {name: table.identity for name, table in tables.items()}
    sources.update(CAR_VARIATION_american=cv.identity, VARIATIONamerican=variations.identity,
                   american_StrDB={"sha256": sha256(strings_raw)}, GENERIC_CAR_idi={"sha256": sha256(labels_raw)})
    banks = []
    bank_paths = {}
    for variant in VARIANTS:
        folder_bank = root / "carsound" / variant
        if not folder_bank.is_dir():
            continue
        for source in sorted(folder_bank.iterdir()):
            if not source.is_file() or not re.fullmatch(r"\d{1,5}", source.name):
                raise ValueError("unexpected carsound entry: " + str(source))
            sid = int(source.name)
            bank_id = "carsound/" + variant + "/" + source.name
            if (sid, variant) in bank_paths:
                raise ValueError("ambiguous numeric bank identity")
            bank_paths[sid, variant] = bank_id
            banks.append({"bank_id": bank_id, "sound_id": sid, "variant": variant, "bytes": source.stat().st_size,
                          "association": "candidate for same Sound ID; actual tuning selection requires native proof"})
    vehicles = []
    for label in labels:
        rid = label["row_id"]
        generic, ge = tables["GENERIC_CAR"].row(rid)
        parts_id, parts_table = struct.unpack_from("<ii", generic)
        if parts_id < 0 or parts_table != 36:
            raise ValueError("unqualified DefaultParts reference")
        parts, pe = tables["DEFAULT_PARTS"].row(parts_id)
        engine_id, engine_table = struct.unpack_from("<ii", parts, 88)
        if engine_id < 0 or engine_table != 12:
            raise ValueError("unqualified Engine reference")
        engine, ee = tables["ENGINE"].row(engine_id)
        sound = struct.unpack_from("<H", engine, 24)[0]
        tuning = {}
        for name, at, tid, category_at in (("NATUNE", 96, 13, 8), ("TURBINEKIT", 104, 14, 8), ("MUFFLER", 152, 20, 6)):
            key, table_id = struct.unpack_from("<ii", parts, at)
            if key == table_id == -1:
                tuning[name] = {"status": "ABSENT_SOURCE_KEY", "default_parts_field_offset": at}
                continue
            if key < 0 or table_id != tid:
                raise ValueError("unqualified tuning reference " + name)
            raw, ev = tables[name].row(key)
            tuning[name] = {"status": "SOURCE_DEFAULT_PART", "table_id": table_id,
                            "default_parts_field_offset": at, "category_byte": raw[category_at],
                            "category_field_offset": category_at, "source": ev,
                            "bank_selection": None}
            if name == "TURBINEKIT":
                tuning[name]["wastegate_byte"] = raw[9]
        cv_raw, cve = cv.row(rid)
        variation, vt = struct.unpack_from("<ii", cv_raw)
        if vt != 42 or variation < 0:
            raise ValueError("unqualified Variation reference")
        models = []; model_rows = []
        for occurrence in range(len(variations.indices.get(variation, []))):
            vraw, ve = variations.row(variation, occurrence)
            string_id = struct.unpack_from("<I", vraw)[0]
            if string_id >= len(strings) or not re.fullmatch(r"[a-z0-9_]{1,40}", strings[string_id]):
                raise ValueError("unqualified ModelCode string reference")
            models.append(strings[string_id]); model_rows.append(ve)
        if not models:
            raise ValueError("missing model variation")
        models = sorted(set(models))
        parts_path = folder / "CARS" / f"{rid:016X}"
        parts_raw = read_bounded(parts_path, 1024 * 1024)
        options = car_parts(parts_raw, tables)
        stage = tuning["MUFFLER"].get("category_byte", 0)
        turbo = tuning["TURBINEKIT"].get("wastegate_byte", 0) != 0
        default_variant = ("turbo" if turbo else "normal") + str(stage)
        vehicles.append({"vehicle_id": label["label"], "generic_car_row": rid, "model_codes": models,
                         "model_files_present": [m for m in models if (root / "car/menu" / m).is_file() or (root / "car/race" / m).is_file()],
                         "engine_row": engine_id, "sound_id": sound, "status": "SOURCE_KEY_CHAIN_VERIFIED",
                         "source_rows": {"GENERIC_CAR": ge, "DEFAULT_PARTS": pe, "ENGINE": ee,
                                         "CAR_VARIATION_american": cve, "VARIATIONamerican": model_rows},
                         "label_record_offset": label["label_record_offset"], "default_tuning": tuning,
                         "tuning_options": options, "parts_list_source": {"path": str(parts_path), "sha256": sha256(parts_raw)},
                         "default_native_bank_candidate": {"variant": default_variant,
                             "bank_id": bank_paths.get((sound, default_variant)),
                             "status": "SUPPLIED_CORE_STATIC_INTERPRETATION_OF_DEFAULT_PARTS",
                             "evidence": "gt4-native.md:00304E98/00304FA0; equipped muffler category + turbine wastegate",
                             "runtime_confirmed": False},
                         "banks": [bank_paths[sound, v] for v in VARIANTS if (sound, v) in bank_paths],
                         "missing_bank_variants": [v for v in VARIANTS if (sound, v) not in bank_paths],
                         "engine_rows_sharing_sound": sorted(sound_engines[sound]), "selected_tuning_bank": None})
    groups = defaultdict(list)
    for v in vehicles:
        groups[v["sound_id"]].append(v["vehicle_id"])
    report = {"schema": SCHEMA, "game": "gt4", "source_root": str(root), "sources": sources,
              "vehicles": vehicles, "banks": banks,
              "shared_sound_ids": [{"sound_id": sid, "vehicle_ids": names} for sid, names in sorted(groups.items())],
              "boundary": "Verified local source key/byte associations. Metadata names follow comparative PDTools; categories are raw values. Native runtime, tuning choice, event attribution and full mixing are separate qualifications."}
    report["counts"] = {"vehicles": len(vehicles), "banks": len(banks), "sound_ids": len(groups)}
    return report


def select_vehicle(catalog, selector):
    matches = [v for v in catalog["vehicles"] if selector == v.get("vehicle_id", v.get("car_label")) or selector in v.get("model_codes", [])]
    if len(matches) != 1:
        raise ValueError("vehicle selector absent or ambiguous; select an exact vehicle_id")
    return matches[0]


def normalize_gt3(report):
    report["schema"] = SCHEMA
    report["game"] = "gt3"
    for vehicle in report["vehicles"]:
        vehicle.setdefault("vehicle_id", vehicle["car_label"])
        vehicle.setdefault("sound_id", vehicle["sound_number"])
        vehicle.setdefault("banks", vehicle["bank_ids"])
    report["counts"] = report["summary"]
    return report


def gt4_bank(root, bank_id):
    if not re.fullmatch(r"carsound/(?:engine|normal[0-3]|turbo[0-3])/\d{1,5}", bank_id) and not re.fullmatch(r"sound_gt/sound/[a-zA-Z0-9_]+\.(?:ins|es)", bank_id):
        raise ValueError("invalid explicit GT4 bank ID")
    root = Path(root).resolve()
    path = (root / bank_id).resolve()
    if not path.is_relative_to(root):
        raise ValueError("bank escapes source root")
    return path


def inspect_gt4(root, bank_id, pitch_core=None):
    path = gt4_bank(root, bank_id)
    raw = read_bounded(path)
    report = parse_engn(raw) if raw[:4] == b"ENGN" else inspect_instrument(raw)
    report.update(schema=SCHEMA, game="gt4", bank_id=bank_id, source=str(path), format=raw[:4].decode("ascii"))
    native = pitch_core_evidence(pitch_core) if pitch_core else None
    report["native_pitch_evidence"] = native
    for i, e in enumerate(report["entries"]):
        e["entry_id"] = str(i)
        if raw[:4] == b"ENGN":
            e["sample_file_offset"] = report["header_bytes"] + e["body_offset"]
            e["codec_status"] = "PCM_VALID"
            # These fields describe a comparative native interpretation, not
            # a claim that the supplied CORE was observed driving these assets.
            words = struct.unpack_from("<4hII", raw, e["record_offset"])
            e["rpm_interpretation"] = {"reference_rpm": words[0], "full_gain_min": words[1], "full_gain_max": words[2],
                                       "gain_code": words[3], "base_spu_pitch": words[4],
                                       "evidence_class": "supplied-CORE comparative native; see gt4-native.md"}
            if not bank_id.startswith("carsound/"):
                e["generic_control_fields"] = e.pop("rpm_interpretation")
                e["control_boundary"] = "Shared road layer receives a separate speed-derived control; fields are not asserted to be vehicle engine RPM."
            if native:
                rate = 48000 * words[4] / 4096
                if not 8000 <= round(rate) <= 96000:
                    raise ValueError("anchor pitch outside supported WAV rate")
                e.update(anchor_rate_exact_hz=rate, full_duration_seconds=e["samples"] / rate)
                if e["loop_start_sample"] is not None:
                    e["loop_duration_seconds"] = (e["loop_end_sample"] - e["loop_start_sample"]) / rate
    return report


def compare_banks(a, b):
    """Encoded identity and metadata comparison, never acoustic attribution."""
    ah = defaultdict(list); bh = defaultdict(list)
    for e in a["entries"]:
        if e.get("encoded_sha256"): ah[e["encoded_sha256"]].append(e["entry_id"])
    for e in b["entries"]:
        if e.get("encoded_sha256"): bh[e["encoded_sha256"]].append(e["entry_id"])
    return {"schema": SCHEMA, "same_bank_bytes": a["sha256"] == b["sha256"],
            "entries_a": len(a["entries"]), "entries_b": len(b["entries"]),
            "shared_encoded_samples": [{"sha256": h, "entries_a": ah[h], "entries_b": bh[h]} for h in sorted(ah.keys() & bh.keys())],
            "boundary": "Encoded equality does not prove equal runtime pitch, envelope, layering, gain or role."}


def gt4_inventory(root, pitch_core=None):
    catalog = gt4_catalog(root)
    records = []; errors = []; by_hash = defaultdict(list)
    for bank in catalog["banks"]:
        try:
            report = inspect_gt4(root, bank["bank_id"], pitch_core)
            records.append(report); by_hash[report["sha256"]].append(bank["bank_id"])
        except (ValueError, OSError, struct.error, UnicodeError) as error:
            errors.append({"bank_id": bank["bank_id"], "status": "UNSUPPORTED", "reason": str(error)})
    sound_dir = Path(root) / "sound_gt/sound"
    for path in sorted(list(sound_dir.glob("*.ins")) + list(sound_dir.glob("*.es"))):
        bank_id = path.relative_to(root).as_posix()
        try:
            records.append(inspect_gt4(root, bank_id))
        except (ValueError, OSError, struct.error) as error:
            errors.append({"bank_id": bank_id, "status": "UNSUPPORTED", "reason": str(error)})
    gtse = read_bounded(sound_dir / "se.inf")
    event_entries = events(gtse)
    bank_names = {"gt4sys.ins": 0, "gt4race.ins": 1, "gt4count.ins": 2, "gt4race2.ins": 3}
    event_banks = {bank_names[Path(r["bank_id"]).name]: r for r in records if Path(r["bank_id"]).name in bank_names}
    return {"schema": SCHEMA, "game": "gt4", "catalog": catalog, "banks": records, "unsupported": errors,
            "events": {"sha256": sha256(gtse), "entries": event_entries,
                       "static_native_resolution": resolve_events(event_banks, {e["name"]: int(e["token"], 16) for e in event_entries}),
                       "routing_status": "SUPPLIED_CORE_COMPARATIVE_STATIC; NO MATCHING_BUILD_RUNTIME"},
            "identical_banks": [v for v in by_hash.values() if len(v) > 1],
            "counts": {"engine_banks_valid": sum(r["bank_id"].startswith("carsound/") for r in records),
                       "shared_engn_banks_valid": sum(r["format"] == "ENGN" and not r["bank_id"].startswith("carsound/") for r in records),
                       "instrument_banks_valid": sum(r["format"] == "INST" for r in records),
                       "unsupported_banks": len(errors), "sample_entries": sum(len(r["entries"]) for r in records),
                       "unsupported_instrument_entries": sum(e["codec_status"] != "PCM_VALID" for r in records if r["format"] == "INST" for e in r["entries"])},
            "additional_sources": [file_identity(p) for p in sorted(sound_dir.iterdir()) if p.is_file() and p.suffix not in (".ins", ".es") and p.name != "se.inf"]}


def export_gt4(root, bank_id, output, sample_rate=None, pitch_core=None, entry_id=None):
    path = gt4_bank(root, bank_id)
    output = private_output(output, (Path(root).parent,))
    raw = read_bounded(path)
    if raw[:4] == b"ENGN":
        if entry_id is None:
            return extract_engine(path, output, sample_rate, pitch_core)
        if (sample_rate is None) == (pitch_core is None):
            raise ValueError("choose exactly one explicit nominal rate or qualified pitch CORE")
        if output == output.with_suffix(".json") or output.with_suffix(".json").exists():
            raise ValueError("new WAV and sidecar paths required")
        report = inspect_gt4(root, bank_id, pitch_core)
        entries = [e for e in report["entries"] if e["entry_id"] == str(entry_id)]
        if len(entries) != 1:
            raise ValueError("entry ID absent")
        e = entries[0]; at = e["sample_file_offset"]
        decoded = decode_spu(raw[at:at + e["encoded_bytes"]])
        rate = round(e["anchor_rate_exact_hz"]) if pitch_core else sample_rate
        loop = None if decoded["loop_start_sample"] is None else (decoded["loop_start_sample"], decoded["loop_end_sample"])
        wav = pcm_wav(decoded["samples"], rate, loop)
        evidence = {"schema": SCHEMA, "game": "gt4", "bank_id": bank_id, "source": str(path),
                    "bank_sha256": report["sha256"], "selection": e, "sample_rate_hz": rate,
                    "native_pitch_evidence": report["native_pitch_evidence"], "wav_sha256": sha256(wav),
                    "authentic_effect_identity": None, "rate_provenance": "supplied CORE anchor pitch" if pitch_core else "explicit caller-selected nominal Hz",
                    "boundary": "Individual source recording only; no complete original GT4 mix."}
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream: stream.write(wav)
        save_json(output.with_suffix(".json"), evidence, (Path(root).parent,))
        return evidence
    if pitch_core or sample_rate is None or entry_id is None:
        raise ValueError("INST requires explicit entry_id and nominal sample_rate")
    report = inspect_gt4(root, bank_id)
    entries = [e for e in report["entries"] if e["entry_id"] == str(entry_id)]
    if len(entries) != 1:
        raise ValueError("entry ID absent")
    e = entries[0]
    return extract_instrument(path, output, e["kind"], e["program"], e["split"], sample_rate)


def event_mapping(game, root=None, volume=None, core=None):
    if game == "gt3":
        if volume is None or core is None:
            raise ValueError("GT3 event routing requires explicit --gt3-volume and --gt3-core")
        from gt3_sound_lab import native_event_mapping
        return native_event_mapping(volume, core)
    if root is None:
        raise ValueError("GT4 event routing requires --gt4-root")
    sound_dir = Path(root) / "sound_gt/sound"
    raw = read_bounded(sound_dir / "se.inf")
    rows = events(raw)
    banks = {i: inspect_instrument(read_bounded(sound_dir / name)) for i, name in
             enumerate(("gt4sys.ins", "gt4race.ins", "gt4count.ins", "gt4race2.ins"))}
    return {"game": "gt4", "schema": SCHEMA, "source": file_identity(sound_dir / "se.inf"),
            "events": resolve_events(banks, {e["name"]: int(e["token"], 16) for e in rows}),
            "boundary": "Supplied CORE static interpretation; exact GT4 build pairing and runtime pitch/mix unconfirmed."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gt4-root", type=Path)
    parser.add_argument("--gt3-volume", type=Path)
    parser.add_argument("--gt3-core", type=Path, help="original CORE.GT3, required for qualified named-event routing")
    parser.add_argument("--pitch-core", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("catalog", "inventory", "vehicle", "inspect", "export", "compare", "events", "event-export"):
        p = sub.add_parser(name)
        p.add_argument("--game", choices=("gt3", "gt4"), required=True)
        p.add_argument("--output", type=Path, required=True)
        if name == "vehicle": p.add_argument("--vehicle", required=True)
        if name in ("inspect", "export", "compare"): p.add_argument("--bank", required=True)
        if name == "compare": p.add_argument("--other-bank", required=True)
        if name == "export":
            p.add_argument("--entry"); p.add_argument("--sample-rate", type=int)
        if name == "event-export":
            p.add_argument("--event", required=True); p.add_argument("--sample-rate", type=int)
            p.add_argument("--lane", choices=("primary", "secondary"), default="primary")
    p = sub.add_parser("serve")
    p.add_argument("--output", type=Path, default=ROOT / "scratch/gt_sound_lab/browser")
    p.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    if args.command == "serve":
        from gt_sound_lab_server import serve
        serve(args); return
    roots = [p for p in (args.gt4_root.parent if args.gt4_root else None, args.gt3_volume.parent if args.gt3_volume else None) if p]
    if args.command in ("events", "event-export"):
        result = event_mapping(args.game, args.gt4_root, args.gt3_volume, args.gt3_core)
        if args.command == "events":
            save_json(args.output, result, roots)
        elif args.game == "gt3":
            if args.sample_rate is not None:
                parser.error("GT3 event-export uses its qualified native leaf pitch; omit --sample-rate")
            from gt3_sound_lab import export_event
            export_event(args.gt3_volume, args.gt3_core, args.event, private_output(args.output, roots), args.lane)
        else:
            matches = [e for e in result["events"] if e["name"] == args.event]
            if len(matches) != 1 or matches[0]["status"] != "STATIC_DIRECT_FIRST_SPLIT" or args.sample_rate is None:
                raise ValueError("one resolved GT4 direct event and explicit nominal --sample-rate required")
            e = matches[0]; selection = e["selection"]
            bank_id = "sound_gt/sound/" + e["bank_name"]
            output = private_output(args.output, roots)
            evidence = extract_instrument(gt4_bank(args.gt4_root, bank_id), output, selection["kind"], selection["program"], selection["split"], args.sample_rate)
            evidence["static_native_event"] = e
            # Preserve the explicit event resolution alongside its sample metadata.
            output.with_suffix(".json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PRIVATE_EVENT_RESULT", "output": str(args.output)})); return
    if args.game == "gt4":
        if args.gt4_root is None: parser.error("--gt4-root required")
        if args.command == "export":
            result = export_gt4(args.gt4_root, args.bank, args.output, args.sample_rate, args.pitch_core, args.entry)
            print(json.dumps({"status": "PRIVATE_AUDITION_EXPORTED", "output": str(args.output)})); return
        if args.command == "catalog": result = gt4_catalog(args.gt4_root)
        elif args.command == "inventory": result = gt4_inventory(args.gt4_root, args.pitch_core)
        elif args.command == "vehicle": result = select_vehicle(gt4_catalog(args.gt4_root), args.vehicle)
        elif args.command == "inspect": result = inspect_gt4(args.gt4_root, args.bank, args.pitch_core)
        else: result = compare_banks(inspect_gt4(args.gt4_root, args.bank), inspect_gt4(args.gt4_root, args.other_bank))
    else:
        if args.gt3_volume is None: parser.error("--gt3-volume required")
        from gt3_sound_lab import catalog, inspect_member, export_member
        if args.command == "export":
            export_member(args.gt3_volume, args.bank, args.entry, private_output(args.output, roots), args.sample_rate)
            print("PRIVATE_GT3_AUDITION_EXPORTED"); return
        if args.command in ("catalog", "inventory"): result = normalize_gt3(catalog(args.gt3_volume, include_banks=args.command == "inventory"))
        elif args.command == "vehicle": result = select_vehicle(normalize_gt3(catalog(args.gt3_volume, include_banks=False)), args.vehicle)
        elif args.command == "inspect": result = inspect_member(args.gt3_volume, args.bank)
        else: result = compare_banks(inspect_member(args.gt3_volume, args.bank), inspect_member(args.gt3_volume, args.other_bank))
    save_json(args.output, result, roots)
    print(json.dumps({"schema": SCHEMA, "output": str(args.output), "counts": result.get("counts")}))


if __name__ == "__main__":
    main()
