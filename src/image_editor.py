#!/usr/bin/env python3
"""burglekutt tile image editor entry point."""

import tkinter as tk
from tkinter import filedialog, messagebox

import shortcuts
from image_editor_window import ImageEditorWindow
from project import Project
from project_io import load_project, save_project


class ImageEditorApp:
    def __init__(self):
        self.project = Project()
        self.project_path = None
        self.root = tk.Tk()
        self.root.withdraw()
        self._editors = []
        self.image_editor = None

        self.open_or_focus_image_editor()
        shortcuts.bind_file_shortcuts(self.root, self)

    def _window_alive(self, editor):
        if editor is None:
            return False
        try:
            return bool(editor.root.winfo_exists())
        except tk.TclError:
            return False

    def open_or_focus_image_editor(self):
        if not self._window_alive(self.image_editor):
            window = tk.Toplevel(self.root)
            self.image_editor = ImageEditorWindow(window, self.project, self)
            self._editors.append(self.image_editor)
        self.image_editor.focus()

    def request_close(self, editor):
        editor.shutdown()
        try:
            editor.root.destroy()
        except tk.TclError:
            pass
        if editor in self._editors:
            self._editors.remove(editor)
        if editor is self.image_editor:
            self.image_editor = None
        if not self._editors:
            self.root.quit()

    def exit_all(self):
        shortcuts.unbind_app_shortcuts(self.root)
        for editor in list(self._editors):
            editor.shutdown()
            try:
                editor.root.destroy()
            except tk.TclError:
                pass
        self._editors.clear()
        self.image_editor = None
        self.root.quit()

    def new_project(self):
        if not messagebox.askyesno(
            "New Project",
            "Discard the current project and start a new one?",
            parent=self.root,
        ):
            return
        self.project.reset()
        self.project_path = None
        self._update_titles()

    def load_project_dialog(self):
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Load Project",
            filetypes=[("burglekutt project", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            data = load_project(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Load Project", str(exc), parent=self.root)
            return
        self.project.load_from_dict(data)
        self.project_path = path
        self._update_titles()

    def save_project_dialog(self):
        path = self.project_path
        if not path:
            path = filedialog.asksaveasfilename(
                parent=self.root,
                title="Save Project",
                defaultextension=".json",
                filetypes=[("burglekutt project", "*.json"), ("All", "*.*")],
            )
            if not path:
                return
        try:
            save_project(path, self.project)
        except OSError as exc:
            messagebox.showerror("Save Project", str(exc), parent=self.root)
            return
        self.project_path = path
        self._update_titles()

    def _update_titles(self):
        suffix = ""
        if self.project_path:
            suffix = " — {}".format(self.project_path)
        for editor in self._editors:
            base = editor.root.title().split(" — ")[0]
            editor.root.title(base + suffix)

    def run(self):
        self.root.mainloop()


def main():
    ImageEditorApp().run()


if __name__ == "__main__":
    main()
