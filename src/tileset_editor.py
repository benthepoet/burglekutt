"""Tileset editor window."""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import theme
from palette import TI_COLORS, PalettePopup
from project import ChangeEvent
from tile_canvas import TILE_PIXEL_SCALE_MIN, TileCanvas
from tile_model import copy_tile
from tile_picker import TilePickerWindow
from undo_stack import UndoStack


class TilesetEditorWindow:
    def __init__(self, root, project, coordinator=None):
        self.root = root
        self.project = project
        self.coordinator = coordinator
        self.undo_stack = UndoStack(max_size=10)
        self._color_target_row = None
        self._color_target_channel = None
        self._palette_popup = None
        self._tile_picker = None
        self._assign_picker = None
        self._stroke_dirty = False
        self._skip_tile_refresh = False

        self.root.title("burglekutt — Tileset")
        min_canvas = 8 * TILE_PIXEL_SCALE_MIN
        self.root.minsize(min_canvas + 200, min_canvas + 120)

        self._window_bg = theme.TILESET_WINDOW_BG
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
        self._update_edit_menu_state()
        self._update_tile_sidebar()

    def _build_menus(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._not_implemented)
        file_menu.add_command(label="Load Project", command=self._not_implemented)
        file_menu.add_command(label="Save Project", command=self._not_implemented)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._exit_app)

        self._edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=self._edit_menu)
        self._edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self._undo)
        self._edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self._redo)
        self._edit_menu.add_separator()
        self._edit_menu.add_command(label="Clear Tile", command=self._clear_tile)
        self._edit_menu.add_command(label="Duplicate to…", command=self._duplicate_tile)

        tiles_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tiles", menu=tiles_menu)
        tiles_menu.add_command(label="Select Tile…", command=self._open_tile_picker)

        window_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Window", menu=window_menu)
        window_menu.add_command(label="Tileset", command=self.focus)
        window_menu.add_command(label="Tile Picker", command=self._open_tile_picker)
        window_menu.add_command(label="Metatile", command=self._focus_metatile)
        window_menu.add_command(label="Supertile", command=self._focus_supertile)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _build_layout(self):
        content = tk.Frame(self._main_frame, bg=self._window_bg)
        theme.register_frame(content, self.root, self._window_bg)
        content.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        center = tk.Frame(content, bg=self._window_bg)
        theme.register_frame(center, self.root, self._window_bg)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tile_canvas = TileCanvas(
            center,
            self.project,
            window_bg=self._window_bg,
            root=self.root,
        )
        self.tile_canvas.pack()
        self.tile_canvas.on_swatch_select(self._on_swatch_select)
        self.tile_canvas.on_pixel_change(self._on_pixel_change)
        self.tile_canvas.on_stroke_end(self._on_stroke_end)

        sidebar = ttk.Labelframe(content, text="Tile", padding=8)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0))

        self._tile_index_label = ttk.Label(sidebar, text="Index: 0")
        self._tile_index_label.pack(anchor=tk.W, pady=(0, 4))

        self._tile_name_label = ttk.Label(sidebar, text="Name: TIL00")
        self._tile_name_label.pack(anchor=tk.W, pady=(0, 8))

        ttk.Button(sidebar, text="Select Tile…", command=self._open_tile_picker).pack(
            fill=tk.X,
            pady=(0, 4),
        )
        ttk.Button(sidebar, text="Rename…", command=self._rename_tile).pack(
            fill=tk.X,
            pady=(0, 4),
        )
        ttk.Button(sidebar, text="Duplicate to…", command=self._duplicate_tile).pack(
            fill=tk.X,
        )

    def _build_status_bar(self):
        status_frame = tk.Frame(self._main_frame, bg=self._window_bg)
        theme.register_frame(status_frame, self.root, self._window_bg)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 6))

        self._status_label = ttk.Label(status_frame, anchor=tk.W)
        self._status_label.pack(fill=tk.X)

    def _bind_shortcuts(self):
        self.root.bind_all("<Control-z>", self._undo)
        self.root.bind_all("<Control-y>", self._redo)
        self.root.bind_all("<Control-Z>", self._redo)

    def _push_undo_snapshot(self):
        self.undo_stack.push(copy_tile(self.project.get_active_tile()))

    def _open_tile_picker(self, event=None):
        if self._assign_picker is not None:
            self._assign_picker.focus()
            return
        if self._tile_picker is None:
            self._tile_picker = TilePickerWindow(
                self.root,
                self.project,
                mode="edit",
                on_close=self._on_tile_picker_closed,
            )
        self._tile_picker.focus()

    def _on_tile_picker_closed(self):
        self._tile_picker = None

    def _duplicate_tile(self, event=None):
        if self._assign_picker is not None:
            self._assign_picker.focus()
            return

        def on_destination_selected(dst_index):
            self._assign_picker = None
            if dst_index == self.project.active_tile_index:
                return
            self.project.duplicate_tile(self.project.active_tile_index, dst_index)
            self.project.set_active_tile_index(dst_index)

        self._assign_picker = TilePickerWindow(
            self.root,
            self.project,
            mode="assign",
            title="Duplicate to Tile",
            on_select=on_destination_selected,
            on_close=self._on_assign_picker_closed,
        )
        self._assign_picker.focus()

    def _on_assign_picker_closed(self):
        self._assign_picker = None

    def _rename_tile(self, event=None):
        tile = self.project.get_active_tile()
        new_name = simpledialog.askstring(
            "Rename Tile",
            "Tile name:",
            initialvalue=tile["name"],
            parent=self.root,
        )
        if new_name is None:
            return
        try:
            self.project.rename_tile(self.project.active_tile_index, new_name)
        except ValueError as exc:
            messagebox.showerror("Rename Tile", str(exc), parent=self.root)
            return
        self._update_tile_sidebar()

    def _on_pixel_change(self, row, col, bit, is_stroke_start):
        if is_stroke_start:
            self._push_undo_snapshot()
            self._stroke_dirty = False
        if self.project.set_pixel(row, col, bit, notify=False):
            self._stroke_dirty = True
            self.tile_canvas.update_pixel(row, col)
        self._update_edit_menu_state()

    def _on_stroke_end(self, _event=None):
        if self._stroke_dirty:
            self._skip_tile_refresh = True
            self.project.notify_active_tile_changed()
            self._stroke_dirty = False

    def _close_palette_popup(self):
        if self._palette_popup is not None:
            self._palette_popup.close()
            self._palette_popup = None

    def _on_swatch_select(self, row, channel, x_root=None, y_root=None):
        self._color_target_row = row
        self._color_target_channel = channel
        self.tile_canvas.set_active_target(row, channel)
        self._close_palette_popup()
        self._palette_popup = PalettePopup(
            self.root,
            row,
            channel,
            self._on_palette_color_pick,
            on_close=self._on_palette_closed,
            x_root=x_root,
            y_root=y_root,
        )
        self._update_status()

    def _on_palette_closed(self):
        self._palette_popup = None
        theme.apply_window_theme(self.root, self._window_bg)
        self.tile_canvas.refresh()

    def _on_palette_color_pick(self, color_index):
        if self._color_target_row is None or self._color_target_channel is None:
            return
        self._push_undo_snapshot()
        kwargs = {self._color_target_channel: color_index}
        self.project.set_row_color(self._color_target_row, **kwargs)
        self.tile_canvas.suppress_next_stroke()
        self._update_edit_menu_state()
        self._update_status(color_index=color_index)

    def _undo(self, event=None):
        snapshot = self.undo_stack.undo(copy_tile(self.project.get_active_tile()))
        if snapshot is None:
            return
        self.project.replace_active_tile(snapshot)
        self._update_edit_menu_state()

    def _redo(self, event=None):
        snapshot = self.undo_stack.redo(copy_tile(self.project.get_active_tile()))
        if snapshot is None:
            return
        self.project.replace_active_tile(snapshot)
        self._update_edit_menu_state()

    def _clear_tile(self, event=None):
        self._push_undo_snapshot()
        self.project.clear_active_tile(reset_colors=False)
        self._update_edit_menu_state()

    def _update_edit_menu_state(self):
        undo_state = tk.NORMAL if self.undo_stack.can_undo() else tk.DISABLED
        redo_state = tk.NORMAL if self.undo_stack.can_redo() else tk.DISABLED
        self._edit_menu.entryconfig(0, state=undo_state)
        self._edit_menu.entryconfig(1, state=redo_state)

    def _update_tile_sidebar(self):
        tile = self.project.get_active_tile()
        index = self.project.active_tile_index
        self._tile_index_label.config(text="Index: {}".format(index))
        self._tile_name_label.config(text="Name: {}".format(tile["name"]))

    def _update_status(self, color_index=None):
        tile = self.project.get_active_tile()
        index = self.project.active_tile_index
        parts = ["Tile {} / {}".format(index, tile["name"])]

        if self._color_target_row is not None and self._color_target_channel is not None:
            channel_label = "fg" if self._color_target_channel == "fg" else "bg"
            parts.append("Row {} {}".format(self._color_target_row, channel_label))
            if color_index is not None:
                parts.append("Color {} ({})".format(color_index, TI_COLORS[color_index]))
        else:
            parts.append("Select a row fg/bg swatch")

        self._status_label.config(text="  |  ".join(parts))

    def _on_project_change(self, event):
        if event.kind == ChangeEvent.ACTIVE_TILE_CHANGED:
            self.undo_stack.clear()
            self.tile_canvas.refresh()
            self._update_tile_sidebar()
            self._update_status()
            self._update_edit_menu_state()
        elif event.kind == ChangeEvent.TILE_CHANGED:
            if event.index == self.project.active_tile_index:
                if self._skip_tile_refresh:
                    self._skip_tile_refresh = False
                else:
                    self.tile_canvas.refresh()
                if self._color_target_row is not None and self._color_target_channel is not None:
                    self.tile_canvas.set_active_target(
                        self._color_target_row,
                        self._color_target_channel,
                    )
            self._update_tile_sidebar()
            self._update_status()

    def shutdown(self):
        self._close_palette_popup()
        if self._tile_picker is not None:
            self._tile_picker.close()
            self._tile_picker = None
        if self._assign_picker is not None:
            self._assign_picker.close()
            self._assign_picker = None
        self.project.remove_listener(self._on_project_change)

    def focus(self):
        self.root.lift()
        self.root.focus_force()
        theme.apply_window_theme(self.root, self._window_bg)

    def _on_focus(self, _event=None):
        theme.apply_window_theme(self.root, self._window_bg)

    def _focus_metatile(self):
        if self.coordinator is not None:
            self.coordinator.focus_metatile()

    def _focus_supertile(self):
        if self.coordinator is not None:
            self.coordinator.focus_supertile()

    def _exit_app(self, _event=None):
        if self.coordinator is not None:
            self.coordinator.exit_all()
        else:
            self._on_close()

    def _not_implemented(self, event=None):
        messagebox.showinfo("Not implemented", "Available in a later phase.")

    def _show_about(self, event=None):
        messagebox.showinfo(
            "About burglekutt",
            "burglekutt — TI-99 tile editor\nPhase 5: supertile editor",
        )

    def _on_close(self, event=None):
        if self.coordinator is not None:
            self.coordinator.request_close(self)
        else:
            self.shutdown()
            self.root.destroy()