"""Tile image editor window (Phase 1 shell)."""

import tkinter as tk
from tkinter import messagebox, ttk

import shortcuts
import theme
from project import ChangeEvent


class ImageEditorWindow:
    def __init__(self, root, project, coordinator=None):
        self.root = root
        self.project = project
        self.coordinator = coordinator

        self.root.title("burglekutt — Tile Image")
        self.root.minsize(480, 280)

        self._window_bg = theme.IMAGE_EDITOR_WINDOW_BG
        self._styles = theme.window_styles(self._window_bg)
        theme.apply_window_theme(self.root, self._window_bg)

        self._main_frame = tk.Frame(self.root, bg=self._window_bg)
        theme.register_frame(self._main_frame, self.root, self._window_bg)
        self._main_frame.pack(fill=tk.BOTH, expand=True)

        self._build_menus()
        self._build_layout()
        self._build_status_bar()
        theme.apply_window_theme(self.root, self._window_bg)

        self.project.add_listener(self._on_project_change)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<FocusIn>", self._on_focus)
        self._bind_shortcuts()

        self._update_status()

    def _build_menus(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="New",
            accelerator="Ctrl+N",
            command=self._new_project,
        )
        file_menu.add_command(
            label="Load Project",
            accelerator="Ctrl+O",
            command=self._load_project,
        )
        file_menu.add_command(
            label="Save Project",
            accelerator="Ctrl+S",
            command=self._save_project,
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit",
            accelerator="Ctrl+Q",
            command=self._exit_app,
        )

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(
            label="Keyboard Shortcuts…",
            command=self._show_shortcuts,
        )
        help_menu.add_command(label="About", command=self._show_about)

    def _build_layout(self):
        content = tk.Frame(self._main_frame, bg=self._window_bg)
        theme.register_frame(content, self.root, self._window_bg)
        content.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        panel = ttk.Labelframe(
            content,
            text="Image",
            padding=8,
            style=self._styles.labelframe,
        )
        panel.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            panel,
            text="Tile image grid will appear here.",
            style=self._styles.label,
        ).pack(anchor=tk.W)

    def _build_status_bar(self):
        status_frame = tk.Frame(self._main_frame, bg=self._window_bg)
        theme.register_frame(status_frame, self.root, self._window_bg)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 6))

        self._status_label = ttk.Label(
            status_frame,
            anchor=tk.W,
            style=self._styles.label,
        )
        self._status_label.pack(fill=tk.X)

    def _bind_shortcuts(self):
        shortcuts.bind_common(self.root, self.coordinator)

    def _update_status(self):
        self._status_label.configure(text="No tile image")

    def _on_project_change(self, event):
        if event.kind == ChangeEvent.PROJECT_LOADED:
            self._update_status()

    def shutdown(self):
        self.project.remove_listener(self._on_project_change)

    def focus(self):
        self.root.lift()
        self.root.focus_force()
        theme.apply_window_theme(self.root, self._window_bg)

    def _on_focus(self, _event=None):
        theme.apply_window_theme(self.root, self._window_bg)

    def _exit_app(self, _event=None):
        if self.coordinator is not None:
            self.coordinator.exit_all()
        else:
            self._on_close()

    def _new_project(self, _event=None):
        if self.coordinator is not None:
            self.coordinator.new_project()

    def _load_project(self, _event=None):
        if self.coordinator is not None:
            self.coordinator.load_project_dialog()

    def _save_project(self, _event=None):
        if self.coordinator is not None:
            self.coordinator.save_project_dialog()

    def _show_shortcuts(self, _event=None):
        shortcuts.show_shortcuts_help(self.root, shortcuts.COMMON_HELP.strip())

    def _show_about(self, _event=None):
        messagebox.showinfo(
            "About burglekutt",
            "burglekutt — TI-99 tile image editor\nPhase 1: shell",
        )

    def _on_close(self, _event=None):
        if self.coordinator is not None:
            self.coordinator.request_close(self)
        else:
            self.shutdown()
            self.root.destroy()
