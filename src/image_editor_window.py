"""Tile image editor window."""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import shortcuts
import theme
from composite import resolve_tile_image_pixels
from image_model import (
    DEFAULT_TILE_IMAGE_HEIGHT,
    DEFAULT_TILE_IMAGE_WIDTH,
    TILE_IMAGE_MAX_UNIQUE_TILES,
    TileImageUniqueTileLimitError,
    assign_tile_image_cell,
    count_unique_tiles,
    empty_tile_image,
    resize_tile_image,
)
from pixel_canvas import draw_pixel_grid
from project import ChangeEvent
from tile_model import TILE_SIZE
from tile_picker import TilePickerWindow

IMAGE_PIXEL_SCALE_DEFAULT = 3
IMAGE_PIXEL_SCALE_MIN = 1
IMAGE_PIXEL_SCALE_MAX = 8


def clamp_image_scale(scale):
    return max(IMAGE_PIXEL_SCALE_MIN, min(IMAGE_PIXEL_SCALE_MAX, scale))


def tile_image_cell_at(x, y, width, height, scale):
    """Return the cell index under canvas pixel (x, y), or None."""
    cell = TILE_SIZE * scale
    if cell <= 0:
        return None
    col = int(x // cell)
    row = int(y // cell)
    if col < 0 or col >= width or row < 0 or row >= height:
        return None
    return row * width + col


class ImageEditorWindow:
    def __init__(self, root, project, coordinator=None):
        self.root = root
        self.project = project
        self.coordinator = coordinator
        self._assign_picker = None
        self._image = empty_tile_image(
            width=DEFAULT_TILE_IMAGE_WIDTH,
            height=DEFAULT_TILE_IMAGE_HEIGHT,
        )
        self.scale = IMAGE_PIXEL_SCALE_DEFAULT

        self.root.title("burglekutt — Tile Image")
        self.root.minsize(640, 400)

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

        self._refresh_preview()
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

        image_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Image", menu=image_menu)
        image_menu.add_command(
            label="Set Dimensions…",
            command=self._set_dimensions,
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

        panel = ttk.Labelframe(
            content,
            text="Image",
            padding=8,
            style=self._styles.labelframe,
        )
        panel.pack(fill=tk.BOTH, expand=True)

        grid = ttk.Frame(panel, style=self._styles.frame)
        grid.pack(fill=tk.BOTH, expand=True)
        grid.rowconfigure(0, weight=1)
        grid.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            grid,
            bg=theme.CANVAS_BG,
            highlightthickness=0,
            cursor="hand2",
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
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.configure(takefocus=True)
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

    def _update_status(self):
        unique = count_unique_tiles(self._image["cells"])
        self._status_label.configure(
            text="{}  {}×{}  Unique tiles: {} / {}".format(
                self._image["name"],
                self._image["width"],
                self._image["height"],
                unique,
                TILE_IMAGE_MAX_UNIQUE_TILES,
            )
        )

    def _on_canvas_click(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        cell_index = tile_image_cell_at(
            canvas_x,
            canvas_y,
            self._image["width"],
            self._image["height"],
            self.scale,
        )
        if cell_index is None:
            return
        self._on_cell_click(cell_index)

    def _close_assign_picker(self):
        if self._assign_picker is not None:
            self._assign_picker.close()
            self._assign_picker = None

    def _on_cell_click(self, cell_index):
        if self._assign_picker is not None:
            self._assign_picker.focus()
            return

        def on_tile_selected(tile_index):
            self._assign_picker = None
            try:
                assign_tile_image_cell(self._image, cell_index, tile_index)
            except TileImageUniqueTileLimitError as exc:
                messagebox.showerror("Unique Tile Limit", str(exc), parent=self.root)
                return
            self._refresh_preview()
            self._update_status()

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

    def _set_dimensions(self, _event=None):
        width = simpledialog.askinteger(
            "Set Dimensions",
            "Width in tiles:",
            initialvalue=self._image["width"],
            minvalue=1,
            parent=self.root,
        )
        if width is None:
            return
        height = simpledialog.askinteger(
            "Set Dimensions",
            "Height in tiles:",
            initialvalue=self._image["height"],
            minvalue=1,
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
            resize_tile_image(self._image, width, height)
        except (ValueError, TileImageUniqueTileLimitError) as exc:
            messagebox.showerror("Set Dimensions", str(exc), parent=self.root)
            return
        self._refresh_preview()
        self._update_status()

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
        if event.kind in (ChangeEvent.TILE_CHANGED, ChangeEvent.PROJECT_LOADED):
            self._refresh_preview()
            self._update_status()

    def shutdown(self):
        self._close_assign_picker()
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
            "burglekutt — TI-99 tile image editor\nPhase 2: grid editor",
        )

    def _on_close(self, _event=None):
        if self.coordinator is not None:
            self.coordinator.request_close(self)
        else:
            self.shutdown()
            self.root.destroy()
