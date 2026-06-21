"""Supertile editor window."""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import theme
from composite import (
    metatile_references_tile,
    resolve_metatile_pixels,
    resolve_supertile_pixels,
)
from metatile_picker import PICKER_METATILE_SCALE_DEFAULT, MetatilePickerWindow
from pixel_canvas import draw_pixel_grid
from project import ChangeEvent
from tile_model import (
    METATILE_PIXEL_SIZE,
    SUPERTILE_COLS,
    SUPERTILE_PIXEL_HEIGHT,
    SUPERTILE_PIXEL_WIDTH,
    SUPERTILE_ROWS,
)

SUPERTILE_PIXEL_SCALE_DEFAULT = 2
CELL_THUMB_SCALE = PICKER_METATILE_SCALE_DEFAULT
CELL_THUMB_SIZE = METATILE_PIXEL_SIZE * CELL_THUMB_SCALE
CELL_GAP = 4


class SupertileEditorWindow:
    def __init__(self, root, project, coordinator=None):
        self.root = root
        self.project = project
        self.coordinator = coordinator
        self._assign_picker = None

        self.root.title("burglekutt — Supertile")
        self.root.minsize(820, 480)

        self._window_bg = theme.SUPERTILE_WINDOW_BG
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

        self._refresh_supertile_list()
        self._refresh_active_supertile()

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
        window_menu.add_command(label="Supertile", command=self._focus_supertile)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _build_layout(self):
        content = tk.Frame(self._main_frame, bg=self._window_bg)
        theme.register_frame(content, self.root, self._window_bg)
        content.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left = ttk.Labelframe(
            content,
            text="Supertiles",
            padding=8,
            style=self._styles.labelframe,
        )
        left.pack(side=tk.LEFT, fill=tk.Y)

        list_frame = ttk.Frame(left, style=self._styles.frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        list_scroll = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            style=self._styles.scrollbar,
        )
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._supertile_list = tk.Listbox(
            list_frame,
            width=18,
            height=16,
            yscrollcommand=list_scroll.set,
        )
        self._supertile_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self._supertile_list.yview)
        self._supertile_list.bind("<<ListboxSelect>>", self._on_list_select)

        buttons = ttk.Frame(left, style=self._styles.frame)
        buttons.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(
            buttons,
            text="Add",
            command=self._add_supertile,
            style=self._styles.button,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            buttons,
            text="Remove",
            command=self._remove_supertile,
            style=self._styles.button,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            buttons,
            text="Rename…",
            command=self._rename_supertile,
            style=self._styles.button,
        ).pack(side=tk.LEFT)

        center = tk.Frame(content, bg=self._window_bg)
        theme.register_frame(center, self.root, self._window_bg)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        composite_size = (
            SUPERTILE_PIXEL_WIDTH * SUPERTILE_PIXEL_SCALE_DEFAULT
        )
        self._composite_canvas = tk.Canvas(
            center,
            width=composite_size,
            height=SUPERTILE_PIXEL_HEIGHT * SUPERTILE_PIXEL_SCALE_DEFAULT,
            bg=theme.CANVAS_BG,
            highlightthickness=0,
        )
        self._composite_canvas.pack()

        right = ttk.Labelframe(
            content,
            text="Cells",
            padding=8,
            style=self._styles.labelframe,
        )
        right.pack(side=tk.LEFT, fill=tk.Y)

        self._cell_grid = tk.Frame(right, bg=self._window_bg)
        theme.register_frame(self._cell_grid, self.root, self._window_bg)
        self._cell_grid.pack()
        self._cell_widgets = []
        for row in range(SUPERTILE_ROWS):
            row_frame = tk.Frame(self._cell_grid, bg=self._window_bg)
            theme.register_frame(row_frame, self.root, self._window_bg)
            row_frame.pack()
            for col in range(SUPERTILE_COLS):
                cell_index = row * SUPERTILE_COLS + col
                cell = tk.Canvas(
                    row_frame,
                    width=CELL_THUMB_SIZE,
                    height=CELL_THUMB_SIZE,
                    bg=theme.CANVAS_BG,
                    highlightthickness=1,
                    highlightbackground=theme.CANVAS_GRID_OUTLINE,
                    cursor="hand2",
                )
                cell.grid(
                    row=row,
                    column=col,
                    padx=CELL_GAP // 2,
                    pady=CELL_GAP // 2,
                )
                cell.bind(
                    "<ButtonRelease-1>",
                    lambda _event, index=cell_index: self._on_cell_click(index),
                )
                self._cell_widgets.append(cell)

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

    def _focus_supertile(self):
        if self.coordinator is not None:
            self.coordinator.open_or_focus_supertile()
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
            "burglekutt — TI-99 tile editor\nPhase 5: supertile editor",
        )

    def _on_close(self, _event=None):
        if self.coordinator is not None:
            self.coordinator.request_close(self)
        else:
            self.shutdown()
            self.root.destroy()

    def _add_supertile(self):
        try:
            self.project.add_supertile()
        except ValueError as exc:
            messagebox.showerror("Add Supertile", str(exc), parent=self.root)

    def _remove_supertile(self):
        if not self.project.supertiles:
            return
        index = self.project.active_supertile_index
        if not messagebox.askyesno(
            "Remove Supertile",
            "Remove supertile {}?".format(index),
            parent=self.root,
        ):
            return
        self.project.remove_supertile(index)

    def _rename_supertile(self):
        if not self.project.supertiles:
            return
        supertile = self.project.get_active_supertile()
        new_name = simpledialog.askstring(
            "Rename Supertile",
            "Supertile name:",
            initialvalue=supertile["name"],
            parent=self.root,
        )
        if new_name is None:
            return
        try:
            self.project.rename_supertile(
                self.project.active_supertile_index,
                new_name,
            )
        except ValueError as exc:
            messagebox.showerror("Rename Supertile", str(exc), parent=self.root)

    def _on_list_select(self, _event=None):
        selection = self._supertile_list.curselection()
        if not selection:
            return
        self.project.set_active_supertile_index(selection[0])

    def _close_assign_picker(self):
        if self._assign_picker is not None:
            self._assign_picker.close()
            self._assign_picker = None

    def _on_cell_click(self, cell_index):
        if not self.project.supertiles:
            return
        if not self.project.metatiles:
            messagebox.showinfo(
                "Assign Metatile",
                "Add at least one metatile first.",
                parent=self.root,
            )
            return
        if self._assign_picker is not None:
            self._assign_picker.focus()
            return

        super_index = self.project.active_supertile_index

        def on_metatile_selected(metatile_index):
            self._assign_picker = None
            self.project.set_supertile_cell(super_index, cell_index, metatile_index)

        self._assign_picker = MetatilePickerWindow(
            self.root,
            self.project,
            mode="assign",
            title="Select Metatile for Cell",
            on_select=on_metatile_selected,
            on_close=self._on_assign_picker_closed,
        )
        self._assign_picker.focus()

    def _on_assign_picker_closed(self):
        self._assign_picker = None

    def _refresh_supertile_list(self):
        self._supertile_list.delete(0, tk.END)
        for supertile in self.project.supertiles:
            self._supertile_list.insert(tk.END, supertile["name"])
        if self.project.supertiles:
            index = self.project.active_supertile_index
            self._supertile_list.selection_clear(0, tk.END)
            self._supertile_list.selection_set(index)
            self._supertile_list.activate(index)
            self._supertile_list.see(index)

    def _draw_metatile_thumbnail(self, canvas, metatile):
        pixels = resolve_metatile_pixels(metatile, self.project.tiles)
        draw_pixel_grid(canvas, pixels, CELL_THUMB_SCALE)

    def _refresh_cells(self):
        if not self.project.supertiles:
            for canvas in self._cell_widgets:
                canvas.delete("all")
            return
        supertile = self.project.get_active_supertile()
        for cell_index, canvas in enumerate(self._cell_widgets):
            metatile = self.project.get_metatile(supertile["cells"][cell_index])
            self._draw_metatile_thumbnail(canvas, metatile)

    def _refresh_composite(self):
        if not self.project.supertiles:
            self._composite_canvas.delete("all")
            return
        supertile = self.project.get_active_supertile()
        pixels = resolve_supertile_pixels(
            supertile,
            self.project.metatiles,
            self.project.tiles,
        )
        scale = SUPERTILE_PIXEL_SCALE_DEFAULT
        draw_pixel_grid(self._composite_canvas, pixels, scale)
        for i in range(SUPERTILE_COLS + 1):
            pos = i * METATILE_PIXEL_SIZE * scale
            size = SUPERTILE_PIXEL_WIDTH * scale
            self._composite_canvas.create_line(
                pos, 0, pos, size - 1, fill=theme.CANVAS_GRID_OUTLINE
            )
            self._composite_canvas.create_line(
                0, pos, size - 1, pos, fill=theme.CANVAS_GRID_OUTLINE
            )
        size = SUPERTILE_PIXEL_WIDTH * scale
        self._composite_canvas.create_line(
            size - 1, 0, size - 1, size - 1, fill=theme.CANVAS_GRID_OUTLINE
        )
        self._composite_canvas.create_line(
            0, size - 1, size - 1, size - 1, fill=theme.CANVAS_GRID_OUTLINE
        )

    def _refresh_active_supertile(self):
        self._refresh_cells()
        self._refresh_composite()
        self._update_status()

    def _update_status(self):
        if not self.project.supertiles:
            self._status_label.config(text="No supertiles")
            return
        supertile = self.project.get_active_supertile()
        index = self.project.active_supertile_index
        self._status_label.config(
            text="Supertile {} / {}".format(index, supertile["name"])
        )

    def _active_supertile_references_metatile(self, metatile_index):
        if not self.project.supertiles:
            return False
        supertile = self.project.get_active_supertile()
        return metatile_index in supertile["cells"]

    def _active_supertile_references_tile(self, tile_index):
        if not self.project.supertiles:
            return False
        supertile = self.project.get_active_supertile()
        for meta_index in set(supertile["cells"]):
            if metatile_references_tile(
                self.project.metatiles[meta_index],
                tile_index,
            ):
                return True
        return False

    def _on_project_change(self, event):
        if event.kind == ChangeEvent.TILE_CHANGED:
            if (
                self.project.supertiles
                and self._active_supertile_references_tile(event.index)
            ):
                self._refresh_cells()
                self._refresh_composite()
        elif event.kind == ChangeEvent.METATILE_CHANGED:
            if (
                self.project.supertiles
                and self._active_supertile_references_metatile(event.index)
            ):
                self._refresh_cells()
                self._refresh_composite()
        elif event.kind == ChangeEvent.SUPERTILE_CHANGED:
            self._refresh_supertile_list()
            if (
                self.project.supertiles
                and event.index == self.project.active_supertile_index
            ):
                self._refresh_active_supertile()
            else:
                self._update_status()
        elif event.kind == ChangeEvent.ACTIVE_SUPERTILE_CHANGED:
            self._refresh_supertile_list()
            self._refresh_active_supertile()