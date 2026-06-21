"""8x8 tile drawing canvas with per-row fg/bg swatch column."""

import tkinter as tk

from palette import resolve_pixel_color, rgb_to_hex
from theme import CANVAS_BG, CANVAS_GRID_OUTLINE
import theme
from tile_model import TILE_SIZE

TILE_PIXEL_SCALE_DEFAULT = 32
TILE_PIXEL_SCALE_MIN = 24
TILE_PIXEL_SCALE_MAX = 48
SWATCH_MIN_SIZE = 20
SWATCH_GAP = 4
SWATCH_SIDE_PADDING = 8


def canvas_pixel_size(scale):
    """Return (width, height) in pixels for an 8x8 grid at the given scale."""
    return TILE_SIZE * scale, TILE_SIZE * scale


def clamp_scale(scale):
    return max(TILE_PIXEL_SCALE_MIN, min(TILE_PIXEL_SCALE_MAX, scale))


def pixel_at(x, y, scale):
    """Map canvas coordinates to (row, col) with clamping."""
    col = max(0, min(TILE_SIZE - 1, int(x // scale)))
    row = max(0, min(TILE_SIZE - 1, int(y // scale)))
    return row, col


def swatch_size(scale):
    return max(SWATCH_MIN_SIZE, scale // 2)


def swatch_layout(scale):
    """Return (size, fg_x, bg_x) for the per-row swatch column."""
    size = swatch_size(scale)
    fg_x = SWATCH_SIDE_PADDING
    bg_x = fg_x + size + SWATCH_GAP
    return size, fg_x, bg_x


def swatch_column_width(scale):
    size, fg_x, bg_x = swatch_layout(scale)
    return bg_x + size + SWATCH_SIDE_PADDING


class TileCanvas(tk.Frame):
    """Composite widget: 8x8 pattern grid plus per-row fg/bg swatches."""

    def __init__(
        self,
        parent,
        project,
        scale=TILE_PIXEL_SCALE_DEFAULT,
        window_bg=None,
        root=None,
    ):
        super().__init__(parent, bg=window_bg or parent.cget("bg"))
        self.project = project
        self.scale = clamp_scale(scale)
        self._window_bg = window_bg or parent.cget("bg")
        self._root = root or parent.winfo_toplevel()
        self._active_row = None
        self._active_channel = None
        self._swatch_select_callbacks = []
        self._pixel_change_callbacks = []
        self._stroke_active = False
        self._suppress_stroke = False
        self._swatch_widgets = []
        self._pixel_rects = [[None] * TILE_SIZE for _ in range(TILE_SIZE)]
        self._stroke_end_callbacks = []

        self._body = tk.Frame(self, bg=self._window_bg)
        theme.register_frame(self._body, self._root, self._window_bg)
        self._body.pack()

        width, height = canvas_pixel_size(self.scale)
        self.canvas = tk.Canvas(
            self._body,
            width=width,
            height=height,
            bg=CANVAS_BG,
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack(side=tk.LEFT)

        self._swatch_column = tk.Frame(self._body, bg=self._window_bg)
        theme.register_frame(self._swatch_column, self._root, self._window_bg)
        self._swatch_column.pack(side=tk.LEFT, padx=(4, 0))
        self._build_swatch_column(height)

        self._bind_drawing_events()
        self.refresh()

    def _build_swatch_column(self, height):
        for child in self._swatch_column.winfo_children():
            child.destroy()
        self._swatch_widgets = []

        scale = self.scale
        size = swatch_size(scale)
        swatch_width = swatch_column_width(scale)
        self._swatch_column.configure(width=swatch_width, height=height)
        self._swatch_column.pack_propagate(False)

        for row in range(TILE_SIZE):
            row_frame = tk.Frame(self._swatch_column, bg=self._window_bg, height=scale)
            theme.register_frame(row_frame, self._root, self._window_bg)
            row_frame.pack(fill=tk.X)
            row_frame.pack_propagate(False)

            inner = tk.Frame(row_frame, bg=self._window_bg)
            theme.register_frame(inner, self._root, self._window_bg)
            inner.pack(pady=max(0, (scale - size) // 2))

            fg = tk.Frame(
                inner,
                width=size,
                height=size,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=CANVAS_GRID_OUTLINE,
            )
            fg.pack(side=tk.LEFT, padx=(SWATCH_SIDE_PADDING, SWATCH_GAP // 2))
            fg.pack_propagate(False)
            fg.bind(
                "<ButtonRelease-1>",
                lambda event, swatch_row=row: self._on_swatch_click(swatch_row, "fg", event),
            )

            bg = tk.Frame(
                inner,
                width=size,
                height=size,
                cursor="hand2",
                highlightthickness=1,
                highlightbackground=CANVAS_GRID_OUTLINE,
            )
            bg.pack(side=tk.LEFT, padx=(SWATCH_GAP // 2, SWATCH_SIDE_PADDING))
            bg.pack_propagate(False)
            bg.bind(
                "<ButtonRelease-1>",
                lambda event, swatch_row=row: self._on_swatch_click(swatch_row, "bg", event),
            )

            self._swatch_widgets.append({"fg": fg, "bg": bg})

    def set_scale(self, scale):
        self.scale = clamp_scale(scale)
        width, height = canvas_pixel_size(self.scale)
        self.canvas.configure(width=width, height=height)
        self._build_swatch_column(height)
        self.refresh()

    def on_swatch_select(self, callback):
        self._swatch_select_callbacks.append(callback)

    def on_pixel_change(self, callback):
        self._pixel_change_callbacks.append(callback)

    def on_stroke_end(self, callback):
        self._stroke_end_callbacks.append(callback)

    def set_active_target(self, row, channel):
        self._active_row = row
        self._active_channel = channel

    def suppress_next_stroke(self):
        """Ignore the next pattern-canvas click (e.g. after palette popup closes)."""
        self._suppress_stroke = True
        self._stroke_active = False

    def update_pixel(self, row, col):
        """Redraw a single pattern pixel after a local data change."""
        rect_id = self._pixel_rects[row][col]
        if rect_id is None:
            return
        tile = self.project.get_active_tile()
        fill = resolve_pixel_color(tile, row, col)
        self.canvas.itemconfig(rect_id, fill=fill)

    def refresh(self):
        tile = self.project.get_active_tile()
        scale = self.scale
        canvas = self.canvas
        canvas.delete("all")

        width, height = canvas_pixel_size(scale)
        for row in range(TILE_SIZE):
            for col in range(TILE_SIZE):
                x0 = col * scale
                y0 = row * scale
                x1 = x0 + scale
                y1 = y0 + scale
                fill = resolve_pixel_color(tile, row, col)
                rect_id = canvas.create_rectangle(
                    x0, y0, x1, y1, fill=fill, outline=""
                )
                self._pixel_rects[row][col] = rect_id

        for i in range(TILE_SIZE + 1):
            pos = i * scale
            if i == TILE_SIZE:
                pos = width - 1
            canvas.create_line(0, pos, width - 1, pos, fill=CANVAS_GRID_OUTLINE)
            canvas.create_line(pos, 0, pos, height - 1, fill=CANVAS_GRID_OUTLINE)

        self._update_swatches()

    def _update_swatches(self):
        tile = self.project.get_active_tile()
        for row, widgets in enumerate(self._swatch_widgets):
            colors = tile["colors"][row]
            widgets["fg"].configure(bg=rgb_to_hex(colors["fg"]))
            widgets["bg"].configure(bg=rgb_to_hex(colors["bg"]))

    def _bind_drawing_events(self):
        for sequence, bit in (
            ("<Button-1>", 1),
            ("<B1-Motion>", 1),
            ("<Button-3>", 0),
            ("<B3-Motion>", 0),
        ):
            self.canvas.bind(sequence, lambda event, value=bit: self._on_draw(event, value))
        self.canvas.bind("<ButtonRelease-1>", self._on_stroke_end)
        self.canvas.bind("<ButtonRelease-3>", self._on_stroke_end)

    def _on_draw(self, event, bit):
        if self._suppress_stroke:
            self._suppress_stroke = False
            return
        row, col = pixel_at(event.x, event.y, self.scale)
        for callback in self._pixel_change_callbacks:
            callback(row, col, bit, not self._stroke_active)
        self._stroke_active = True

    def _on_stroke_end(self, _event=None):
        if self._stroke_active:
            for callback in self._stroke_end_callbacks:
                callback()
        self._stroke_active = False

    def _on_swatch_click(self, row, channel, event):
        self.set_active_target(row, channel)
        for callback in self._swatch_select_callbacks:
            callback(row, channel, event.x_root, event.y_root)