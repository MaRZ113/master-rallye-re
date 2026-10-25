"""Manifest-driven, offline planning foundation for the addon vehicle SDK.

This package deliberately does not patch or launch the game.  It validates
addon identity and emits deterministic integration plans against a pinned
retail capability profile.
"""

from .compiler import build_artifacts, build_to_directory, verify_build, verify_retail_executable
from .manifest import (
    AddonValidationError, classify_runtime_identity, load_capabilities,
    load_manifests, validate_manifests,
)
from .runtime_state import inspect_frontend_capture
from .project import build_project, initialize_project, validate_project
from .physics import clone_vehicle_family_xml

__all__ = [
    "AddonValidationError",
    "build_artifacts",
    "build_project",
    "build_to_directory",
    "classify_runtime_identity",
    "clone_vehicle_family_xml",
    "initialize_project",
    "inspect_frontend_capture",
    "load_capabilities",
    "load_manifests",
    "validate_manifests",
    "validate_project",
    "verify_build",
    "verify_retail_executable",
]
