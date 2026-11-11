"""Python API of the Master Rallye Menu Builder.

Thin, dependency-free wrapper around ``mrmenu.exe`` (every command returns one JSON document) plus
helpers to edit ``*.mrmenu.json`` projects directly. Intended for scripts and coding agents (Codex):
the same core that drives the editor validates, compiles and installs layouts.

Example::

    from mr_menu_builder import MenuBuilder, Project
    mb = MenuBuilder(game=r"D:\\Game\\Master Rallye")
    p = Project.new("MyMenus", screens=["MainMenu"])
    p.patch("MainMenu", "Options", x=300, y=233, scaleX=0.9, scaleY=0.9)
    p.add_element("MainMenu", "MB_Credits", template="MainMenu/OnePlayer", x=252, y=125, text="CREDITS",
                  buttonId=10, up=4, down=5, action={"type": "navigate.screen", "screen": "Credits"})
    p.save("my.mrmenu.json")
    report = mb.validate("my.mrmenu.json")
    if report["ok"]:
        result = mb.install("my.mrmenu.json")      # transactional; errors always block
        print(result["outcome"], result["message"])  # Installed | Updated | ValidationFailed | RollbackCompleted | InstallationFailed
    mb.edit("my.mrmenu.json", "MainMenu", hide=["Progress"])   # dependency-safe edit (raises MenuBuilderError if blocked)

The executable is found via ``MRMENU_EXE``, next to this file (packaged layout) or in the build output.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

FORMAT = "mr-menu-project"
VERSION = 1
ACTION_TYPES = ("native", "navigate.screen", "navigate.back", "native.forward", "broker.set_int",
                "broker.toggle_bool", "broker.cycle_int", "extension", "none")
INSTALL_OUTCOMES = ("Installed", "Updated", "ValidationFailed", "RollbackCompleted", "InstallationFailed")
_LAYOUT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,47}$")
_ACTION_ID = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")


class MenuBuilderError(RuntimeError):
    def __init__(self, message: str, payload: dict | None = None):
        super().__init__(message)
        self.payload = payload or {}


def _find_exe() -> Path:
    env = os.environ.get("MRMENU_EXE")
    if env:
        return Path(env)
    here = Path(__file__).resolve().parent
    for candidate in (here / "mrmenu.exe", here.parent / "mrmenu.exe",
                      here.parent / "MenuBuilder.Cli/bin/Release/net8.0/mrmenu.exe",
                      here.parent / "MenuBuilder.Cli/bin/Debug/net8.0/mrmenu.exe"):
        if candidate.is_file():
            return candidate
    raise MenuBuilderError("mrmenu.exe not found; set MRMENU_EXE")


class MenuBuilder:
    """Commands bound to one game installation (read-only except install/activate/uninstall)."""

    def __init__(self, game: str | os.PathLike, exe: str | os.PathLike | None = None, game_exe: str | None = None):
        self.game = str(game)
        self.exe = Path(exe) if exe else _find_exe()
        self.game_exe = game_exe

    def run(self, command: str, *args: str, check: bool = True) -> dict[str, Any]:
        argv = [str(self.exe), command, *args]
        out = subprocess.run(argv, capture_output=True, text=True)
        try:
            data = json.loads(out.stdout)
        except json.JSONDecodeError as e:
            raise MenuBuilderError(f"{command}: no JSON output ({out.stderr.strip() or out.stdout[:200]})") from e
        if check and out.returncode == 2:
            raise MenuBuilderError(data.get("error", f"{command} failed"), data)
        return data

    def _g(self) -> list[str]:
        g = ["--game", self.game]
        if self.game_exe:
            g += ["--exe", self.game_exe]
        return g

    # -- read-only ---------------------------------------------------------------------------
    def screens(self) -> list[dict]:
        return self.run("screens", *self._g())["screens"]

    def inspect(self, screen: str, project: str | None = None, aspect: str | None = None, original: bool = False) -> dict:
        a = [*self._g(), "--screen", screen]
        if project: a += ["--project", str(project)]
        if aspect: a += ["--aspect", aspect]
        if original: a += ["--original"]
        return self.run("inspect", *a)

    def render(self, screen: str, out: str, project: str | None = None, aspect: str = "4:3", mode: str = "stock",
               size: str | None = None, focus: int | None = None, hitboxes: bool = False, nav: bool = False,
               safe: bool = False, original: bool = False) -> dict:
        a = [*self._g(), "--screen", screen, "--out", str(out), "--aspect", aspect, "--mode", mode]
        if project: a += ["--project", str(project)]
        if size: a += ["--size", size]
        if focus is not None: a += ["--focus", str(focus)]
        for flag, on in (("--hitboxes", hitboxes), ("--nav", nav), ("--safe", safe), ("--original", original)):
            if on: a.append(flag)
        return self.run("render", *a)

    def compare(self, project: str, screen: str, out: str, aspect: str = "4:3", mode: str = "stock") -> dict:
        return self.run("compare", *self._g(), "--project", str(project), "--screen", screen, "--out", str(out), "--aspect", aspect, "--mode", mode)

    def validate(self, project: str) -> dict:
        """Returns {ok, errors, warnings, screens[buttons...], findings[...]} (ok=False on errors)."""
        return self.run("validate", *self._g(), "--project", str(project), check=False)

    def texts(self, group: int | None = None, language: int = 0) -> dict:
        a = [*self._g(), "--language", str(language)]
        if group is not None: a += ["--group", str(group)]
        return self.run("texts", *a)

    def live(self) -> dict:
        return self.run("live", "--game", self.game, check=False)

    def status(self) -> dict:
        return self.run("status", "--game", self.game)

    # -- writes ------------------------------------------------------------------------------
    def compile(self, project: str, out: str) -> dict:
        return self.run("compile", *self._g(), "--project", str(project), "--out", str(out))

    def install(self, project: str, target: str | None = None, activate: bool = True, replace_foreign: bool = False) -> dict:
        """Transactional install. Returns {"ok", "outcome", "message", "findings", ...}; validation errors always block
        (there is no force). ``replace_foreign`` replaces a layout of the same name installed by another project."""
        a = [*self._g(), "--project", str(project)]
        if target: a += ["--target", str(target)]
        if not activate: a.append("--no-activate")
        if replace_foreign: a.append("--replace-foreign")
        return self.run("install", *a, check=False)

    def edit(self, project: str, screen: str, *, hide: list[str] | None = None, show: list[str] | None = None,
             disable: list[str] | None = None, enable: list[str] | None = None, delete: list[str] | None = None,
             rename: tuple[str, str] | None = None, force: bool = False) -> dict:
        """Dependency-safe element operation (same rules as the editor). Raises MenuBuilderError with the blocking
        dependencies when a native element would be deleted/renamed without ``force``."""
        a = [*self._g(), "--project", str(project), "--screen", screen]
        for flag, names in (("--hide", hide), ("--show", show), ("--disable", disable), ("--enable", enable), ("--delete", delete)):
            if names: a += [flag, ",".join(names)]
        if rename: a += ["--rename", rename[0], "--to", rename[1]]
        if force: a.append("--force")
        r = self.run("edit", *a, check=False)
        if not r.get("ok"):
            raise MenuBuilderError(r.get("error", "edit failed"), r)
        return r

    def deps(self, project: str, screen: str, element: str | None = None) -> dict:
        a = [*self._g(), "--project", str(project), "--screen", screen]
        if element: a += ["--element", element]
        return self.run("deps", *a)

    def actions(self) -> list[dict]:
        """Typed action/value catalog (IDs, owner: BuiltIn | ExtraOptions | Planned)."""
        return self.run("actions")["actions"]

    def activate(self, layout: str) -> dict:
        return self.run("activate", "--game", self.game, "--layout", layout)

    def classic(self) -> dict:
        return self.run("activate", "--game", self.game, "--classic")

    def uninstall(self, layout: str) -> dict:
        return self.run("uninstall", "--game", self.game, "--layout", layout)

    def fix_margins(self, project: str, screen: str) -> dict:
        return self.run("fix-margins", *self._g(), "--project", str(project), "--screen", screen)

    def add_screen(self, project: str, screen: str, custom: bool = False, base: str | None = None, title: str | None = None) -> dict:
        a = [*self._g(), "--project", str(project), "--screen", screen]
        if custom: a.append("--custom")
        if base: a += ["--base", base]
        if title: a += ["--title", title]
        return self.run("add-screen", *a)

    def export_screen(self, project: str, screen: str, out: str) -> dict:
        return self.run("export-screen", "--project", str(project), "--screen", screen, "--out", str(out))

    def import_screen(self, project: str, path: str, rename: str | None = None) -> dict:
        a = ["--project", str(project), "--in", str(path)]
        if rename: a += ["--rename", rename]
        return self.run("import-screen", *a)

    def api(self) -> dict:
        return self.run("api")


class Project:
    """Direct editing of a project document (same JSON the editor writes; camelCase keys)."""

    def __init__(self, data: dict):
        if data.get("format") != FORMAT:
            raise MenuBuilderError("not a mr-menu-project document")
        if int(data.get("version", 0)) > VERSION:
            raise MenuBuilderError(f"project version {data['version']} is newer than this API ({VERSION})")
        self.data = data

    @classmethod
    def new(cls, name: str, screens: list[str] | None = None) -> "Project":
        if not _LAYOUT_NAME.match(name):
            raise MenuBuilderError(f"invalid project/layout name {name!r}: letters, digits, '-' and '_' only (max 48)")
        import uuid
        d = {"format": FORMAT, "version": VERSION, "name": name, "id": uuid.uuid4().hex,
             "settings": {"mouse": True, "aspects": ["4:3", "16:10", "16:9", "21:9"], "language": 0},
             "styles": {}, "components": {}, "screens": []}
        p = cls(d)
        for s in screens or []:
            p.add_retail_screen(s)
        return p

    @classmethod
    def load(cls, path: str | os.PathLike) -> "Project":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def save(self, path: str | os.PathLike) -> None:
        Path(path).write_text(json.dumps(self.data, indent=2) + "\n", encoding="utf-8")

    # -- screens -----------------------------------------------------------------------------
    def screen(self, name: str) -> dict:
        for s in self.data["screens"]:
            if s["name"].lower() == name.lower():
                return s
        raise KeyError(name)

    def add_retail_screen(self, name: str) -> dict:
        s = {"name": name, "kind": "retail", "base": name, "elements": [], "aspects": {}}
        self.data["screens"].append(s)
        return s

    def add_custom_screen(self, name: str, title: str, base: str = "GraphicsMain", remove_base_buttons=("Options", "CardSetup"),
                          default_focus: int | None = 1) -> dict:
        s = {"name": name, "kind": "custom", "base": base, "title": title, "back": {"type": "navigate.back"},
             "elements": [{"name": n, "base": n, "deleted": True} for n in remove_base_buttons], "aspects": {}}
        if default_focus is not None:
            s["defaultFocus"] = default_focus
        self.data["screens"].append(s)
        return s

    # -- elements ----------------------------------------------------------------------------
    def element(self, screen: str, name: str) -> dict:
        s = self.screen(screen)
        for e in s["elements"]:
            if e["name"] == name or e.get("base") == name:
                return e
        e = {"name": name, "base": name, "patch": {}}
        s["elements"].append(e)
        return e

    def patch(self, screen: str, egg: str, aspect: str | None = None, **fields: Any) -> dict:
        """Patch fields (x, y, scaleX, scaleY, model, bankIndex, drawPriority, visible, buttonId, up, down, left,
        right, enabled, text, textId, textIndex, textKey, font, textOffsetX, textOffsetY, icon, hJustify,
        vJustify, anchor, raw). With ``aspect`` the patch only applies to that variant."""
        if aspect and aspect != "4:3":
            overrides = self.screen(screen).setdefault("aspects", {}).setdefault(aspect, {})
            target = overrides.setdefault(egg, {})
        else:
            target = self.element(screen, egg).setdefault("patch", {})
        target.update({k: v for k, v in fields.items() if v is not None})
        return target

    def add_element(self, screen: str, name: str, template: str, action: dict | None = None, style: str | None = None, **fields: Any) -> dict:
        """New element from a template: "Egg" of the base screen, "Screen/Egg" of a retail screen or "component:Name"."""
        if action is not None and action.get("type") not in ACTION_TYPES:
            raise MenuBuilderError(f"unknown action type {action.get('type')}")
        e = {"name": name, "template": template, "patch": {k: v for k, v in fields.items() if v is not None}}
        if action is not None: e["action"] = action
        if style: e["style"] = style
        self.screen(screen)["elements"].append(e)
        return e

    def delete(self, screen: str, egg: str) -> None:
        e = self.element(screen, egg)
        if e.get("base") is None:
            self.screen(screen)["elements"].remove(e)
        else:
            e["deleted"] = True

    def set_action(self, screen: str, egg: str, action: dict | None) -> None:
        e = self.element(screen, egg)
        if action is None:
            e.pop("action", None)
        else:
            if action.get("type") not in ACTION_TYPES:
                raise MenuBuilderError(f"unknown action type {action.get('type')}")
            if action.get("type") == "extension" and not _ACTION_ID.match(action.get("extension") or ""):
                raise MenuBuilderError(f"invalid action ID {action.get('extension')!r} (lower-case dotted name, e.g. vehicle.paint)")
            e["action"] = action

    def bind_value(self, screen: str, egg: str, source: str | None, fmt: str = "{value}", fallback: str = "N/A") -> None:
        """Dynamic text: the runtime writes the provider value (e.g. vehicle.model_source) into this text element."""
        e = self.element(screen, egg)
        patch = e.setdefault("patch", {})
        if source is None:
            for k in ("valueSource", "valueFormat", "valueFallback"): patch.pop(k, None)
            return
        if not _ACTION_ID.match(source):
            raise MenuBuilderError(f"invalid value ID {source!r}")
        patch.update({"valueSource": source, "valueFormat": fmt, "valueFallback": fallback})

    def style(self, name: str, **fields: Any) -> None:
        self.data.setdefault("styles", {})[name] = fields

    def component(self, name: str, template: str, style: str | None = None, **fields: Any) -> None:
        c = {"template": template, "patch": fields}
        if style: c["style"] = style
        self.data.setdefault("components", {})[name] = c


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Menu Builder API smoke: list screens and validate a project")
    ap.add_argument("--game", required=True)
    ap.add_argument("--project")
    a = ap.parse_args()
    mb = MenuBuilder(a.game)
    print(json.dumps([s["name"] for s in mb.screens()]))
    if a.project:
        r = mb.validate(a.project)
        print(json.dumps({"ok": r["ok"], "errors": r["errors"], "warnings": r["warnings"]}))
