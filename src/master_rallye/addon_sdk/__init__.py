"""Manifest-driven, offline planning foundation for the addon vehicle SDK.

This package deliberately does not patch or launch the game.  It validates
addon identity and emits deterministic integration plans against a pinned
retail capability profile.
"""

from .compiler import build_artifacts, build_to_directory, verify_build, verify_retail_executable
from .manifest import AddonValidationError, load_capabilities, load_manifests, validate_manifests
from .runtime_state import inspect_frontend_capture

__all__ = [
    "AddonValidationError",
    "build_artifacts",
    "build_to_directory",
    "inspect_frontend_capture",
    "load_capabilities",
    "load_manifests",
    "validate_manifests",
    "verify_build",
    "verify_retail_executable",
]
