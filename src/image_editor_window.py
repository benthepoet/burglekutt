"""Tile image editor window."""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import shortcuts
import theme
from composite import resolve_tile_image_pixels
from export_preview import (
    MODE_ASSEMBLY,
    MODE_BINARY,
    SCOPE_TILE_IMAGE,
    show_export_preview,
)
from image_model import (
    DEFAULT_TILE_IMAGE_HEIGHT,
    DEFAULT_TILE_IMAGE_WIDTH,
    TILE_IMAGE_MAX_CELLS,
    TILE_IMAGE_MAX_UNIQUE_TILES,
    TileImageUniqueTileLimitError,
    count_unique_tiles,
    ensure_unique_cell_tile,
    unused_tile_image_name,
)
from palette import resolve_pixel_color
from pixel_canvas import draw_pixel_grid, put_scaled_pixel
from project import ChangeEvent
from tile_model import TILE_SIZE
from theme import CANVAS_GRID_OUTLINE

IMAGE_PIXEL_SCALE_DEFAULT = 3
IMAGE_PIXEL_SCALE_MIN = 1
IMAGE_PIXEL_SCALE_MAX = 8


def clamp_image_scale(scale):
    return max(IMAGE_PIXEL_SCALE_MIN, min(IMAGE_PIXEL_SCALE_MAX, scale))


