"""Validate a Course Delta Registry v2 file. Uses jsonschema when installed,
otherwise a minimal structural check of required keys and enums."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent


def _minimal(reg, schema):
    defs = schema["$defs"]
    errors = []
    for key in schema["required"]:
        if key not in reg:
            errors.append(f"missing {key}")
    if reg.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    for c in reg.get("courses", []):
        for key in defs["course"]["required"]:
            if key not in c:
                errors.append(f"{c.get('course')}: missing {key}")
        for e in c.get("elements", []):
            props = defs["element"]["properties"]
            for key in defs["element"]["required"]:
                if key not in e:
                    errors.append(f"{e.get('id')}: missing {key}")
            for key in ("layer", "delta_class", "channel", "status"):
                if e.get(key) not in props[key]["enum"]:
                    errors.append(f"{e.get('id')}: bad {key}")
            if e.get("evidence") not in defs["evidence"]["enum"]:
                errors.append(f"{e.get('id')}: bad evidence")
            if e.get("channel") == "C_NATIVE_HOOK" and e.get("status") == "IMPLEMENTED_PENDING_USER_RUNTIME":
                errors.append(f"{e.get('id')}: native hook without gate")
    return errors


def main(path):
    schema = json.loads((HERE / "registry-schema.json").read_text(encoding="utf-8"))
    reg = json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        import jsonschema
        errors = [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(reg)]
    except ImportError:
        errors = _minimal(reg, schema)
    for e in errors:
        print("FAIL:", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else HERE / "registry-example.json"))
