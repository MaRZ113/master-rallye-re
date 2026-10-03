from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "tools" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from broker_observatory import (  # noqa: E402
    ObservatoryError,
    diff_snapshots,
    main,
    parse_dump_bytes,
)


def row(
    path: str,
    value: str,
    *,
    type_name: str = "Int",
    scope: str = "GLOBAL",
    revision: int = 0,
    save_file: str = "Game",
    s: bool = False,
    o: bool = False,
    ps: bool = False,
    continuation: tuple[str, ...] = (),
) -> list[str]:
    first = (
        f"[Rev={revision}] [ID={scope}] [Save: S={'T' if s else 'F'}, O={'T' if o else 'F'}, "
        f"PS={'T' if ps else 'F'}] [SaveFile={save_file}] "
        f"{path:<20} ({type_name})    = {value}"
    )
    return [first, *continuation]


def dump(rows: list[list[str]], filenames: tuple[str, ...] = ("Game", "Vehicles")) -> bytes:
    counts = {"GLOBAL": 0, "SCENE": 0, "USER": 0}
    for lines in rows:
        prefix = lines[0]
        scope = prefix.split("[ID=", 1)[1].split("]", 1)[0]
        counts[scope if scope in counts else "USER"] += 1
    total = len(rows)
    lines = [f"enBroker(Size {total} Capacity {max(total, 8)})", "{"]
    for entry_lines in rows:
        lines.extend(entry_lines)
    lines.extend(
        [
            f"NUM BROKER ENTRIES: GLOBAL [{counts['GLOBAL']}]",
            f"NUM BROKER ENTRIES: SCENE  [{counts['SCENE']}]",
            f"NUM BROKER ENTRIES: USER    [{counts['USER']}]",
            f"NUM BROKER ENTRIES: TOTAL   [{total}]",
            "}",
            f"enBroker FilenamesList Num entries ={len(filenames)}",
            "{",
            *filenames,
            "}",
        ]
    )
    return ("\n".join(lines) + "\n").encode("cp1252")


def parse_rows(rows: list[list[str]], filenames: tuple[str, ...] = ("Game", "Vehicles")) -> dict:
    return parse_dump_bytes(dump(rows, filenames))