def fit_image_scale(image_width, image_height, view_width, view_height):
    """Largest integer scale that fits the tile image in the view."""
    tile_w = image_width * TILE_SIZE
    tile_h = image_height * TILE_SIZE
    if tile_w < 1 or tile_h < 1 or view_width < 1 or view_height < 1:
        return IMAGE_PIXEL_SCALE_MIN
    scale = min(view_width // tile_w, view_height // tile_h)
    return clamp_image_scale(scale)


def tile_image_cell_at(x, y, width, height, scale):
    """Return the cell index under canvas pixel (x, y), or None."""
    hit = tile_image_pixel_at(x, y, width, height, scale)
    if hit is None:
        return None
    return hit[0]


def tile_image_pixel_at(x, y, width, height, scale):
    """Return (cell_index, local_row, local_col) under canvas pixel (x, y)."""
    if scale <= 0:
        return None
    cell = TILE_SIZE * scale
    col = int(x // cell)
    row = int(y // cell)
    if col < 0 or col >= width or row < 0 or row >= height:
        return None
    local_col = int((x - col * cell) // scale)
    local_row = int((y - row * cell) // scale)
    if local_col < 0 or local_col >= TILE_SIZE or local_row < 0 or local_row >= TILE_SIZE:
        return None
    return row * width + col, local_row, local_col


class ImageEditorWindow:
    def __init__(self, root, project, coordinator=None):
        self.root = root
        self.project = project
        self.coordinator = coordinator
        self._stroke_tile_index = None
        self._stroke_dirty = False
        self._painting = False
        self._export_preview = None
        self.scale = IMAGE_PIXEL_SCALE_DEFAULT

        self.root.title("burglekutt — Tile Image")
        self.root.minsize(800, 560)
        self.root.geometry("1200x800")
        self._did_initial_fit = False

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

        self._refresh_image_list()
        self._refresh_preview()
        self._update_status()

    @property
    def _image(self):
        return self.project.get_active_tile_image()

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

        image_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Image", menu=image_menu)
        image_menu.add_command(label="Add…", command=self._add_image)
        image_menu.add_command(label="Remove", command=self._remove_image)
        image_menu.add_command(label="Rename…", command=self._rename_image)
        image_menu.add_separator()
        image_menu.add_command(
            label="Set Dimensions…",
            command=self._set_dimensions,
        )

        export_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Export", menu=export_menu)
        export_menu.add_command(
            label="Save Assembly…",
            accelerator="Ctrl+Shift+A",
            command=self._preview_assembly,
        )
        export_menu.add_command(
            label="Save Binary…",
            accelerator="Ctrl+Shift+B",
            command=self._preview_binary,
        )

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(
            label="Zoom In",
            accelerator="+",
            command=self._zoom_in,
        )
        view_menu.add_command(
            label="Zoom Out",
            accelerator="-",
            command=self._zoom_out,
        )
        view_menu.add_command(
            label="Fit to Window",
            command=self._fit_to_window,
        )
        view_menu.add_command(
            label="Reset Zoom",
            command=self._zoom_reset,
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

        left = ttk.Labelframe(
            content,
            text="Images",
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

        self._image_list = tk.Listbox(
            list_frame,
            width=20,
            height=16,
            yscrollcommand=list_scroll.set,
        )
        self._image_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self._image_list.yview)
        self._image_list.bind("<<ListboxSelect>>", self._on_list_select)
        self._image_list.bind("<F2>", self._rename_image)
        self._image_list.bind("<Delete>", self._remove_image)

        buttons = ttk.Frame(left, style=self._styles.frame)
        buttons.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(
            buttons,
            text="Add…",
            command=self._add_image,
            style=self._styles.button,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            buttons,
            text="Remove",
            command=self._remove_image,
            style=self._styles.button,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            buttons,
            text="Rename…",
            command=self._rename_image,
            style=self._styles.button,
        ).pack(side=tk.LEFT)

        panel = ttk.Labelframe(
            content,
            text="Image",
            padding=8,
            style=self._styles.labelframe,
        )
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        grid = ttk.Frame(panel, style=self._styles.frame)
        grid.pack(fill=tk.BOTH, expand=True)
        grid.rowconfigure(0, weight=1)
        grid.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            grid,
            bg=theme.CANVAS_BG,
            highlightthickness=0,
            cursor="crosshair",
        )
        self._hscroll = ttk.Scrollbar(
            grid,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview,
            style=self._styles.scrollbar,
        )
        self._vscroll = ttk.Scrollbar(
            grid,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            style=self._styles.scrollbar,
        )
        self.canvas.configure(
            xscrollcommand=self._hscroll.set,
            yscrollcommand=self._vscroll.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self._vscroll.grid(row=0, column=1, sticky="ns")
        self._hscroll.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(takefocus=True)
        self.canvas.bind("<Button-1>", lambda event: self._on_draw(event, 1))
        self.canvas.bind("<B1-Motion>", lambda event: self._on_draw(event, 1))
        self.canvas.bind("<Button-3>", lambda event: self._on_draw(event, 0))
        self.canvas.bind("<B3-Motion>", lambda event: self._on_draw(event, 0))
        self.canvas.bind("<ButtonRelease-1>", self._on_stroke_end)
        self.canvas.bind("<ButtonRelease-3>", self._on_stroke_end)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        shortcuts.bind_canvas_zoom(self.canvas, self._zoom_in, self._zoom_out)

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

    def _image_pixel_size(self):
        return (
            self._image["width"] * TILE_SIZE * self.scale,
            self._image["height"] * TILE_SIZE * self.scale,
        )

    def _refresh_preview(self):
        pixels = resolve_tile_image_pixels(self._image, self.project.tiles)
        draw_pixel_grid(self.canvas, pixels, self.scale)
        width, height = self._image_pixel_size()
        self.canvas.configure(scrollregion=(0, 0, width, height))
        cell = TILE_SIZE * self.scale
        for col in range(self._image["width"] + 1):
            x = col * cell
            if col == self._image["width"]:
                x = width - 1
            self.canvas.create_line(x, 0, x, height, fill=CANVAS_GRID_OUTLINE)
        for row in range(self._image["height"] + 1):
            y = row * cell
            if row == self._image["height"]:
                y = height - 1
            self.canvas.create_line(0, y, width, y, fill=CANVAS_GRID_OUTLINE)

    def _update_status(self, cell_index=None):
        unique = count_unique_tiles(self._image["cells"])
        parts = [
            "{}  {}×{}".format(
                self._image["name"],
                self._image["width"],
                self._image["height"],
            ),
            "Unique tiles: {} / {}".format(unique, TILE_IMAGE_MAX_UNIQUE_TILES),
        ]
        if cell_index is not None:
            tile_index = self._image["cells"][cell_index]
            col = cell_index % self._image["width"]
            row = cell_index // self._image["width"]
            tile = self.project.get_tile(tile_index)
            parts.append("Cell {},{} → {} (TIL{:02X})".format(
                col, row, tile["name"], tile_index
            ))
        self._status_label.configure(text="  |  ".join(parts))

    def _on_draw(self, event, bit):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        hit = tile_image_pixel_at(
            canvas_x,
            canvas_y,
            self._image["width"],
            self._image["height"],
            self.scale,
        )
        if hit is None:
            return
        cell_index, local_row, local_col = hit
        if not self._painting:
            self._begin_cell_stroke(cell_index)
        elif (
            self._stroke_tile_index is not None
            and self._image["cells"][cell_index] != self._stroke_tile_index
        ):
            self._end_cell_stroke()
            self._begin_cell_stroke(cell_index)
        if self._stroke_tile_index is None:
            return
        if self.project.set_tile_pixel(
            self._stroke_tile_index,
            local_row,
            local_col,
            bit,
            notify=False,
        ):
            self._stroke_dirty = True
            self._blit_tile_pixel(self._stroke_tile_index, local_row, local_col)
            self._update_status(cell_index)

    def _blit_tile_pixel(self, tile_index, local_row, local_col):
        """Update one pattern pixel on every image cell that uses tile_index."""
        photo = getattr(self.canvas, "_pixel_photo", None)
        if photo is None:
            self._refresh_preview()
            return
        color = resolve_pixel_color(
            self.project.get_tile(tile_index), local_row, local_col
        )
        width = self._image["width"]
        for cell_index, mapped in enumerate(self._image["cells"]):
            if mapped != tile_index:
                continue
            cell_col = cell_index % width
            cell_row = cell_index // width
            put_scaled_pixel(
                photo,
                cell_col * TILE_SIZE + local_col,
                cell_row * TILE_SIZE + local_row,
                color,
                self.scale,
            )

    def _begin_cell_stroke(self, cell_index):
        self._painting = True
        tile_index, source_index = ensure_unique_cell_tile(self._image, cell_index)
        if source_index is not None:
            self.project.duplicate_tile(source_index, tile_index, notify=False)
            self.project.notify_tile_image_changed()
        self._stroke_tile_index = tile_index
        self._stroke_dirty = False

    def _end_cell_stroke(self):
        if self._stroke_dirty and self._stroke_tile_index is not None:
            self.project.notify_tile_changed(self._stroke_tile_index)
        self._stroke_tile_index = None
        self._stroke_dirty = False
        self._painting = False

    def _on_stroke_end(self, _event=None):
        self._end_cell_stroke()
        self._update_status()

    def _image_list_label(self, image):
        return "{}  {}×{}".format(image["name"], image["width"], image["height"])

    def _refresh_image_list(self):
        self._image_list.delete(0, tk.END)
        for image in self.project.tile_images:
            self._image_list.insert(tk.END, self._image_list_label(image))
        if self.project.tile_images:
            index = self.project.active_tile_image_index
            self._image_list.selection_clear(0, tk.END)
            self._image_list.selection_set(index)
            self._image_list.activate(index)
            self._image_list.see(index)

    def _on_list_select(self, _event=None):
        selection = self._image_list.curselection()
        if not selection:
            return
        index = int(selection[0])
        if index == self.project.active_tile_image_index:
            return
        self._end_cell_stroke()
        self.project.set_active_tile_image_index(index)

    def _add_image(self, _event=None):
        try:
            default_name = unused_tile_image_name(self.project.tile_images)
        except ValueError as exc:
            messagebox.showerror("Add Image", str(exc), parent=self.root)
            return
        name = simpledialog.askstring(
            "Add Image",
            "Image name:",
            initialvalue=default_name,
            parent=self.root,
        )
        if name is None:
            return
        try:
            name = name.strip()
        except ValueError as exc:
            messagebox.showerror("Add Image", str(exc), parent=self.root)
            return
        width = simpledialog.askinteger(
            "Add Image",
            "Width in tiles (max {} tiles total):".format(TILE_IMAGE_MAX_CELLS),
            initialvalue=DEFAULT_TILE_IMAGE_WIDTH,
            minvalue=1,
            maxvalue=TILE_IMAGE_MAX_CELLS,
            parent=self.root,
        )
        if width is None:
            return
        max_height = TILE_IMAGE_MAX_CELLS // width
        height = simpledialog.askinteger(
            "Add Image",
            "Height in tiles (max {} for width {}):".format(max_height, width),
            initialvalue=min(DEFAULT_TILE_IMAGE_HEIGHT, max_height),
            minvalue=1,
            maxvalue=max_height,
            parent=self.root,
        )
        if height is None:
            return
        self._end_cell_stroke()
        try:
            self.project.add_tile_image(name, width, height)
        except ValueError as exc:
            messagebox.showerror("Add Image", str(exc), parent=self.root)

    def _remove_image(self, _event=None):
        if len(self.project.tile_images) <= 1:
            messagebox.showwarning(
                "Remove Image",
                "At least one tile image is required.",
                parent=self.root,
            )
            return
        image = self._image
        if not messagebox.askyesno(
            "Remove Image",
            "Remove image {}?".format(image["name"]),
            parent=self.root,
        ):
            return
        self._end_cell_stroke()
        try:
            self.project.remove_tile_image(self.project.active_tile_image_index)
        except ValueError as exc:
            messagebox.showerror("Remove Image", str(exc), parent=self.root)

    def _rename_image(self, _event=None):
        image = self._image
        new_name = simpledialog.askstring(
            "Rename Image",
            "Image name:",
            initialvalue=image["name"],
            parent=self.root,
        )
        if new_name is None:
            return
        try:
            self.project.rename_tile_image(
                self.project.active_tile_image_index, new_name
            )
        except ValueError as exc:
            messagebox.showerror("Rename Image", str(exc), parent=self.root)

    def _set_dimensions(self, _event=None):
        width = simpledialog.askinteger(
            "Set Dimensions",
            "Width in tiles (max {} tiles total):".format(TILE_IMAGE_MAX_CELLS),
            initialvalue=self._image["width"],
            minvalue=1,
            maxvalue=TILE_IMAGE_MAX_CELLS,
            parent=self.root,
        )
        if width is None:
            return
        max_height = TILE_IMAGE_MAX_CELLS // width
        height = simpledialog.askinteger(
            "Set Dimensions",
            "Height in tiles (max {} for width {}):".format(max_height, width),
            initialvalue=min(self._image["height"], max_height),
            minvalue=1,
            maxvalue=max_height,
            parent=self.root,
        )
        if height is None:
            return
        if width < self._image["width"] or height < self._image["height"]:
            if not messagebox.askyesno(
                "Set Dimensions",
                "Shrinking the image will discard tiles outside the new size. Continue?",
                parent=self.root,
            ):
                return
        try:
            self.project.resize_tile_image_at(
                self.project.active_tile_image_index, width, height
            )
        except (ValueError, TileImageUniqueTileLimitError) as exc:
            messagebox.showerror("Set Dimensions", str(exc), parent=self.root)

    def _on_canvas_configure(self, event):
        if event.widget is not self.canvas:
            return
        if event.width < 32 or event.height < 32:
            return
        if self._did_initial_fit:
            return
        self._did_initial_fit = True
        self._fit_to_window()

    def _fit_to_window(self, _event=None):
        self.canvas.update_idletasks()
        view_w = max(self.canvas.winfo_width(), 1)
        view_h = max(self.canvas.winfo_height(), 1)
        scale = fit_image_scale(
            self._image["width"],
            self._image["height"],
            view_w,
            view_h,
        )
        if scale != self.scale:
            self.scale = scale
        self._refresh_preview()

    def _zoom_in(self, _event=None):
        scale = clamp_image_scale(self.scale + 1)
        if scale != self.scale:
            self.scale = scale
            self._refresh_preview()

    def _zoom_out(self, _event=None):
        scale = clamp_image_scale(self.scale - 1)
        if scale != self.scale:
            self.scale = scale
            self._refresh_preview()

    def _zoom_reset(self, _event=None):
        if self.scale != IMAGE_PIXEL_SCALE_DEFAULT:
            self.scale = IMAGE_PIXEL_SCALE_DEFAULT
            self._refresh_preview()

    def _on_project_change(self, event):
        if self._painting:
            return
        if event.kind == ChangeEvent.PROJECT_LOADED:
            self._end_cell_stroke()
            self._refresh_image_list()
            self._fit_to_window()
            self._update_status()
            return
        if event.kind == ChangeEvent.ACTIVE_TILE_IMAGE_CHANGED:
            self._refresh_image_list()
            self._fit_to_window()
            self._update_status()
            return
        if event.kind == ChangeEvent.TILE_IMAGE_CHANGED:
            self._refresh_image_list()
            self._refresh_preview()
            self._update_status()
            return
        if event.kind == ChangeEvent.TILE_CHANGED:
            self._refresh_preview()
            self._update_status()

    def _close_export_preview(self):
        if self._export_preview is not None:
            self._export_preview.close()
            self._export_preview = None

    def _preview_assembly(self, _event=None):
        self._close_export_preview()
        try:
            self.project.get_active_tile_image()
        except IndexError:
            return
        self._export_preview = show_export_preview(
            self.root,
            self.project,
            SCOPE_TILE_IMAGE,
            MODE_ASSEMBLY,
            self._window_bg,
        )

    def _preview_binary(self, _event=None):
        self._close_export_preview()
        try:
            self.project.get_active_tile_image()
        except IndexError:
            return
        self._export_preview = show_export_preview(
            self.root,
            self.project,
            SCOPE_TILE_IMAGE,
            MODE_BINARY,
            self._window_bg,
        )

    def shutdown(self):
        self._end_cell_stroke()
        self._close_export_preview()
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
            "burglekutt — TI-99 tile image editor\nPhase 4: project I/O and export",
        )

    def _on_close(self, _event=None):
        if self.coordinator is not None:
            self.coordinator.request_close(self)
        else:
            self.shutdown()
            self.root.destroy()
