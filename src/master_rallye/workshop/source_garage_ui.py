"""Separate neutral source-scene workspace; no native MR build actions."""
from __future__ import annotations

import copy
import json
import subprocess
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .branding import apply_icon
from master_rallye.source_scene_preview import capture_startup_info, capture_views, stage_source_scene, viewer_command, preview_cull, VIEWS

MATERIAL_MODES = {"Source RGB / default coverage": "original", "Explicit opacity interpretation": "interpreted",
                  "Material ID colors (diagnostic)": "material_ids"}
VISIBILITY_MODES = {"Selected stock configuration": "selected", "Original source visibility flags": "source",
                    "All retained parts (diagnostic)": "all"}


def native_creation_available(scene):
    return bool(scene and scene.get('metadata', {}).get('source_adapter') == 'evo2-4runner/1')


def load_source_project(path: Path):
    """Reopen through the common validator, not through an MR Workshop project."""
    from master_rallye.universal_vehicle_scene import load_scene
    path = Path(path)
    scene_path = path / "scene.json" if path.is_dir() else path
    scene = load_scene(scene_path)
    if scene.get("schema") != "universal-vehicle-scene/1":
        raise ValueError("Universal Vehicle Scene v1 required")
    return scene_path.parent, scene


def preview_configuration(scene: dict, settings: dict) -> dict:
    """Explicit interpretation is a copy; original scene is never mutated."""
    result = copy.deepcopy(scene)
    overrides = settings.get("opacity_overrides", {})
    known = {m["id"] for m in result["materials"]}
    if not isinstance(overrides, dict) or set(overrides) - known:
        raise ValueError("Unknown material opacity override")
    for material in result["materials"]:
        if material["id"] in overrides:
            value = overrides[material["id"]]
            if type(value) not in (int, float) or not 0 <= value <= 1:
                raise ValueError("Preview opacity must be 0..1")
            material["preview"] = {**material.get("preview", {}), "opacity": value}
    detail = settings.get("wheel_detail")
    if detail is not None:
        variants = result.get("wheel_variants", {})
        known_meshes = {mesh["id"] for mesh in result["meshes"]}
        if detail not in ("08", "12", "16") or any(detail + side not in variants for side in ("L", "R")):
            raise ValueError("Wheel detail is not a retained source variant")
        for node in result["nodes"]:
            if node.get("role") != "wheel":
                continue
            slot = node.get("wheel_slot", "")
            if ".ltire" in slot: side = "L"
            elif ".rtire" in slot: side = "R"
            else: raise ValueError("Unknown source wheel-side association")
            mesh_ids = variants[detail + side]["mesh_ids"]
            if not mesh_ids or any(key not in known_meshes for key in mesh_ids):
                raise ValueError("Wheel variant references missing source geometry")
            node["mesh_ids"] = list(mesh_ids)
        result.setdefault("selection", {})["wheel_detail"] = detail
        result["selection"]["wheel_lod_index"] = {"08": 0, "12": 1, "16": 2}[detail]
    return result


class SourceGarageWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root); apply_icon(self.window)
        self.window.title("Rally Workshop — Source Garage")
        self.window.geometry("1160x850"); self.window.minsize(960, 680)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.scene = None; self.scene_root = None; self.process = None; self.photos = []
        self.preview_path = None; self.opacity_overrides = {}; self.selected_material = None
        self.source = tk.StringVar()
        default = Path("E:/RallyWorkshop_Sources/sources/4x4 Evo 2")
        if default.is_dir():
            self.source.set(str(default))
        self.catalog = tk.StringVar(value="TRUCK/T4RSR52.TRK")
        self.basis = tk.StringVar(value="normalized")
        self.material_mode = tk.StringVar(value=next(iter(MATERIAL_MODES)))
        self.visibility = tk.StringVar(value=next(iter(VISIBILITY_MODES)))
        self.view = tk.StringVar(value="isometric")
        self.opacity = tk.StringVar(value="1.0")
        self.wheel_detail = tk.StringVar(value="16")
        self.status = tk.StringVar(value="Read-only Evo2 source → neutral scene. MR integration and gameplay are separate milestones.")
        bar = ttk.Frame(self.window, padding=8); bar.pack(fill="x")
        ttk.Label(bar, text="Read-only Evo2 installation").pack(side="left")
        ttk.Entry(bar, textvariable=self.source).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(bar, text="Choose source…", command=self.choose_source).pack(side="left")
        actions = ttk.Frame(self.window, padding=(8, 0, 8, 8)); actions.pack(fill="x")
        self.action_buttons = {}
        for label, method in (("Inspect source", self.inspect), ("Create neutral source scene", self.create),
                              ("Reopen source scene…", self.reopen), ("Preview", self.preview),
                              ("Open neutral 3D", self.interactive), ("Capture six views", self.capture),
                              ("Save preview choices", self.save_choices)):
            button = ttk.Button(actions, text=label, command=method); button.pack(side="left", padx=3)
            self.action_buttons[label] = button
        authoring = ttk.Frame(self.window, padding=(8, 0, 8, 8)); authoring.pack(fill="x")
        self.action_buttons["Create 4Runner Stable…"] = ttk.Button(authoring, text="Create 4Runner Stable…", command=self.create_mr_dialog)
        self.action_buttons["Create 4Runner Stable…"].pack(side="left")
        ttk.Button(authoring, text="Source / MR Help", command=lambda:self.app.show_help('universal-source')).pack(side="left", padx=8)
        self.identity = tk.StringVar(value="Toyota 4Runner SR5 Sport Package 2WD · catalog T4RSR52 · neutral D3D9 approximation · unspecified TIFF channel is not assumed alpha")
        ttk.Label(self.window, textvariable=self.identity,
                  padding=(10, 0)).pack(fill="x")
        options = ttk.Frame(self.window, padding=8); options.pack(fill="x")
        for label, variable, choices, width in (("Coordinates", self.basis, ("normalized", "source"), 13),
                                               ("Materials", self.material_mode, tuple(MATERIAL_MODES), 32),
                                               ("Parts", self.visibility, tuple(VISIBILITY_MODES), 32),
                                               ("View", self.view, VIEWS, 12)):
            ttk.Label(options, text=label).pack(side="left", padx=(5, 3))
            box = ttk.Combobox(options, textvariable=variable, values=choices, state="readonly", width=width)
            box.pack(side="left"); box.bind("<<ComboboxSelected>>", self._mark_preview_pending)
        wheelbar = ttk.Frame(self.window, padding=(8, 0, 8, 5)); wheelbar.pack(fill="x")
        ttk.Label(wheelbar, text="Original wheel detail").pack(side="left", padx=5)
        wheelbox = ttk.Combobox(wheelbar, textvariable=self.wheel_detail, values=("08", "12", "16"), state="readonly", width=5)
        self.wheelbox = wheelbox
        wheelbox.pack(side="left"); wheelbox.bind("<<ComboboxSelected>>", self._wheel_changed)
        self.wheel_hint = tk.StringVar(value="16 = explicit high-detail inspection; original six wheel meshes stay retained. Static zero-angle pose.")
        ttk.Label(wheelbar, textvariable=self.wheel_hint).pack(side="left", padx=8)
        split = ttk.Panedwindow(self.window, orient="horizontal"); split.pack(fill="both", expand=True, padx=8)
        self.window.after(100, lambda: split.sashpos(0, max(410, self.window.winfo_width() * 43 // 100)))
        left = ttk.Frame(split); right = ttk.Frame(split); split.add(left, weight=2); split.add(right, weight=3)
        treeframe = ttk.Frame(left); treeframe.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(treeframe, columns=("role", "visible", "material"), show="tree headings", height=12)
        self.tree.heading("#0", text="Retained source node / mesh"); self.tree.column("#0", width=220)
        for key, title in (("role", "Role"), ("visible", "Selected"), ("material", "Material")):
            self.tree.heading(key, text=title); self.tree.column(key, width=80)
        scroll = ttk.Scrollbar(treeframe, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set); scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True); self.tree.bind("<<TreeviewSelect>>", self.selected)
        alpha = ttk.Frame(left, padding=6); alpha.pack(fill="x")
        ttk.Label(alpha, text="Selected material preview opacity").pack(side="left")
        ttk.Entry(alpha, textvariable=self.opacity, width=6).pack(side="left", padx=4)
        ttk.Button(alpha, text="Set interpretation", command=self.set_opacity).pack(side="left")
        self.details = tk.Text(left, bg="#191d23", fg="#e5e7eb", wrap="word", height=8, width=48)
        self.details.pack(fill="both", expand=True)
        self.image = ttk.Label(right, text="Create or reopen a neutral source scene.", anchor="center")
        self.image.pack(fill="both", expand=True)
        self.image_source = None
        self.image.bind("<Configure>", self._fit_image)
        ttk.Label(self.window, textvariable=self.status, wraplength=1100, padding=8).pack(fill="x")
        self._controls()

    def _controls(self):
        for label in ("Preview", "Open neutral 3D", "Capture six views", "Save preview choices", "Create 4Runner Stable…"):
            self.action_buttons[label].state(["!disabled"] if self.scene is not None else ["disabled"])
        if self.scene is not None and not native_creation_available(self.scene):
            self.action_buttons["Create 4Runner Stable…"].state(["disabled"])

    def _run(self, title, work, done):
        if self.app.busy:
            return
        def finish(value):
            if self.window.winfo_exists():
                done(value); self._controls()
        self.app.run(title, work, finish)

    def create_mr_dialog(self):
        if self.scene is None or self.app.busy:return
        if not native_creation_available(self.scene):
            self.status.set('This source is research-only; no qualified native MR conversion profile.');return
        if getattr(self,'mr_dialog',None) is not None and self.mr_dialog.winfo_exists():
            self.mr_dialog.lift();return
        dialog=tk.Toplevel(self.window);apply_icon(dialog);dialog.title('Create independent 4Runner Stable project')
        self.mr_dialog=dialog
        retail=self.app.sdk_root.parent/'corpora/retail'
        defaults={'donor_dir':retail/'Data.sma_unpacked/DataGx/Vehicles/Terrano',
                  'retail_sma':retail/'Data.sma','retail_root':retail/'Data.sma_unpacked',
                  'base_roster':self.app.sdk_root/'.research-output/vehicles/heritage/roster'}
        self.mr_fields={key:tk.StringVar(value=str(value) if value.exists() else '')for key,value in defaults.items()}
        for key,label in (('donor_dir','Qualified retail SUV model folder'),('retail_sma','Clean retail Data.sma'),
                          ('retail_root','Unpacked clean retail resource root'),('base_roster','Qualified base roster folder (copied)')):
            row=ttk.Frame(dialog,padding=6);row.pack(fill='x')
            ttk.Label(row,text=label,width=39).pack(side='left')
            ttk.Entry(row,textvariable=self.mr_fields[key],width=70).pack(side='left',fill='x',expand=True)
            def browse(k=key):
                path=(filedialog.askopenfilename(parent=dialog,title='Clean retail Data.sma',filetypes=[('Master Rallye archive','*.sma')])
                      if k=='retail_sma' else filedialog.askdirectory(parent=dialog,title='Select '+k.replace('_',' ')))
                if path:self.mr_fields[k].set(path)
            ttk.Button(row,text='Choose…',command=browse).pack(side='left',padx=5)
        ttk.Label(dialog,wraplength=830,padding=12,text='4Runner Stable: accepted side glass and lower brake fixes, original dark rear glazing, mirrors, paint and crew. Creates private source, authoring and Workshop copies; preserves the neutral scene. The selected roster is copied into an independent CarID29 alternative. MR donor systems are adaptations. Gameplay remains pending owner testing.').pack(fill='x')
        visual=ttk.LabelFrame(dialog,text='Rejected Visual Polish experiments — disabled after owner D3D8 review',padding=8)
        visual.pack(fill='x',padx=10)
        labels={'paint_reflection':'Subtle opaque paint reflections','mirror_insets':'Reflective mirror insets',
                'cabin':'MR Navara steering wheel / minimal dashboard / dark cabin',
                'rear_glazing':'Static rear glazing with dark backing (no rear damage zone)',
                'underbody_frame':'Body-fixed underbody frame (no moving axles or physics edits)'}
        self.mr_visual_options={key:tk.BooleanVar(value=False)for key in labels}
        for key,label in labels.items():ttk.Checkbutton(visual,text=label,variable=self.mr_visual_options[key],state='disabled').pack(anchor='w')
        self.mr_upper_brake=tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog,text='Upper center brake strip: independent test variant (D3D8 owner test pending)',variable=self.mr_upper_brake).pack(anchor='w',padx=12,pady=5)
        def create():
            values={key:Path(value.get())for key,value in self.mr_fields.items()}
            if any(not value.get().strip()for value in self.mr_fields.values()):
                messagebox.showerror('MR Source Fidelity','Supply all four qualified input paths.',parent=dialog);return
            scene_path=self.scene_root/'scene.json'
            visual_options={key:value.get()for key,value in self.mr_visual_options.items()}
            upper_brake=self.mr_upper_brake.get()
            target=self.app.workspace/'universal-imports'/uuid.uuid4().hex[:16]
            def work():
                from master_rallye.source_garage_pilot import create_pilot
                return create_pilot(scene_path,values['donor_dir'],values['retail_sma'],target,
                                    retail_root=values['retail_root'],base_roster=values['base_roster'],build=False,visual_options=visual_options,upper_brake_lamp=upper_brake)
            def done(report):
                from .service import WorkshopProject
                if dialog.winfo_exists():dialog.destroy()
                self.show(report);self.app._opened(WorkshopProject(Path(report['workshop'])))
                self.status.set('Independent MR Source Fidelity project created. Use Workshop Validate / Build; original neutral source is unchanged.')
            self._run('Create independent MR Source Fidelity addon',work,done)
        self.mr_create_button=ttk.Button(dialog,text='Create 4Runner Stable project',command=create)
        self.mr_create_button.pack(pady=12)

    def show(self, value):
        self.details.delete("1.0", "end")
        self.details.insert("end", json.dumps(value, indent=2, ensure_ascii=False, default=str))

    def choose_source(self):
        selected = filedialog.askdirectory(parent=self.window, title="Original read-only 4x4 Evolution 2 installation")
        if selected:
            self.source.set(selected)

    def inspect(self):
        from master_rallye.source_adapters.evo2 import inspect_source
        source = Path(self.source.get())
        self._run("Inspect read-only Evo2 source", lambda: inspect_source(source), self.show)

    def create(self):
        from master_rallye.source_adapters.evo2 import create_scene
        source = Path(self.source.get())
        detail = self.wheel_detail.get() or "16"
        target = self.app.workspace / "source-garage" / uuid.uuid4().hex[:16]
        def work():
            report = create_scene(source, target, wheel_detail=detail)
            return target, report
        def done(value):
            target, report = value
            self._open(target / "scene.json"); self.show(report)
            self.status.set("Neutral source scene created. Source game files stay read-only; no MR CarID or build was created.")
        self._run("Create bounded Evo2 neutral scene", work, done)

    def reopen(self):
        selected = filedialog.askopenfilename(parent=self.window, title="Reopen Universal Vehicle Scene",
                                              filetypes=[("Neutral source scene", "scene.json"), ("JSON", "*.json")])
        if selected:
            try:
                self._open(Path(selected))
            except (ValueError, OSError, KeyError) as exc:
                messagebox.showerror("Source Garage", str(exc), parent=self.window)

    def _open(self, path):
        from master_rallye.universal_vehicle_scene import read_bounded
        scene_root, scene = load_source_project(path)
        choices = scene_root / "source-preview-choices.json"
        settings = {}
        if choices.is_file():
            settings = json.loads(read_bounded(choices, 1024 * 1024))
            if settings.get("schema") != "source-preview-choices/1":
                raise ValueError("Unsupported source preview choices")
            preview_configuration(scene, settings)
            if settings.get("basis") in ("source", "normalized"):
                self.basis.set(settings["basis"])
            if settings.get("material_mode") in MATERIAL_MODES:
                self.material_mode.set(settings["material_mode"])
            if settings.get("visibility") in VISIBILITY_MODES:
                self.visibility.set(settings["visibility"])
            if settings.get("view") in VIEWS:
                self.view.set(settings["view"])
        self.scene_root, self.scene = scene_root, scene
        self.opacity_overrides = settings.get("opacity_overrides", {}); self.preview_path = None
        self.selected_material = None
        self.image_source = None; self.photos = []
        self.image.configure(image="", text="Scene reopened. Choose Preview to render current choices.")
        self.wheel_detail.set(settings.get("wheel_detail", scene.get("selection", {}).get("wheel_detail", "16")))
        has_wheel_variants = bool(scene.get("wheel_variants"))
        self.wheelbox.configure(state="readonly" if has_wheel_variants else "disabled")
        if not has_wheel_variants:self.wheel_detail.set("")
        self.wheel_hint.set("16 = explicit high-detail inspection; original six wheel meshes stay retained. Static zero-angle pose."
                            if has_wheel_variants else "Original source wheel assembly; no qualified alternate detail selection. Static inspection pose.")
        self.identity.set(scene.get("metadata", {}).get("display_name", "Source vehicle") +
                          " · neutral D3D9 · original source and rendering interpretations remain separate")
        self._populate()
        self.show({"scene": str(self.scene_root / "scene.json"), "metadata": self.scene.get("metadata"),
                   "coordinate_system": self.scene["coordinate_system"], "unknown_semantics": self.scene.get("unknown_semantics")})
        self.status.set("Reopened neutral source scene. Original data and preview interpretations are separate.")
        self._controls()

    def _populate(self):
        if self.scene is None:
            return
        scene = preview_configuration(self.scene, self.settings())
        self.selected_material = None
        self.tree.delete(*self.tree.get_children())
        meshes = {m["id"]: m for m in scene["meshes"]}
        self.rows = {}
        for node in scene["nodes"]:
            for mesh_id in node["mesh_ids"]:
                mesh = meshes[mesh_id]; key = str(len(self.rows)); self.rows[key] = (node, mesh)
                self.tree.insert("", "end", iid=key, text=node.get("name", node["id"]) + " / " + mesh.get("name", mesh_id),
                                 values=(node.get("role", ""), node["visible"], mesh["material_id"]))

    def _mark_preview_pending(self, event=None):
        if self.scene is not None:
            self.image_source = None; self.photos = []
            self.image.configure(image="", text="Preview choices changed. Choose Preview or reopen neutral 3D.")
            self.status.set("Preview choices changed; the next render applies them. Original source scene is unchanged.")

    def _wheel_changed(self, event=None):
        self._populate(); self._mark_preview_pending()

    def selected(self, event=None):
        keys = self.tree.selection()
        if not keys:
            return
        node, mesh = self.rows[keys[0]]
        material = next(m for m in self.scene["materials"] if m["id"] == mesh["material_id"])
        texture = next((t for t in self.scene["textures"] if t["id"] == material.get("diffuse_texture_id")), {})
        self.selected_material = material["id"]; self.opacity.set(str(self.opacity_overrides.get(material["id"], 1.)))
        self.show({"node": node, "mesh": {k: v for k, v in mesh.items() if k not in ("positions", "normals", "uvs", "triangles", "animation_frames")},
                   "source_material": material, "texture_source_channels": texture.get("source_channels"),
                   "preview_opacity_override": self.opacity_overrides.get(material["id"]),
                   "boundary": "Names/flags retained as source evidence; unknown native shaders are not synthesized."})

    def set_opacity(self):
        if not self.selected_material:
            self.status.set("Select a source surface first."); return
        try:
            value = float(self.opacity.get())
            preview_configuration(self.scene, {"opacity_overrides": {self.selected_material: value}})
            self.opacity_overrides[self.selected_material] = value
            self.material_mode.set("Explicit opacity interpretation")
            self._mark_preview_pending()
            self.status.set("Explicit preview opacity set. Original channel bytes and source material remain unchanged; this does not decode the unspecified TIFF channel.")
        except ValueError as exc:
            messagebox.showerror("Preview interpretation", str(exc), parent=self.window)

    def settings(self):
        return {"schema": "source-preview-choices/1", "basis": self.basis.get(), "material_mode": self.material_mode.get(),
                "visibility": self.visibility.get(), "view": self.view.get(), "opacity_overrides": self.opacity_overrides,
                "wheel_detail": self.wheel_detail.get() if self.scene and self.scene.get("wheel_variants") else None}

    def save_choices(self):
        if self.scene_root is None:
            return
        from master_rallye.universal_vehicle_scene import unlinked, read_bounded
        try:
            path = self.scene_root / "source-preview-choices.json"; unlinked(path)
            protected = [self.scene["source"]["root"], *self.scene["source"].get("protected_roots", [])]
            if any(path.resolve().is_relative_to(Path(root).resolve()) for root in protected):
                raise ValueError("Preview choices cannot be written inside original game source")
            if path.exists() and json.loads(read_bounded(path, 1024 * 1024)).get("schema") != "source-preview-choices/1":
                raise ValueError("Refusing to replace an unrelated file")
            temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
            with temporary.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(self.settings(), indent=2, allow_nan=False) + "\n")
            temporary.replace(path)
            self.status.set("Preview choices saved beside the private scene. Reopening restores the choices; original scene is unchanged.")
        except (ValueError, OSError) as exc:
            messagebox.showerror("Source preview choices", str(exc), parent=self.window)

    def _request(self):
        settings = self.settings(); scene = preview_configuration(self.scene, settings)
        target = self.app.workspace / "source-garage-previews" / uuid.uuid4().hex[:16]
        return scene, target, {"scene_root": self.scene_root, "basis": settings["basis"],
                               "material_mode": MATERIAL_MODES[settings["material_mode"]],
                               "visibility": VISIBILITY_MODES[settings["visibility"]]}

    def _display(self, path):
        from PIL import Image
        with Image.open(path) as image:
            self.image_source = image.convert("RGB")
        self._fit_image()

    def _fit_image(self, event=None):
        if self.image_source is None:
            return
        from PIL import ImageTk
        image = self.image_source.copy()
        image.thumbnail((max(100, self.image.winfo_width() - 10), max(100, self.image.winfo_height() - 10)))
        photo = ImageTk.PhotoImage(image, master=self.window)
        self.photos = [photo]; self.image.configure(image=photo, text="")

    def preview(self):
        if self.scene is None:
            return
        scene, target, options = self._request(); view = self.view.get()
        def work():
            report = stage_source_scene(scene, target / "preview.mrpv", **options)
            capture = target / (view + ".bmp")
            subprocess.run(viewer_command(self.app.viewer, target / "preview.mrpv", view=view, capture=capture,
                                          provenance=report["display_name"], basis=report["basis"], cull=preview_cull(scene)), check=True, timeout=45,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), startupinfo=capture_startup_info())
            return target / "preview.mrpv", capture, report
        def done(value):
            self.preview_path, capture, report = value; self._display(capture)
            self.status.set(f"D3D9 {view} · {report['basis']} coordinates · {report['material_mode']} · {report['visibility']} parts. Source-game parity unqualified.")
        self._run("Render neutral source scene", work, done)

    def interactive(self):
        if self.scene is None:
            return
        scene, target, options = self._request(); view = self.view.get()
        def work():
            report = stage_source_scene(scene, target / "interactive.mrpv", **options)
            return target / "interactive.mrpv", report
        def done(value):
            path, report = value
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()
            self.process = subprocess.Popen(viewer_command(self.app.viewer, path, view=view, provenance=report["display_name"], basis=report["basis"], cull=preview_cull(scene)))
            self.preview_path = path
            self.status.set("Neutral 3D viewport: orbit/pan/zoom, geometry picking, layer isolation, source material diagnostics. No MR compilation.")
        self._run("Stage interactive neutral preview", work, done)

    def capture(self):
        if self.scene is None:
            return
        scene, target, options = self._request()
        def work():
            report = stage_source_scene(scene, target / "capture.mrpv", **options)
            result = capture_views(self.app.viewer, target / "capture.mrpv", target / "views", provenance=report["display_name"], basis=report["basis"], cull=preview_cull(scene))
            return target, result
        def done(value):
            target, report = value; self._display(report["views"]["isometric"]); self.show(report)
            self.status.set(f"Six D3D9 orthographic captures saved; showing isometric: {target / 'views'}. Static source wheel pose; no settled-suspension or source-game parity claim.")
        self._run("Capture neutral source scene from six views", work, done)

    def close(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
        self.window.destroy()