class BrokerDumpParserTests(unittest.TestCase):
    def test_typed_rows_flags_and_filenames_are_preserved(self):
        fixture = dump(
            [
                row("Race/Car0/Count", "4", type_name="Int", s=True, o=True, ps=True),
                row("Race/Car0/Speed", "-1.92", type_name="Float", scope="SCENE", save_file="__NO_SAVE"),
                row("Game/LargeFloat", "1.25e+30", type_name="Float"),
                row("Hud/Hud0/Name", '"needle with spaces"', type_name="String", continuation=("  nested detail",)),
                row("Input/Vec2", "1.00 / -2.00", type_name="nuVector2"),
                row("Input/Vec3", "1.00 / 2.00 / 3.00", type_name="nuVector3"),
                row("Input/Vec4", "1.00 / 2.00 / 3.00 / 4.00", type_name="nuVector4"),
                row("Drivers/Driver7/Mode", "2", type_name="Int", scope="USER 7", save_file="Dev"),
            ],
            ("Game", "Dev", "Vehicles", "__NO_SAVE"),
        )
        parsed = parse_dump_bytes(fixture, {"capture_kind": "synthetic"})
        self.assertEqual(parsed["dump"]["reported_scope_counts"], {"GLOBAL": 6, "SCENE": 1, "USER": 1, "TOTAL": 8})
        self.assertEqual(parsed["dump"]["filenames"], ["Game", "Dev", "Vehicles", "__NO_SAVE"])
        self.assertEqual(parsed["dump"]["special_labels_observed"], ["__NO_SAVE"])
        first = parsed["entries"][0]
        self.assertEqual(first["path"], "Race/Car0/Count")
        self.assertEqual(first["broker_id"], "GLOBAL")
        self.assertTrue(first["save_game"])
        self.assertTrue(first["save_options"])
        self.assertTrue(first["save_player_state"])
        self.assertEqual(first["save_flags"], {"S": True, "O": True, "PS": True})
        self.assertEqual(parsed["entries"][1]["save_file"], "__NO_SAVE")
        self.assertEqual(parsed["entries"][1]["value"], -1.92)
        self.assertEqual(parsed["entries"][1]["value_raw"], "-1.92")
        self.assertEqual(parsed["entries"][2]["value"], 1.25e30)
        self.assertEqual(parsed["entries"][3]["value"], "needle with spaces")
        self.assertEqual(parsed["entries"][3]["value_raw"], '"needle with spaces"')
        self.assertEqual(parsed["entries"][3]["continuation_lines"], ["  nested detail"])
        self.assertEqual([entry["type"] for entry in parsed["entries"][4:7]], ["nuVector2", "nuVector3", "nuVector4"])
        self.assertEqual(parsed["entries"][4]["value"], [1.0, -2.0])
        self.assertEqual(parsed["entries"][7]["scope_label"], "USER")
        self.assertEqual(parsed["entries"][7]["broker_id"], "USER 7")
        self.assertEqual(parsed["source"]["raw_sha256"], __import__("hashlib").sha256(fixture).hexdigest())

    def test_duplicate_paths_are_retained_and_occurrence_numbered(self):
        parsed = parse_rows(
            [
                row("Race/Shared/Value", "1"),
                row("Race/Shared/Value", "2"),
                row("Race/Shared/Value", "3", scope="SCENE"),
            ]
        )
        self.assertEqual(len(parsed["entries"]), 3)
        self.assertEqual(
            [(e["scope_label"], e["occurrence"]) for e in parsed["entries"]],
            [("GLOBAL", 0), ("GLOBAL", 1), ("SCENE", 0)],
        )

    def test_whitespace_variation_and_bracketed_path(self):
        raw = dump([row("Race/Car[0]/Value", "1.25", type_name="Float")], ("Game",))
        raw = raw.replace(
            b"[Rev=0] [ID=GLOBAL] [Save: S=F, O=F, PS=F] [SaveFile=Game] ",
            b"[Rev=0]   [ID=GLOBAL] [Save:  S=F ,  O=F, PS=F]   [SaveFile=Game]  ",
        )
        parsed = parse_dump_bytes(raw)
        self.assertEqual(parsed["entries"][0]["path"], "Race/Car[0]/Value")
        self.assertEqual(parsed["entries"][0]["value"], 1.25)

    def test_matrix_and_string_list_continuation_lines_are_kept(self):
        parsed = parse_rows(
            [
                row(
                    "Camera/Matrix",
                    "row0",
                    type_name="Matrix",
                    continuation=(
                        "  1.00 / 2.00 / 3.00 / 4.00",
                        "  5.00 / 6.00 / 7.00 / 8.00",
                        "  9.00 / 10.00 / 11.00 / 12.00",
                        "  13.00 / 14.00 / 15.00 / 16.00",
                    ),
                ),
                row("Frontend/Tags", "", type_name="StringList", continuation=("{", "  A", "  B", "}")),
                row("Vehicles/Car0/Data", "unspecified", type_name="xmlData", continuation=("  class data",)),
            ]
        )
        self.assertEqual(parsed["entries"][0]["continuation_lines"][0], "  1.00 / 2.00 / 3.00 / 4.00")
        self.assertEqual(parsed["entries"][0]["value"], [float(i) for i in range(1, 17)])
        self.assertEqual(parsed["entries"][1]["continuation_lines"], ["{", "  A", "  B", "}"])
        self.assertEqual(parsed["entries"][1]["value"], ["A", "B"])
        self.assertEqual(parsed["entries"][2]["type"], "xmlData")

    def test_latest_complete_block_wins_and_incomplete_newer_block_is_reported(self):
        old = dump([row("Race/State", "1")], ("Game",))
        incomplete = b"enBroker(Size 1 Capacity 8)\n{\n[Rev=0] [ID=GLOBAL] [Save: S=F, O=F, PS=F] [SaveFile=Game] Race/State (Int) = 2\n"
        parsed = parse_dump_bytes(old + incomplete)
        self.assertEqual(parsed["entries"][0]["value"], 1)
        self.assertEqual(parsed["diagnostics"]["complete_dump_candidates"], 1)
        self.assertEqual(parsed["diagnostics"]["incomplete_candidates"][-1]["reason"], "one or more broker scope totals are absent")
        malformed_newer = dump([row("Race/State", "2")], ("Game",)).replace(b"[Rev=0]", b"[Rev=bad]")
        parsed_with_malformed = parse_dump_bytes(old + malformed_newer)
        self.assertEqual(len(parsed_with_malformed["diagnostics"]["malformed_lines"]), 1)

    def test_nul_terminator_is_counted_but_not_parsed_as_a_line(self):
        raw = dump([row("Input/Selected", "3")], ("Input",)) + b"\x00"
        parsed = parse_dump_bytes(raw)
        self.assertEqual(parsed["source"]["raw_nul_suffix_bytes"], 1)
        self.assertEqual(parsed["source"]["raw_byte_length"], len(raw))

    def test_no_complete_block_or_unknown_row_fails_closed(self):
        with self.assertRaisesRegex(ObservatoryError, "No complete Broker Dump block"):
            parse_dump_bytes(b"no broker output\n")
        unknown = dump([row("Race/Unknown", "x", type_name="NewType")], ("Game",))
        with self.assertRaisesRegex(ObservatoryError, "malformed/unknown entry"):
            parse_dump_bytes(unknown)
        malformed = dump([row("Game/Mode", "2")], ("Game",)).replace(
            b"[Rev=0]", b"[Rev=bad]"
        )
        with self.assertRaisesRegex(ObservatoryError, "entry-like row failed header parse"):
            parse_dump_bytes(malformed)

    def test_cli_parse_writes_machine_readable_snapshot(self):
        raw = dump([row("Game/Mode", "2")], ("Game",))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "debug.bin"
            output = root / "snapshot.json"
            source.write_bytes(raw)
            self.assertEqual(main(["parse", str(source), "--label", "frontend", "--output", str(output)]), 0)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["entries"][0]["path"], "Game/Mode")
            self.assertEqual(result["source"]["label"], "frontend")

    def test_snapshot_schema_is_valid_json_and_matches_parser_keys(self):
        schema_path = ROOT / "research" / "general-re" / "broker-observatory" / "broker-snapshot.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        parsed = parse_rows([row("Game/Mode", "2")])
        self.assertEqual(schema["properties"]["kind"]["const"], parsed["kind"])
        self.assertEqual(set(schema["required"]), set(parsed) - {"tool_version"})
        self.assertNotIn("tool_version", schema["required"])
        self.assertEqual(schema["properties"]["tool_version"]["type"], "string")
        self.assertEqual(set(schema["properties"]["entries"]["items"]["required"]), set(parsed["entries"][0]))


