"""Exact, immutable Observatory identities. Unknown executables fail closed."""
from dataclasses import dataclass
import hashlib
from pathlib import Path


@dataclass(frozen=True)
class ObservatoryBuildProfile:
    id: str
    display_name: str
    sha256: str
    file_size: int
    active_log_sink_rva: int
    debug_sink_vtable_rva: int
    evidence: str
    tools: tuple[str, ...]


RETAIL_PRISTINE = ObservatoryBuildProfile(
    "retail-pristine", "Master Rallye Retail (pristine)",
    "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4",
    3121214, 0x2F7B7C, 0x29CEA8, "CONFIRMED_BY_RUNTIME",
    ("broker-editor", "flow-builder"),
)
RETAIL_WIDESCREEN_FREEZE = ObservatoryBuildProfile(
    "retail-widescreen-freeze", "Master Rallye Retail (widescreen + freeze)",
    "bcf310a79133b03aa89ce51197a37516ee27c1b0e9da19788519e849e7a2f2f6",
    3117118, 0x2F6B64, 0x29BF3C, "CONFIRMED_BY_EXE; runtime pending",
    ("broker-editor",),
)
PROFILES = (RETAIL_PRISTINE, RETAIL_WIDESCREEN_FREEZE)


def match_profile(sha256: str, file_size: int) -> ObservatoryBuildProfile:
    for profile in PROFILES:
        if sha256 == profile.sha256:
            if file_size != profile.file_size:
                raise ValueError("Known executable hash has an unexpected file size")
            return profile
    raise ValueError("Unsupported Master Rallye executable: unknown SHA256")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def profile_for_file(path: Path) -> ObservatoryBuildProfile:
    return match_profile(sha256_file(path), path.stat().st_size)
