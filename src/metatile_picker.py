"""Scrollable metatile picker for assigning metatile indices."""

import math
import tkinter as tk

from composite import resolve_metatile_pixels
from pixel_canvas import photoimage_from_pixels
from project import ChangeEvent
import theme

PICKER_METATILE_SCALE_DEFAULT = 2
PICKER_METATILE_SCALE_MIN = 2
PICKER_COLUMNS = 16
PICKER_CELL_GAP = 2
PICKER_VISIBLE_ROWS = 8


def clamp_picker_scale(scale):
    return max(PICKER_METATILE_SCALE_MIN, scale)


def cell_pixel_size(scale):
    return 16 * clamp_picker_scale(scale)


def picker_grid_size(scale, metatile_count):
    """Return (width, height) of the metatile picker grid in pixels."""
    if metatile_count <= 0:
        return 0, 0
    rows = int(math.ceil(metatile_count / PICKER_COLUMNS))
    cell = cell_pixel_size(scale)
    width = PICKER_COLUMNS * cell + (PICKER_COLUMNS - 1) * PICKER_CELL_GAP
    height = rows * cell + (rows - 1) * PICKER_CELL_GAP
    return width, height


class MetatilePickerWindow:
    """Non-modal metatile picker for one-shot cell assignment."""

    def __init__(
        self,
        parent,
        project,
        mode="assign",
        title=None,
        on_select=None,
        on_close=None,
    ):
        self.parent = parent
        self.project = project
        self.mode = mode
        self.on_select = on_select
        self._on_close = on_close
        self.scale = PICKER_METATILE_SCALE_DEFAULT

        self.window = tk.Toplevel(parent)
        if title is None:
            title = "Select Metatile for Cell"
        self.window.title("burglekutt — {}".format(title))
        self._picker_bg = theme.TILE_PICKER_BG
        self.window.configure(bg=self._picker_bg)
        self.window.transient(parent)

        shell = tk.Frame(self.window, bg=self._picker_bg, padx=8, pady=8)
        shell.pack(fill=tk.BOTH, expand=True)

        self._grid_frame = tk.Frame(shell, bg=self._picker_bg)
        self._grid_frame.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(
            self._grid_frame,
            bg=self._picker_bg,
            highlightthickness=0,
            cursor="hand2",
        )
        self._scrollbar = tk.Scrollbar(
            self._grid_frame,
            orient=tk.VERTICAL,
            command=self._canvas.yview,
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._canvas.bind("<Button-1>", self._on_click)
        self._canvas.bind("<Motion>", self._on_motion)
        self._canvas.bind("<Leave>", self._on_leave)

        status_frame = tk.Frame(shell, bg=self._picker_bg)
        status_frame.pack(fill=tk.X, pady=(8, 0))
        self._status_label = tk.Label(
            status_frame,
            text="",
            anchor=tk.W,
            bg=self._picker_bg,
            fg=theme.TEXT_FG,
        )
        self._status_label.pack(fill=tk.X)

        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.project.add_listener(self._on_project_change)
        self.refresh()
        self._update_status()

    def focus(self):
        self.window.lift()
        self.window.focus_force()

    def refresh(self):
        self._canvas.delete("all")
        self._canvas._thumb_photos = []
        count = len(self.project.metatiles)
        grid_width, grid_height = picker_grid_size(self.scale, count)
        visible_height = (
            PICKER_VISIBLE_ROWS * cell_pixel_size(self.scale)
            + (PICKER_VISIBLE_ROWS - 1) * PICKER_CELL_GAP
        )
        canvas_height = max(grid_height, visible_height) if count else visible_height
        self._canvas.config(
            width=max(grid_width, 1),
            height=visible_height,
            scrollregion=(0, 0, max(grid_width, 1), canvas_height),
        )

        if count == 0:
            return

        cell = cell_pixel_size(self.scale)
        stride = cell + PICKER_CELL_GAP
        pixel_scale = self.scale

        for index in range(count):
            row = index // PICKER_COLUMNS
            col = index % PICKER_COLUMNS
            x0 = col * stride
            y0 = row * stride
            x1 = x0 + cell
            y1 = y0 + cell

            metatile = self.project.get_metatile(index)
            pixels = resolve_metatile_pixels(metatile, self.project.tiles)
            thumb = photoimage_from_pixels(pixels, pixel_scale)
            self._canvas.create_image(x0, y0, anchor=tk.NW, image=thumb)
            self._canvas._thumb_photos.append(thumb)

    def _canvas_coords(self, event):
        return self._canvas.canvasx(event.x), self._canvas.canvasy(event.y)

    def _index_at(self, x, y):
        count = len(self.project.metatiles)
        if count == 0:
            return None
        cell = cell_pixel_size(self.scale)
        stride = cell + PICKER_CELL_GAP
        col = int(x // stride)
        row = int(y // stride)
        if col < 0 or col >= PICKER_COLUMNS or row < 0:
            return None
        if x - col * stride >= cell or y - row * stride >= cell:
            return None
        index = row * PICKER_COLUMNS + col
        if index >= count:
            return None
        return index

    def _on_click(self, event):
        if not self.project.metatiles:
            return
        x, y = self._canvas_coords(event)
        index = self._index_at(x, y)
        if index is None:
            return
        if self.mode == "assign":
            if self.on_select is not None:
                self.on_select(index)
            self.close()

    def _on_motion(self, event):
        if not self.project.metatiles:
            self._update_status()
            return
        x, y = self._canvas_coords(event)
        index = self._index_at(x, y)
        if index is None:
            self._update_status()
            return
        metatile = self.project.get_metatile(index)
        self._status_label.config(
            text="Metatile {} / {}".format(index, metatile["name"])
        )

    def _on_leave(self, _event=None):
        self._update_status()

    def _update_status(self):
        if not self.project.metatiles:
            self._status_label.config(text="No metatiles defined")
            return
        if self.mode == "assign":
            self._status_label.config(text="Click a metatile to assign")
            return
        self._status_label.config(text="")

    def _on_project_change(self, event):
        if event.kind in (ChangeEvent.TILE_CHANGED, ChangeEvent.METATILE_CHANGED):
            self.refresh()
            self._update_status()

    def close(self, _event=None):
        self.project.remove_listener(self._on_project_change)
        try:
            self.window.destroy()
        except tk.TclError:
            pass
        if self._on_close is not None:
            self._on_close()