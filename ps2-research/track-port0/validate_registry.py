"""Validate a Course Delta Registry v2 file.

Uses jsonschema when installed, otherwise a structural check of required keys and enums.
Both paths then apply the semantic rules that JSON Schema does not express:
  * a native-hook aspect cannot reach IMPLEMENTED_PENDING_USER_RUNTIME or RUNTIME_CONFIRMED without recorded gates;
  * trigger-layer elements must state behavior_intent;
  * on a course with pcsx2_required, every non-SAME element needs pcsx2_verification
    REQUIRED_PENDING or PERFORMED.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
DONE = ("IMPLEMENTED_PENDING_USER_RUNTIME", "RUNTIME_CONFIRMED")


def _structural(reg, schema):
    defs = schema["$defs"]
    errors = []
    for key in schema["required"]:
        if key not in reg:
            errors.append(f"missing {key}")
    if reg.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    props = defs["element"]["properties"]
    for c in reg.get("courses", []):
        for key in defs["course"]["required"]:
            if key not in c:
                errors.append(f"{c.get('course')}: missing {key}")
        for e in c.get("elements", []):
            eid = e.get("id")
            for key in defs["element"]["required"]:
                if key not in e:
                    errors.append(f"{eid}: missing {key}")
            for key in ("layer", "delta_class", "status", "pcsx2_verification"):
                if e.get(key) not in props[key]["enum"]:
                    errors.append(f"{eid}: bad {key}")
            if e.get("evidence") not in defs["evidence"]["enum"]:
                errors.append(f"{eid}: bad evidence")
            ch = e.get("channels", {})
            for aspect in defs["channels"]["required"]:
                if ch.get(aspect) not in defs["aspect"]["enum"]:
                    errors.append(f"{eid}: bad channel for {aspect}")
    return errors


def _semantic(reg):
    errors = []
    for c in reg.get("courses", []):
        for e in c.get("elements", []):
            eid = e.get("id")
            ch = e.get("channels", {})
            if "C_NATIVE_HOOK" in ch.values() and e.get("status") in DONE and not e.get("gates"):
                errors.append(f"{eid}: native hook without recorded gates")
            if e.get("layer") == "trigger" and "behavior_intent" not in e:
                errors.append(f"{eid}: trigger element needs behavior_intent")
            if c.get("pcsx2_required") and e.get("delta_class") != "SAME" \
                    and e.get("pcsx2_verification") not in ("REQUIRED_PENDING", "PERFORMED"):
                errors.append(f"{eid}: PCSX2 verification required on this course")
    return errors


def main(path):
    schema = json.loads((HERE / "registry-schema.json").read_text(encoding="utf-8"))
    reg = json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        import jsonschema
        errors = [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(reg)]
    except ImportError:
        errors = _structural(reg, schema)
    errors += _semantic(reg)
    for e in errors:
        print("FAIL:", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else HERE / "registry-example.json"))
