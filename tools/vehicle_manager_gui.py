"""Vehicle Manager window (tkinter): order, remove/restore, packages, apply. See tools/vehicle_manager.py."""
from __future__ import annotations
import threading, tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from vehicle_manager import CLASSES, Manager


def run(m: Manager):
    root = tk.Tk()
    root.title(f"Master Rallye Vehicle Manager - {m.game}")
    root.geometry("980x560")
    status = tk.StringVar(value="")
    lists, ids = {}, {}

    top = ttk.Frame(root, padding=8); top.pack(fill="both", expand=True)
    classes = ttk.Frame(top); classes.pack(side="left", fill="both", expand=True)
    for col, cls in enumerate(CLASSES):
        frame = ttk.LabelFrame(classes, text=cls, padding=4)
        frame.grid(row=0, column=col, sticky="nsew", padx=4)
        classes.columnconfigure(col, weight=1); classes.rowconfigure(0, weight=1)
        box = tk.Listbox(frame, width=26, height=20, exportselection=False)
        box.pack(fill="both", expand=True)
        lists[cls] = box

    def selected():
        for cls, box in lists.items():
            pick = box.curselection()
            if pick:
                return ids[cls][pick[0]]
        return None

    def refresh(keep=None):
        try:
            native, plan = m.native(), m.plan()
        except Exception as e:                       # no base yet
            status.set(f"No base roster: {e}. Use 'Import active roster'.")
            return
        names = native["names"]
        removed = set(m.selection().get("removed", []))
        for cls in CLASSES:
            box = lists[cls]; box.delete(0, "end"); ids[cls] = []
            for vid in plan[cls]:
                box.insert("end", f"{vid:2d}  {names.get(vid, '')}"); ids[cls].append(vid)
            for vid in native["classes"][cls]:
                if vid in removed:
                    box.insert("end", f"{vid:2d}  {names.get(vid, '')}  (removed)"); box.itemconfig("end", fg="gray"); ids[cls].append(vid)
            if keep in ids[cls]:
                box.selection_set(ids[cls].index(keep))
        packages.delete(*packages.get_children())
        for p in m.list_packages():
            packages.insert("", "end", iid=p["file"], values=("yes" if p["enabled"] else "no", p["file"], p["base"], f"{p['manufacturer']} {p['model']}"))
        status.set(f"{native['count']} records; {sum(len(v) for v in plan.values())} offered. Changes take effect after Apply.")

    def act(fn):
        def run_it():
            try:
                fn(); refresh(selected())
            except Exception as e:
                messagebox.showerror("Vehicle Manager", str(e))
        return run_it

    side = ttk.Frame(top, padding=(8, 0)); side.pack(side="right", fill="y")
    ttk.Button(side, text="Move up", command=act(lambda: m.move(selected(), -1))).pack(fill="x")
    ttk.Button(side, text="Move down", command=act(lambda: m.move(selected(), 1))).pack(fill="x")
    ttk.Button(side, text="Remove", command=act(lambda: m.remove(selected()))).pack(fill="x", pady=(8, 0))
    ttk.Button(side, text="Restore", command=act(lambda: m.restore(selected()))).pack(fill="x")
    ttk.Separator(side).pack(fill="x", pady=8)
    packages = ttk.Treeview(side, columns=("on", "file", "base", "name"), show="headings", height=8)
    for c, w in (("on", 40), ("file", 150), ("base", 90), ("name", 170)):
        packages.heading(c, text=c); packages.column(c, width=w)
    packages.pack(fill="x")

    def package_toggle():
        for name in packages.selection():
            if name in m.selection().get("packages", []):
                m.uninstall(name)
            else:
                m.install(m.packages / name)

    def package_add():
        path = filedialog.askopenfilename(filetypes=[("Vehicle package", "*.mrcar")])
        if path:
            m.install(Path(path))

    ttk.Button(side, text="Enable / disable package", command=act(package_toggle)).pack(fill="x")
    ttk.Button(side, text="Install package...", command=act(package_add)).pack(fill="x")
    ttk.Separator(side).pack(fill="x", pady=8)

    def apply():
        status.set("Applying ...")
        def work():
            try:
                result = m.apply()
                root.after(0, lambda: (status.set(f"Applied: {result['active']}"), refresh()))
            except Exception as e:
                root.after(0, lambda: (status.set("Apply failed"), messagebox.showerror("Vehicle Manager", str(e))))
        threading.Thread(target=work, daemon=True).start()

    ttk.Button(side, text="Apply to game", command=apply).pack(fill="x")
    ttk.Button(side, text="Stock game (disable roster)", command=act(lambda: messagebox.showinfo("Vehicle Manager", m.stock()))).pack(fill="x")
    labels = Path(__file__).resolve().parents[1] / "docs/vehicle-manager/presentation-fix-01.json"
    ttk.Button(side, text="Import active roster as base",
               command=act(lambda: m.import_base(force=True, names=labels if labels.is_file() else None))).pack(fill="x", pady=(8, 0))
    ttk.Label(root, textvariable=status, padding=6).pack(fill="x")
    refresh()
    root.mainloop()
