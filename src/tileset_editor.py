"""Tileset editor window."""

import tkinter as tk
from tkinter import messagebox, ttk

import theme
from project import ChangeEvent
from tile_canvas import TILE_PIXEL_SCALE_MIN, TileCanvas


class TilesetEditorWindow:
    def __init__(self, root, project):
        self.root = root
        self.project = project
        self.root.title("burglekutt — Tileset")
        min_canvas = 8 * TILE_PIXEL_SCALE_MIN
        self.root.minsize(min_canvas + 40, min_canvas + 100)

        self._window_bg = theme.TILESET_WINDOW_BG
        theme.apply_window_theme(self.root, self._window_bg)

        self._main_frame = tk.Frame(self.root, bg=self._window_bg)
        theme.register_frame(self._main_frame)
        self._main_frame.pack(fill=tk.BOTH, expand=True)

        self._build_menus()
        self._build_layout()
        self._build_status_bar()
        theme.apply_window_theme(self.root, self._window_bg)

        self.project.add_listener(self._on_project_change)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._update_status()

    def _build_menus(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._not_implemented)
        file_menu.add_command(label="Load Project", command=self._not_implemented)
        file_menu.add_command(label="Save Project", command=self._not_implemented)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)

        window_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Window", menu=window_menu)
        window_menu.add_command(label="Tileset", command=self._focus_window)
        window_menu.add_command(
            label="Metatile (Phase 4)",
            state=tk.DISABLED,
        )
        window_menu.add_command(
            label="Supertile (Phase 5)",
            state=tk.DISABLED,
        )

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _build_layout(self):
        content = tk.Frame(self._main_frame, bg=self._window_bg)
        theme.register_frame(content)
        content.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Reserved for Phase 2 palette sidebar
        self._left_placeholder = tk.Frame(content, width=1, bg=self._window_bg)
        theme.register_frame(self._left_placeholder)

        center = tk.Frame(content, bg=self._window_bg)
        theme.register_frame(center)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tile_canvas = TileCanvas(center, self.project, window_bg=self._window_bg)
        self.tile_canvas.pack()
        self.tile_canvas.refresh()

        # Reserved for Phase 3 tile picker controls
        self._right_placeholder = tk.Frame(content, width=1, bg=self._window_bg)
        theme.register_frame(self._right_placeholder)

    def _build_status_bar(self):
        status_frame = tk.Frame(self._main_frame, bg=self._window_bg)
        theme.register_frame(status_frame)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 6))

        self._status_label = ttk.Label(status_frame, anchor=tk.W)
        self._status_label.pack(fill=tk.X)

    def _update_status(self):
        tile = self.project.get_active_tile()
        index = self.project.active_tile_index
        self._status_label.config(text=f"Tile {index} / {tile['name']}")

    def _on_project_change(self, event):
        if event.kind == ChangeEvent.TILE_CHANGED:
            self.tile_canvas.refresh()
            self._update_status()

    def _focus_window(self):
        self.root.lift()
        self.root.focus_force()

    def _not_implemented(self, event=None):
        messagebox.showinfo("Not implemented", "Available in a later phase.")

    def _show_about(self, event=None):
        messagebox.showinfo(
            "About burglekutt",
            "burglekutt — TI-99 tile editor\nPhase 1: tileset canvas shell",
        )

    def _on_close(self, event=None):
        self.project.remove_listener(self._on_project_change)
        self.root.quit()
        self.root.destroy()