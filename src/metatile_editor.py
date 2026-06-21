"""Metatile editor window."""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import theme
from composite import resolve_metatile_pixels, resolve_tile_pixels, tile_is_empty
from project import ChangeEvent
from tile_model import (
    METATILE_FLAG_DOOR,
    METATILE_FLAG_HURT,
    METATILE_FLAG_SOLID,
    METATILE_FLAG_STAIRS,
    METATILE_FLAG_WATER,
    flags_has,
    flags_summary,
)
from tile_picker import PICKER_CELL_PLACEHOLDER, PICKER_TILE_SCALE_DEFAULT, TilePickerWindow

METATILE_PIXEL_SCALE_DEFAULT = 8
METATILE_SIZE = 16
CELL_THUMB_SCALE = PICKER_TILE_SCALE_DEFAULT
CELL_THUMB_SIZE = 8 * CELL_THUMB_SCALE
CELL_GAP = 4


class MetatileEditorWindow:
    def __init__(self, root, project, coordinator=None):
        self.root = root
        self.project = project
        self.coordinator = coordinator
        self._assign_picker = None
        self._flag_vars = {}

        self.root.title("burglekutt — Metatile")
        self.root.minsize(720, 420)

        self._window_bg = theme.METATILE_WINDOW_BG
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

        self._refresh_metatile_list()
        self._refresh_active_metatile()

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

        window_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Window", menu=window_menu)
        window_menu.add_command(label="Tileset", command=self._focus_tileset)
        window_menu.add_command(label="Metatile", command=self._focus_metatile)
        window_menu.add_command(
            label="Supertile (Phase 5)",
            state=tk.DISABLED,
        )

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _build_layout(self):
        content = tk.Frame(self._main_frame, bg=self._window_bg)
        theme.register_frame(content, self.root, self._window_bg)
        content.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left = ttk.Labelframe(content, text="Metatiles", padding=8)
        left.pack(side=tk.LEFT, fill=tk.Y)

        self._metatile_list = tk.Listbox(left, width=18, height=16)
        self._metatile_list.pack(fill=tk.BOTH, expand=True)
        self._metatile_list.bind("<<ListboxSelect>>", self._on_list_select)

        buttons = ttk.Frame(left)
        buttons.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(buttons, text="Add", command=self._add_metatile).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(buttons, text="Remove", command=self._remove_metatile).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(buttons, text="Rename…", command=self._rename_metatile).pack(side=tk.LEFT)

        flags_frame = ttk.Labelframe(left, text="Flags", padding=8)
        flags_frame.pack(fill=tk.X, pady=(8, 0))
        flag_defs = (
            (METATILE_FLAG_SOLID, "Solid"),
            (METATILE_FLAG_HURT, "Hurt"),
            (METATILE_FLAG_WATER, "Water"),
            (METATILE_FLAG_DOOR, "Door"),
            (METATILE_FLAG_STAIRS, "Stairs"),
        )
        for mask, label in flag_defs:
            var = tk.BooleanVar(value=False)
            self._flag_vars[mask] = var
            ttk.Checkbutton(
                flags_frame,
                text=label,
                variable=var,
                command=lambda m=mask: self._on_flag_toggle(m),
            ).pack(anchor=tk.W)

        center = tk.Frame(content, bg=self._window_bg)
        theme.register_frame(center, self.root, self._window_bg)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        composite_size = METATILE_SIZE * METATILE_PIXEL_SCALE_DEFAULT
        self._composite_canvas = tk.Canvas(
            center,
            width=composite_size,
            height=composite_size,
            bg=theme.CANVAS_BG,
            highlightthickness=0,
        )
        self._composite_canvas.pack()

        right = ttk.Labelframe(content, text="Cells", padding=8)
        right.pack(side=tk.LEFT, fill=tk.Y)

        self._cell_grid = tk.Frame(right, bg=self._window_bg)
        theme.register_frame(self._cell_grid, self.root, self._window_bg)
        self._cell_grid.pack()
        self._cell_widgets = []
        for row in range(2):
            row_frame = tk.Frame(self._cell_grid, bg=self._window_bg)
            theme.register_frame(row_frame, self.root, self._window_bg)
            row_frame.pack()
            for col in range(2):
                cell_index = row * 2 + col
                cell = tk.Canvas(
                    row_frame,
                    width=CELL_THUMB_SIZE,
                    height=CELL_THUMB_SIZE,
                    bg=theme.CANVAS_BG,
                    highlightthickness=1,
                    highlightbackground=theme.CANVAS_GRID_OUTLINE,
                    cursor="hand2",
                )
                cell.grid(row=row, column=col, padx=CELL_GAP // 2, pady=CELL_GAP // 2)
                cell.bind(
                    "<ButtonRelease-1>",
                    lambda _event, index=cell_index: self._on_cell_click(index),
                )
                self._cell_widgets.append(cell)

    def _build_status_bar(self):
        status_frame = tk.Frame(self._main_frame, bg=self._window_bg)
        theme.register_frame(status_frame, self.root, self._window_bg)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 6))

        self._status_label = ttk.Label(status_frame, anchor=tk.W)
        self._status_label.pack(fill=tk.X)

    def shutdown(self):
        self._close_assign_picker()
        self.project.remove_listener(self._on_project_change)

    def focus(self):
        self.root.lift()
        self.root.focus_force()
        theme.apply_window_theme(self.root, self._window_bg)

    def _on_focus(self, _event=None):
        theme.apply_window_theme(self.root, self._window_bg)

    def _focus_tileset(self):
        if self.coordinator is not None:
            self.coordinator.open_or_focus_tileset()

    def _focus_metatile(self):
        if self.coordinator is not None:
            self.coordinator.open_or_focus_metatile()
        else:
            self.focus()

    def _exit_app(self, _event=None):
        if self.coordinator is not None:
            self.coordinator.exit_all()
        else:
            self._on_close()

    def _not_implemented(self, _event=None):
        messagebox.showinfo("Not implemented", "Available in a later phase.")

    def _show_about(self, _event=None):
        messagebox.showinfo(
            "About burglekutt",
            "burglekutt — TI-99 tile editor\nPhase 4: metatile editor",
        )

    def _on_close(self, _event=None):
        if self.coordinator is not None:
            self.coordinator.request_close(self)
        else:
            self.shutdown()
            self.root.destroy()

    def _add_metatile(self):
        try:
            self.project.add_metatile()
        except ValueError as exc:
            messagebox.showerror("Add Metatile", str(exc), parent=self.root)

    def _remove_metatile(self):
        if not self.project.metatiles:
            return
        index = self.project.active_metatile_index
        refs = self.project.supertiles_referencing_metatile(index)
        if refs:
            messagebox.showwarning(
                "Remove Metatile",
                "Supertile(s) still reference metatile {}.".format(index),
                parent=self.root,
            )
            return
        if not messagebox.askyesno(
            "Remove Metatile",
            "Remove metatile {}?".format(index),
            parent=self.root,
        ):
            return
        self.project.remove_metatile(index)

    def _rename_metatile(self):
        if not self.project.metatiles:
            return
        metatile = self.project.get_active_metatile()
        new_name = simpledialog.askstring(
            "Rename Metatile",
            "Metatile name:",
            initialvalue=metatile["name"],
            parent=self.root,
        )
        if new_name is None:
            return
        try:
            self.project.rename_metatile(self.project.active_metatile_index, new_name)
        except ValueError as exc:
            messagebox.showerror("Rename Metatile", str(exc), parent=self.root)

    def _on_list_select(self, _event=None):
        selection = self._metatile_list.curselection()
        if not selection:
            return
        self.project.set_active_metatile_index(selection[0])

    def _on_flag_toggle(self, mask):
        if not self.project.metatiles:
            return
        index = self.project.active_metatile_index
        enabled = self._flag_vars[mask].get()
        self.project.set_metatile_flag(index, mask, enabled)

    def _close_assign_picker(self):
        if self._assign_picker is not None:
            self._assign_picker.close()
            self._assign_picker = None

    def _on_cell_click(self, cell_index):
        if not self.project.metatiles:
            return
        if self._assign_picker is not None:
            self._assign_picker.focus()
            return

        meta_index = self.project.active_metatile_index

        def on_tile_selected(tile_index):
            self._assign_picker = None
            self.project.set_metatile_cell(meta_index, cell_index, tile_index)

        self._assign_picker = TilePickerWindow(
            self.root,
            self.project,
            mode="assign",
            title="Select Tile for Cell",
            on_select=on_tile_selected,
            on_close=self._on_assign_picker_closed,
        )
        self._assign_picker.focus()

    def _on_assign_picker_closed(self):
        self._assign_picker = None

    def _refresh_metatile_list(self):
        self._metatile_list.delete(0, tk.END)
        for index, metatile in enumerate(self.project.metatiles):
            summary = flags_summary(metatile["flags"])
            suffix = " [{}]".format(summary) if summary else ""
            self._metatile_list.insert(tk.END, "{}{}".format(metatile["name"], suffix))
        if self.project.metatiles:
            self._metatile_list.selection_clear(0, tk.END)
            self._metatile_list.selection_set(self.project.active_metatile_index)
            self._metatile_list.activate(self.project.active_metatile_index)

    def _refresh_flags(self):
        if not self.project.metatiles:
            for var in self._flag_vars.values():
                var.set(False)
            return
        flags = self.project.get_active_metatile()["flags"]
        for mask, var in self._flag_vars.items():
            var.set(flags_has(flags, mask))

    def _draw_tile_thumbnail(self, canvas, tile):
        canvas.delete("all")
        size = CELL_THUMB_SIZE
        if tile_is_empty(tile):
            canvas.create_rectangle(0, 0, size, size, fill=theme.CANVAS_BG, outline="")
            inset = max(1, CELL_THUMB_SCALE)
            canvas.create_rectangle(
                inset,
                inset,
                size - inset,
                size - inset,
                fill=PICKER_CELL_PLACEHOLDER,
                outline="",
            )
            return
        pixels = resolve_tile_pixels(tile)
        for row in range(8):
            for col in range(8):
                x0 = col * CELL_THUMB_SCALE
                y0 = row * CELL_THUMB_SCALE
                x1 = x0 + CELL_THUMB_SCALE
                y1 = y0 + CELL_THUMB_SCALE
                canvas.create_rectangle(
                    x0,
                    y0,
                    x1,
                    y1,
                    fill=pixels[row][col],
                    outline="",
                )

    def _refresh_cells(self):
        if not self.project.metatiles:
            for canvas in self._cell_widgets:
                canvas.delete("all")
            return
        metatile = self.project.get_active_metatile()
        for cell_index, canvas in enumerate(self._cell_widgets):
            tile = self.project.get_tile(metatile["cells"][cell_index])
            self._draw_tile_thumbnail(canvas, tile)

    def _refresh_composite(self):
        self._composite_canvas.delete("all")
        if not self.project.metatiles:
            return
        metatile = self.project.get_active_metatile()
        pixels = resolve_metatile_pixels(metatile, self.project.tiles)
        scale = METATILE_PIXEL_SCALE_DEFAULT
        for row in range(METATILE_SIZE):
            for col in range(METATILE_SIZE):
                x0 = col * scale
                y0 = row * scale
                x1 = x0 + scale
                y1 = y0 + scale
                self._composite_canvas.create_rectangle(
                    x0,
                    y0,
                    x1,
                    y1,
                    fill=pixels[row][col],
                    outline="",
                )
        for i in range(3):
            pos = i * 8 * scale
            size = METATILE_SIZE * scale
            self._composite_canvas.create_line(
                pos, 0, pos, size - 1, fill=theme.CANVAS_GRID_OUTLINE
            )
            self._composite_canvas.create_line(
                0, pos, size - 1, pos, fill=theme.CANVAS_GRID_OUTLINE
            )
        size = METATILE_SIZE * scale
        self._composite_canvas.create_line(
            size - 1, 0, size - 1, size - 1, fill=theme.CANVAS_GRID_OUTLINE
        )
        self._composite_canvas.create_line(
            0, size - 1, size - 1, size - 1, fill=theme.CANVAS_GRID_OUTLINE
        )

    def _refresh_active_metatile(self):
        self._refresh_flags()
        self._refresh_cells()
        self._refresh_composite()
        self._update_status()

    def _update_status(self):
        if not self.project.metatiles:
            self._status_label.config(text="No metatiles")
            return
        metatile = self.project.get_active_metatile()
        index = self.project.active_metatile_index
        summary = flags_summary(metatile["flags"])
        parts = ["Metatile {} / {}".format(index, metatile["name"])]
        if summary:
            parts.append("Flags {}".format(summary))
        self._status_label.config(text="  |  ".join(parts))

    def _on_project_change(self, event):
        if event.kind == ChangeEvent.TILE_CHANGED:
            if self.project.metatiles:
                self._refresh_cells()
                self._refresh_composite()
        elif event.kind == ChangeEvent.METATILE_CHANGED:
            self._refresh_metatile_list()
            if event.index == self.project.active_metatile_index:
                self._refresh_active_metatile()
            else:
                self._update_status()
        elif event.kind == ChangeEvent.ACTIVE_METATILE_CHANGED:
            self._refresh_metatile_list()
            self._refresh_active_metatile()