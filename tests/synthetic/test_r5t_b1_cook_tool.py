from __future__ import annotations

import sys
import json
import struct
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src", ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import r5t_b1_course_cook as cook_tool


class R5TB1CookToolTests(unittest.TestCase):
    @staticmethod
    def _write_startpoint_source(folder: Path) -> None:
        folder.mkdir(parents=True)
        txt = b"moModel(Name [Model])\n  moMesh(Name [startpoint] Index 0 Size 12)\n"
        table = struct.pack("<H", 5) + b"Model" + struct.pack("<BBHIIH", 1, 1, 0, 0, 12, 10) + b"startpoint"
        points = struct.pack(
            "<24f",
            0, 0, 0, 10, 0, 0, 0, 10, 0, 10, 10, 0,
            0, 0, 10, 10, 0, 10, 0, 10, 10, 10, 10, 10,
        )
        header = struct.pack("<8I", 1, 0, 1, 1, 36, 0, 12, 8)
        gxm = header + bytes(16) + bytes(36 * 4) + points + table
        (folder / "Model.gxm").write_bytes(gxm)
        (folder / "Model.txt").write_bytes(txt)

    def test_course_target_rejects_absolute_drive_and_parent_paths(self):
        for value in ("../outside", "DataGx/../../outside", "C:/outside", "\\\\server\\share"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                cook_tool._safe_relative(value, "course target")
        self.assertEqual(
            cook_tool._safe_relative("DataGx\\Course\\France1", "course target"),
            Path("DataGx", "Course", "France1"),
        )

    def test_prepare_and_reset_modify_only_the_isolated_copy_and_generated_caches(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            output_root = temp_root / "out"
            runtime_source = temp_root / "runtime-source"
            source_course = temp_root / "source-course"
            course_target = runtime_source / "DataGx" / "Course" / "France1"
            course_target.mkdir(parents=True)
            source_course.mkdir()
            (runtime_source / "MRallye.exe").write_bytes(b"synthetic-runtime")
            (course_target / "retail.dx").write_bytes(b"original-runtime-dx")
            (course_target / "keep.bin").write_bytes(b"keep")
            (source_course / "france1.gxm").write_bytes(b"synthetic-gxm")
            (source_course / "france1.txt").write_bytes(b"synthetic-txt")
            (source_course / "old.dx").write_bytes(b"generated-dx")
            (source_course / "old.dxt").write_bytes(b"generated-dxt")

            args = Namespace(
                experiment="synthetic",
                cohort="baseline",
                runtime_source=runtime_source,
                source_course=source_course,
                course_target="DataGx/Course/France1",
            )
            with patch.object(cook_tool, "WORK_ROOT", output_root):
                prepared = cook_tool.prepare(args)
                staged = output_root / "experiments" / "synthetic" / "baseline" / "runtime"
                staged_course = staged / "DataGx" / "Course" / "France1"
                self.assertEqual(prepared["removed_cache_files"], 3)
                self.assertTrue((staged_course / "france1.gxm").is_file())
                self.assertFalse((staged_course / "old.dx").exists())
                self.assertFalse((staged_course / "old.dxt").exists())
                self.assertTrue((course_target / "retail.dx").is_file())

                (staged_course / "cooked.dx").write_bytes(b"new-dx")
                (staged_course / "cooked.dxt").write_bytes(b"new-dxt")
                (staged_course / "keep.bin").write_bytes(b"changed in clone")
                reset_args = Namespace(
                    experiment="synthetic",
                    cohort="baseline",
                    runtime_root=None,
                    course_target="DataGx/Course/France1",
                )
                result = cook_tool.reset(reset_args)
                self.assertEqual(set(result["removed_generated_cache_files"]), {"cooked.dx", "cooked.dxt"})
                self.assertTrue((staged_course / "keep.bin").is_file())
                self.assertEqual((course_target / "keep.bin").read_bytes(), b"keep")

    def test_snapshot_records_source_inputs_and_all_course_resource_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            output_root = Path(temp) / "output"
            runtime = output_root / "experiments" / "snapshot" / "baseline" / "runtime"
            course = runtime / "DataGx" / "Course" / "France1"
            course.mkdir(parents=True)
            inputs = {
                "france1.gxm": b"source-gxm",
                "France1.txt": b"source-txt",
                "foliage.gxi": b"source-gxi",
                "france1.dx": b"cooked-dx",
                "foliage.dxt": b"cooked-dxt",
                "extra.bin": b"opaque-resource",
            }
            for name, data in inputs.items():
                (course / name).write_bytes(data)
            args = Namespace(
                experiment="snapshot",
                cohort="baseline",
                run_id="baseline-01",
                runtime_root=None,
                course_target="DataGx/Course/France1",
                log=None,
            )
            with patch.object(cook_tool, "WORK_ROOT", output_root):
                result = cook_tool.snapshot(args)
            run_root = Path(result["run_root"])
            metadata = json.loads((run_root / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(result["course_file_count"], len(inputs))
            self.assertEqual(
                {Path(item["path"]).name.casefold() for item in metadata["input_manifest"].values()},
                {"france1.gxm", "france1.txt", "foliage.gxi"},
            )
            self.assertEqual(len(metadata["resource_manifest"]), len(inputs))
            for name, data in inputs.items():
                self.assertEqual((run_root / "course" / name).read_bytes(), data)

    def test_startpoint_patch_copies_source_and_changes_one_expected_float(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            source = temp_root / "source"
            self._write_startpoint_source(source)
            original = (source / "Model.gxm").read_bytes()
            args = Namespace(
                experiment="point-edit",
                source_course=source,
                point_index=0,
                axis="x",
                expected=0.0,
                replacement=1.0,
            )
            with patch.object(cook_tool, "WORK_ROOT", temp_root / "out"):
                result = cook_tool.patch_startpoint(args)
                modified = Path(result["modified_source_course"]) / "Model.gxm"
                modified_data = modified.read_bytes()
                self.assertEqual((source / "Model.gxm").read_bytes(), original)
                changed = [index for index, (a, b) in enumerate(zip(original, modified_data)) if a != b]
                patch_bytes = range(result["patch"]["byte_offset"], result["patch"]["byte_offset"] + 4)
                self.assertTrue(changed)
                self.assertTrue(set(changed).issubset(set(patch_bytes)))
                self.assertEqual(struct.unpack_from("<f", modified_data, result["patch"]["byte_offset"])[0], 1.0)
                self.assertEqual((Path(result["modified_source_course"]) / "Model.txt").read_bytes(), (source / "Model.txt").read_bytes())

    def test_recorded_patch_input_validation_allows_only_the_expected_gxm_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            experiment = root / "experiment"
            experiment.mkdir()
            (experiment / "source-patch.json").write_text(json.dumps({
                "gxm_name": "France1.gxm",
                "gxm_sha256_before": "original-gxm",
                "gxm_sha256_after": "modified-gxm",
            }), encoding="utf-8")
            groups = {"baseline": [], "modified": []}
            for cohort, gxm_hash in (("baseline", "original-gxm"), ("modified", "modified-gxm")):
                for index in range(1, 4):
                    course = root / cohort / f"run-{index}" / "course"
                    course.mkdir(parents=True)
                    manifest = {
                        "france1.gxm": {"path": "France1.gxm", "bytes": 4, "sha256": gxm_hash},
                        "France1.txt": {"path": "France1.txt", "bytes": 4, "sha256": "same-txt"},
                    }
                    (course.parent / "run.json").write_text(json.dumps({"input_manifest": manifest}), encoding="utf-8")
                    groups[cohort].append(course)
            result = cook_tool.validate_source_patch_inputs(experiment, groups["baseline"], groups["modified"])
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["only_cross_cohort_input_change"], "france1.gxm")


if __name__ == "__main__":
    unittest.main()
