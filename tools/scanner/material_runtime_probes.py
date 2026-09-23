"""Generate isolated same-size DXT runtime probes; never edit the source corpus."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from master_rallye.dxt import (
    PNG_ROWS_PRESERVE_STORED, decode_rgba_pixels, encode_dxt_pixels,
    parse_dxt, parse_dxt_bytes,
)

PROBES = {
    "M1_body_helper": ("whitepaint-tga.dxt", ("white", "black", "gray")),
    "M2_windscreen_alpha": ("windscreen32-tga.dxt", ("alpha255", "alpha128", "alpha0")),
    "M3_envmap": ("chrome-tga.dxt", ("asymmetric",)),
    "M4_brake_glow": ("breaklightsonglow-tga.dxt", ("alpha255", "alpha128", "alpha0")),
}


def variant_pixels(template, name: str) -> bytes:
    data = bytearray(decode_rgba_pixels(template, PNG_ROWS_PRESERVE_STORED))
    for y in range(template.height):
        for x in range(template.width):
            i = (y * template.width + x) * 4
            if name in ("white", "black", "gray"):
                value = {"white": 255, "black": 0, "gray": 128}[name]
                data[i:i + 3] = bytes((value, value, value))
            elif name.startswith("alpha"):
                data[i + 3] = int(name[5:])
            elif name == "asymmetric":
                # Four distinct blocks plus unequal red and white corner markers.
                palette = ((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0))
                color = palette[(2 if y >= template.height // 2 else 0)
                                + (1 if x >= template.width // 2 else 0)]
                if x < template.width // 8 and y < template.height // 4:
                    color = (255, 255, 255)
                data[i:i + 3] = bytes(color)
            else:
                raise ValueError(name)
    return bytes(data)


def main(root: Path, output: Path) -> None:
    source_dir = root / "Astero"
    if not source_dir.is_dir():
        raise SystemExit(f"missing Astero source directory: {source_dir}")
    output = output.resolve()
    source_dir = source_dir.resolve()
    source_root = root.resolve()
    if ".research-output" not in output.parts:
        raise SystemExit("output must be inside an ignored .research-output directory")
    if output == source_root or source_root in output.parents:
        raise SystemExit("output must not be inside the original game asset directory")
    for test, (filename, variants) in PROBES.items():
        source = source_dir / filename
        template = parse_dxt(source)
        original = source.read_bytes()
        folder = output / test
        rows = []
        for variant in variants:
            rgba = variant_pixels(template, variant)
            encoded = encode_dxt_pixels(
                template, rgba, template.width, template.height,
                row_policy=PNG_ROWS_PRESERVE_STORED,
            )
            decoded = parse_dxt_bytes(encoded)
            assert encoded[:20] == original[:20]
            assert (decoded.width, decoded.height) == (template.width, template.height)
            assert len(encoded) == len(original)
            assert decoded.bgra != template.bgra
            if test in ("M2_windscreen_alpha", "M4_brake_glow"):
                assert decoded.bgra[:3] == template.bgra[:3]
                assert all(decoded.bgra[i:i + 3] == template.bgra[i:i + 3]
                           for i in range(0, len(decoded.bgra), 4))
            target = folder / variant / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(encoded)
            rows.append({
                "variant": variant, "relative_candidate": f"{variant}/{filename}",
                "sha256": hashlib.sha256(encoded).hexdigest(),
                "same_dimensions": True, "same_header": True,
                "same_length": True,
                "rgb_preserved": test in ("M2_windscreen_alpha", "M4_brake_glow"),
            })
        validation = {
            "test": test,
            "source_resource": "Astero/car.dx",
            "source_texture": f"Astero/{filename}",
            "source_sha256": hashlib.sha256(original).hexdigest(),
            "dimensions": [template.width, template.height],
            "source_bytes_untouched": source.read_bytes() == original,
            "candidates": rows,
            "runtime_tested": False,
        }
        (folder / "validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
        instructions = {
            "M1_body_helper": "Compare body panels in fixed lighting. Vary only whitepaint slot 1; keep slot 0 and DX unchanged. Record color, brightness, reflection, masking, and unchanged regions.",
            "M2_windscreen_alpha": "Compare windscreen in fixed camera and lighting. Vary only slot 0 alpha while RGB and DX stay unchanged. Record transparency, threshold, sorting/Z artifacts, and reflections.",
            "M3_envmap": "Rotate camera and vehicle around chromebar/wheel. Vary only chrome slot 1. Record whether pattern follows UVs, camera, or reflection direction; include multiple angles.",
            "M4_brake_glow": "Compare the brake/glow-like draw (Astero/car.dx draw 30). Vary only slot 0 alpha while RGB and DX stay unchanged. Record blend response with brakes off/on and compare against M2.",
        }[test]
        (folder / "TEST_INSTRUCTIONS.txt").write_text(
            f"{test}\nTarget: Astero/car.dx, {filename}\n"
            "Stage ONE variant in a disposable game copy using the established archive/override workflow.\n"
            "Back up that copy first; never replace the original source archive or this repository's corpus.\n"
            "Use identical scene, camera, lighting, and game settings for each capture.\n"
            + instructions + "\nRecord game version, screenshot paths, observations, and restore result.\n",
            encoding="utf-8",
        )
        print(test, template.width, template.height, len(rows), "validated candidates")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vehicle_root", type=Path)
    parser.add_argument("--output", type=Path, default=Path(".research-output/r4d_1/runtime-tests"))
    args = parser.parse_args()
    main(args.vehicle_root, args.output)
