"""Copy isolated Italy1 retail-resource overlays into ignored research output."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=REPO_ROOT.parent / "corpora")
    parser.add_argument("--inventory", type=Path, default=REPO_ROOT / "research" / "r5t_a" / "course-corpus.json")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / ".research-output" / "r5t_a" / "compatibility")
    args = parser.parse_args()

    corpus_root = args.corpus_root.resolve()
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    retail = next(build for build in inventory["builds"] if build["key"] == "retail")
    italy1 = next(course for course in retail["courses"] if course["normalized_course_key"] == "italy1")

    candidates: list[tuple[str, str, str]] = []
    dx = italy1["artifacts"].get(".dx", [])
    txt = italy1["race_test_xml"]
    sfl = [item for item in italy1["spatial_fields"] if item["path"].casefold().endswith(".sfl")]
    if len(dx) != 1 or len(txt) != 1 or len(sfl) != 1:
        raise SystemExit("inventory does not contain one exact Italy1 DX, RaceTest XML, and SFL")
    candidates.extend([
        ("01-retail-dx-only", dx[0]["path"], "compiled course DX compatibility"),
        ("02-retail-sfl-only", sfl[0]["path"], "SFL payload compatibility"),
        ("03-retail-xml-only", txt[0]["path"], "RaceTest scene compatibility"),
    ])

    data_root = corpus_root / "retail" / "Data.sma_unpacked"
    output_root = args.output_dir.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "r5t-a-compatibility-overlays-v1",
        "target_runtime": "Demo 9.3.1",
        "track": "Italy1",
        "read_only_sources": True,
        "source_data_root_label": "corpora/retail/Data.sma_unpacked",
        "overlays": [],
    }
    for name, relative, purpose in candidates:
        source = data_root / Path(relative)
        if not source.is_file():
            raise SystemExit(f"missing source resource: {source}")
        destination = output_root / name / "overlay" / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        source_hash = sha256(source)
        copied_hash = sha256(destination)
        if source_hash != copied_hash:
            raise SystemExit(f"copy hash mismatch for {relative}")
        manifest["overlays"].append({
            "name": name,
            "purpose": purpose,
            "runtime_relative_path": Path(relative).as_posix(),
            "source_relative_path": Path(relative).as_posix(),
            "size_bytes": source.stat().st_size,
            "sha256": source_hash,
            "overlay_file": destination.relative_to(output_root).as_posix(),
        })
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"output_dir": str(output_root), "overlays": len(candidates), "manifest": str(output_root / "manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
