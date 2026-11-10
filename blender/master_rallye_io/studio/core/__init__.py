"""Alias of the bpy-free Course Studio core (repository checkout or the vendored copy in the ZIP).

``from .core.materials import X`` resolves to ``master_rallye.studio.materials``.
"""
import importlib
import sys

try:
    _base = importlib.import_module("master_rallye.studio")
except ImportError:  # packaged add-on
    _base = importlib.import_module(__name__.rsplit(".", 2)[0] + ".vendor.master_rallye.studio")

NAMES = ("ai", "build", "collision", "dx_build", "importer", "materials", "model", "ps2_objects", "race",
         "templates", "textures", "validate")
for _name in NAMES:
    _module = importlib.import_module(f"{_base.__name__}.{_name}")
    sys.modules[f"{__name__}.{_name}"] = _module
    globals()[_name] = _module

SCHEMA = _base.SCHEMA
resolve_resource_root = model.resolve_resource_root  # noqa: F821
