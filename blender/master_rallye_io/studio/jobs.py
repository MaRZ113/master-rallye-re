"""Long Course Studio operations in a worker thread with progress and cancel (Esc).

The worker runs only bpy-free core code. Data is taken from Blender before the
thread starts and results are applied to Blender in the modal timer (main
thread), so the interface stays responsive and undo stays consistent.
"""
from __future__ import annotations

import threading
import traceback

import bpy

_JOB = {"thread": None, "result": None, "error": None, "stage": "", "fraction": 0.0, "cancel": False,
        "on_done": None, "label": ""}


class Cancelled(Exception):
    pass


def progress(stage, fraction=None):
    if _JOB["cancel"]:
        raise Cancelled()
    _JOB["stage"] = str(stage)
    if isinstance(fraction, (int, float)):
        _JOB["fraction"] = max(0.0, min(1.0, float(fraction)))


def busy() -> bool:
    t = _JOB["thread"]
    return t is not None and t.is_alive()


def start(context, label: str, work, on_done):
    if busy():
        raise RuntimeError("another Course Studio operation is running")
    if bpy.app.background:      # headless (tests, batch builds): run in place
        _JOB.update(cancel=False, label=label)
        result = work(progress)
        text = on_done(context, result)
        if text:
            print(f"Course Studio: {text}")
        return
    _JOB.update(result=None, error=None, stage="starting", fraction=0.0, cancel=False, on_done=on_done, label=label)

    def run():
        try:
            _JOB["result"] = work(progress)
        except Cancelled:
            _JOB["error"] = "cancelled"
        except Exception as exc:   # reported in the UI
            _JOB["error"] = f"{exc}\n{traceback.format_exc(limit=6)}"
    thread = threading.Thread(target=run, daemon=True)
    _JOB["thread"] = thread
    context.scene.mr_studio.busy = label
    thread.start()
    bpy.ops.mr.job_monitor("INVOKE_DEFAULT")


class MR_OT_job_monitor(bpy.types.Operator):
    bl_idname = "mr.job_monitor"
    bl_label = "Course Studio Operation"
    bl_description = "Progress of the running Course Studio operation (Esc cancels)"
    _timer = None

    def invoke(self, context, event):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.2, window=context.window)
        wm.modal_handler_add(self)
        wm.progress_begin(0, 100)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        s = context.scene.mr_studio
        if event.type == "ESC":
            _JOB["cancel"] = True
        if event.type != "TIMER":
            return {"PASS_THROUGH"}
        s.progress = _JOB["fraction"]
        s.busy = f"{_JOB['label']}: {_JOB['stage']}"
        context.window_manager.progress_update(int(100 * _JOB["fraction"]))
        for area in context.screen.areas:
            if area.type in ("VIEW_3D", "PROPERTIES"):
                area.tag_redraw()
        if busy():
            return {"PASS_THROUGH"}
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
        s.busy = ""
        s.progress = 0.0
        if _JOB["error"]:
            message = _JOB["error"].splitlines()[0]
            self.report({"WARNING" if _JOB["error"] == "cancelled" else "ERROR"},
                        f"{_JOB['label']}: {message}")
            if _JOB["error"] != "cancelled":
                print(_JOB["error"])
            return {"CANCELLED"}
        try:
            text = _JOB["on_done"](context, _JOB["result"])
            if text:
                self.report({"INFO"}, text)
        except Exception as exc:
            traceback.print_exc()
            self.report({"ERROR"}, f"{_JOB['label']}: {exc}")
        return {"FINISHED"}


CLASSES = (MR_OT_job_monitor,)
