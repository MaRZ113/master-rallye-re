"""Loopback-only optional browser for gt_sound_lab; no third-party packages."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import uuid

import gt_sound_lab as lab
from gt4_audio_extract import decode_spu, pcm_wav


def normalize_gt3(report):
    return lab.normalize_gt3(report)


def serve(args):
    output = lab.private_output(args.output, tuple(p for p in
        (args.gt4_root.parent if args.gt4_root else None, args.gt3_volume.parent if args.gt3_volume else None) if p))
    output.mkdir(parents=True)
    catalogs = {}
    if args.gt4_root:
        catalogs["gt4"] = lab.gt4_catalog(args.gt4_root)
        sound_dir = args.gt4_root / "sound_gt/sound"
        catalogs["gt4"]["global_banks"] = [p.relative_to(args.gt4_root).as_posix() for p in sorted(list(sound_dir.glob("*.ins")) + list(sound_dir.glob("*.es")))]
    if args.gt3_volume:
        from gt3_sound_lab import catalog
        catalogs["gt3"] = normalize_gt3(catalog(args.gt3_volume, include_banks=False))
        catalogs["gt3"]["global_banks"] = [b["bank_id"] for b in catalogs["gt3"]["banks"] if b.get("format") == "INST" or b["bank_id"].endswith(".ins")]
    if not catalogs:
        raise ValueError("at least one explicit local source required")
    inspected = {}; audio_files = {}

    def inspect(game, bank):
        key = game, bank
        if key not in inspected:
            if game not in catalogs:
                raise ValueError("source game not configured")
            allowed = {b["bank_id"] for b in catalogs[game]["banks"]} | set(catalogs[game]["global_banks"])
            if bank not in allowed:
                raise ValueError("bank not in configured source inventory")
            if game == "gt4":
                inspected[key] = lab.inspect_gt4(args.gt4_root, bank, args.pitch_core)
            else:
                from gt3_sound_lab import inspect_member
                inspected[key] = inspect_member(args.gt3_volume, bank)
        return inspected[key]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *unused): pass

        def send(self, status, data, mime="application/json; charset=utf-8"):
            if not isinstance(data, bytes): data = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; media-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers(); self.wfile.write(data)

        def local_request(self):
            host = self.headers.get("Host", "")
            expected = f"127.0.0.1:{self.server.server_port}"
            if host != expected:
                raise ValueError("loopback host required")
            if self.headers.get("Origin") not in (None, "http://" + expected):
                raise ValueError("same-origin request required")

        def do_GET(self):
            try:
                self.local_request()
                url = urlparse(self.path); q = parse_qs(url.query)
                if url.path == "/":
                    self.send(200, (Path(__file__).with_name("gt_sound_lab.html")).read_bytes(), "text/html; charset=utf-8")
                elif url.path == "/api/catalog":
                    # Catalogs stay in this process; this is a private local viewer.
                    self.send(200, catalogs)
                elif url.path == "/api/bank":
                    self.send(200, inspect(q["game"][0], q["bank"][0]))
                elif url.path == "/api/compare":
                    self.send(200, lab.compare_banks(inspect(q["game"][0], q["bank"][0]), inspect(q["game"][0], q["other"][0])))
                elif url.path.startswith("/audio/") and url.path[7:] in audio_files:
                    self.send(200, audio_files[url.path[7:]].read_bytes(), "audio/wav")
                else: self.send(404, {"error": "not found"})
            except (ValueError, KeyError, OSError, IndexError) as error:
                self.send(400, {"error": str(error)})

        def do_POST(self):
            try:
                self.local_request()
                size = int(self.headers.get("Content-Length", "0"))
                if self.path != "/api/audition" or not 1 <= size <= 4096:
                    raise ValueError("bounded audition request required")
                data = json.loads(self.rfile.read(size))
                game, bank = data["game"], data["bank"]
                report = inspect(game, bank)
                matches = [e for e in report["entries"] if str(e["entry_id"]) == str(data["entry"])]
                if len(matches) != 1 or matches[0].get("codec_status") != "PCM_VALID":
                    raise ValueError("select one PCM-valid entry")
                entry = matches[0]
                if game == "gt4":
                    raw = lab.read_bounded(lab.gt4_bank(args.gt4_root, bank))
                else:
                    from gt3_ui_icon import read_member
                    raw, _ = read_member(args.gt3_volume, bank)
                if lab.sha256(raw) != report["sha256"]:
                    raise ValueError("source changed since inspection")
                at = entry["sample_file_offset"]
                if game == "gt3":
                    from gt3_sound_lab import decode_sample
                    decoded = {"samples": decode_sample(raw, entry), "loop_start_sample": entry["loop_start_sample"],
                               "loop_end_sample": entry["loop_end_sample"]}
                else:
                    decoded = decode_spu(raw[at:at + entry["encoded_bytes"]])
                if game == "gt4" and args.pitch_core and report["format"] == "ENGN":
                    rate = round(entry["anchor_rate_exact_hz"])
                    provenance = "qualified supplied CORE anchor pitch; comparative native evidence, no full mixer"
                else:
                    rate = data.get("sample_rate")
                    provenance = "explicit caller-selected nominal rate; original pitch UNKNOWN"
                loop = None if decoded["loop_start_sample"] is None else (decoded["loop_start_sample"], decoded["loop_end_sample"])
                wav = pcm_wav(decoded["samples"], rate, loop)
                identifier = uuid.uuid4().hex
                path = output / (identifier + ".wav")
                path.write_bytes(wav)
                sidecar = {"schema": lab.SCHEMA, "game": game, "bank_id": bank, "bank_sha256": report["sha256"],
                           "selection": entry, "sample_rate_hz": rate, "rate_provenance": provenance,
                           "wav_sha256": lab.sha256(wav), "authentic_effect_identity": None,
                           "boundary": "Private individual sample audition. No complete original vehicle mix is reproduced."}
                lab.save_json(path.with_suffix(".json"), sidecar)
                audio_files[path.name] = path
                self.send(200, {"audio_url": "/audio/" + path.name, "output": str(path), "provenance": sidecar})
            except (ValueError, TypeError, KeyError, OSError, IndexError) as error:
                self.send(400, {"error": str(error)})

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"GT Sound Bank Lab: http://127.0.0.1:{server.server_port}", flush=True)
    print(f"Private audition output: {output}", flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == "__main__":
    raise SystemExit("Run tools/gt_sound_lab.py serve")