class BrokerSnapshotDiffTests(unittest.TestCase):
    def test_all_supported_change_categories_are_reported(self):
        before = parse_rows(
            [
                row("P/value", "1.00", type_name="Float"),
                row("P/type", "4", type_name="Int"),
                row("P/revision", "8", revision=0),
                row("P/scope", '"x"', type_name="String", scope="GLOBAL"),
                row("P/mask", "True", type_name="Bool"),
                row("P/file", '"x"', type_name="String", save_file="Game"),
                row("P/remove", "1"),
            ]
        )
        after = parse_rows(
            [
                row("P/value", "2.00", type_name="Float"),
                row("P/type", "5", type_name="Float"),
                row("P/revision", "8", revision=1),
                row("P/scope", '"x"', type_name="String", scope="SCENE"),
                row("P/mask", "True", type_name="Bool", o=True),
                row("P/file", '"x"', type_name="String", save_file="Vehicles"),
                row("P/add", "3"),
            ]
        )
        result = diff_snapshots(before, after)
        changed = {kind for event in result["events"] if event["kind"] == "CHANGED" for kind in event["changes"]}
        self.assertEqual(
            changed,
            {"VALUE_CHANGED", "TYPE_CHANGED", "REVISION_CHANGED", "BROKER_ID_CHANGED", "SCOPE_CHANGED", "SAVE_MASK_CHANGED", "SAVE_FILE_CHANGED"},
        )
        self.assertIn("ADDED", {event["kind"] for event in result["events"]})
        self.assertIn("REMOVED", {event["kind"] for event in result["events"]})
        type_event = next(event for event in result["events"] if event.get("path") == "P/type")
        self.assertEqual(set(type_event["changes"]), {"TYPE_CHANGED", "VALUE_CHANGED"})

    def test_scope_move_pairs_only_when_unique_by_path_occurrence(self):
        before = parse_rows([row("Race/State", "1", scope="GLOBAL")])
        after = parse_rows([row("Race/State", "1", scope="SCENE")])
        result = diff_snapshots(before, after)
        event = next(item for item in result["events"] if item["kind"] == "CHANGED")
        self.assertEqual(
            event["changes"],
            {
                "BROKER_ID_CHANGED": {"before": "GLOBAL", "after": "SCENE"},
                "SCOPE_CHANGED": {"before": "GLOBAL", "after": "SCENE"},
            },
        )
        self.assertEqual(event["pairing"], "unique-path-occurrence-fallback")

    def test_ambiguous_duplicate_scope_moves_remain_remove_and_add(self):
        before = parse_rows([row("Race/State", "1", scope="GLOBAL"), row("Race/State", "2", scope="SCENE")])
        after = parse_rows([row("Race/State", "1", scope="USER 1"), row("Race/State", "2", scope="USER 2")])
        result = diff_snapshots(before, after)
        self.assertFalse(any(item["kind"] == "CHANGED" for item in result["events"]))
        self.assertEqual(sum(item["kind"] == "REMOVED" for item in result["events"]), 2)
        self.assertEqual(sum(item["kind"] == "ADDED" for item in result["events"]), 2)

    def test_float_tolerance_and_prefix_filter(self):
        before = parse_rows([row("Vehicles/Car0/Radius", "1.00", type_name="Float"), row("Race/Time", "1.00", type_name="Float")])
        after = parse_rows([row("Vehicles/Car0/Radius", "1.01", type_name="Float"), row("Race/Time", "2.00", type_name="Float")])
        result = diff_snapshots(before, after, prefixes=("Vehicles/",), float_tolerance=0.02)
        self.assertEqual(result["events"], [])
        self.assertEqual(result["filters"]["path_prefixes"], ["Vehicles/"])

    def test_label_is_metadata_only_and_non_entry_lines_are_reported(self):
        raw = b"debug startup message\n" + dump([row("Game/Mode", "2")], ("Game",)) + b"tail message\n"
        parsed = parse_dump_bytes(raw, {"label": "frontend"})
        self.assertEqual(parsed["source"]["label"], "frontend")
        self.assertEqual(parsed["diagnostics"]["ignored_non_entry_line_count"], 2)
        self.assertEqual(parsed["diagnostics"]["malformed_lines"], [])

    def test_duplicate_paths_do_not_collapse_in_diff(self):
        before = parse_rows([row("Race/Duplicate", "1"), row("Race/Duplicate", "2")])
        after = parse_rows([row("Race/Duplicate", "1")])
        result = diff_snapshots(before, after)
        removed = [item for item in result["events"] if item["kind"] == "REMOVED"]
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]["entry"]["occurrence"], 1)

    def test_cli_json_and_csv_outputs(self):
        before = parse_rows([row("Game/Mode", "1")])
        after = parse_rows([row("Game/Mode", "2"), row("Game/New", "3")])
        before["source"]["label"] = "frontend"
        after["source"]["label"] = "race"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_path, new_path = root / "old.json", root / "new.json"
            json_path, csv_path = root / "diff.json", root / "diff.csv"
            old_path.write_text(json.dumps(before), encoding="utf-8")
            new_path.write_text(json.dumps(after), encoding="utf-8")
            self.assertEqual(main(["diff", str(old_path), str(new_path), "--format", "json", "--output", str(json_path)]), 0)
            self.assertEqual(main(["diff", str(old_path), str(new_path), "--format", "csv", "--output", str(csv_path)]), 0)
            structured = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(len(structured["events"]), 2)
            self.assertEqual(structured["before_label"], "frontend")
            with csv_path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 2)


if __name__ == "__main__":
    unittest.main()
