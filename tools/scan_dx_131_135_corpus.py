#!/usr/bin/env python3
"""Regenerate DX 131 -> 135 corpus coverage from an ignored input directory."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from master_rallye.dx_corpus import scan_dx_corpus, write_corpus_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan vehicle DX inputs and regenerate deterministic revision 131/135 coverage reports."
    )
    parser.add_argument(
        "input_root",
        type=Path,
        help="ignored DX/GXM corpus directory, normally inputs/",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        type=Path,
        default=Path("research/r-cooker2/corpus-coverage.json"),
        help="JSON output path (default: research/r-cooker2/corpus-coverage.json)",
    )
    parser.add_argument(
        "--markdown",
        dest="markdown_path",
        type=Path,
        default=Path("research/r-cooker2/corpus-coverage.md"),
        help="Markdown output path (default: research/r-cooker2/corpus-coverage.md)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = scan_dx_corpus(args.input_root, repository_root=REPOSITORY_ROOT)
        write_corpus_reports(report, args.json_path, args.markdown_path)
    except (OSError, ValueError) as exc:
        print(f"Corpus scan failed: {exc}", file=sys.stderr)
        return 2

    summary = report["summary"]
    pairs = report["pairing_summary"]
    conversion = report["conversion_regression"]
    existing = report["existing_rev135_validation"]
    unexpected = report["official_rev135_comparison"]["additional_or_unresolved_differences"]
    hard_failures = (
        conversion["rejected"] > 0
        or existing["rejected"]
        or pairs["formula_mismatches"] > 0
        or pairs["unresolved_direct_pairs"] > 0
        or unexpected
        or summary["unrecognized_or_invalid_dx_files"] > 0
    )
    print(
        "DX corpus scan: "
        f"{summary['dx_file_instances']} file instances, "
        f"{summary['unique_dx_payloads']} unique payloads; "
        f"{conversion['converted']}/{conversion['unique_rev131_payloads_attempted']} unique rev131 payloads converted; "
        f"{pairs['verified_same_source_pairs']} verified same-source pairs, "
        f"{pairs['formula_matches']}/{pairs['draw_records_checked']} direct draw prefixes matched."
    )
    print(f"JSON: {args.json_path}")
    print(f"Markdown: {args.markdown_path}")
    if hard_failures:
        print(
            "Corpus scan found conversion, parser, prefix-oracle, or pair-comparison failures; "
            "inspect the generated reports.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
