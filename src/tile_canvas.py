"""8x8 tile drawing canvas with per-row fg/bg swatch column."""

import tkinter as tk

from palette import resolve_pixel_color, rgb_to_hex
from theme import ACCENT_BORDER, CANVAS_BG, CANVAS_GRID_OUTLINE
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

    def __init__(self, parent, project, scale=TILE_PIXEL_SCALE_DEFAULT, window_bg=None):
        super().__init__(parent, bg=window_bg or parent.cget("bg"))
        self.project = project
        self.scale = clamp_scale(scale)
        self._window_bg = window_bg or parent.cget("bg")
        self._active_row = None
        self._active_channel = None
        self._swatch_select_callbacks = []
        self._pixel_change_callbacks = []
        self._stroke_active = False

        body = tk.Frame(self, bg=self._window_bg)
        body.pack()

        width, height = canvas_pixel_size(self.scale)
        self.canvas = tk.Canvas(
            body,
            width=width,
            height=height,
            bg=CANVAS_BG,
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack(side=tk.LEFT)

        swatch_width = swatch_column_width(self.scale)
        self._swatch_canvas = tk.Canvas(
            body,
            width=swatch_width,
            height=height,
            bg=CANVAS_BG,
            highlightthickness=0,
            cursor="hand2",
        )
        self._swatch_canvas.pack(side=tk.LEFT, padx=(4, 0))

        self._bind_drawing_events()
        self._bind_swatch_events()
        self.refresh()

    def set_scale(self, scale):
        self.scale = clamp_scale(scale)
        width, height = canvas_pixel_size(self.scale)
        swatch_width = swatch_column_width(self.scale)
        self.canvas.configure(width=width, height=height)
        self._swatch_canvas.configure(width=swatch_width, height=height)
        self.refresh()

    def on_swatch_select(self, callback):
        self._swatch_select_callbacks.append(callback)

    def on_pixel_change(self, callback):
        self._pixel_change_callbacks.append(callback)

    def set_active_target(self, row, channel):
        self._active_row = row
        self._active_channel = channel
        self._draw_swatches()

    def refresh(self):
        tile = self.project.get_active_tile()
        scale = self.scale
        canvas = self.canvas
        canvas.delete("all")

        for row in range(TILE_SIZE):
            for col in range(TILE_SIZE):
                x0 = col * scale
                y0 = row * scale
                x1 = x0 + scale
                y1 = y0 + scale
                fill = resolve_pixel_color(tile, row, col)
                canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="")

        for i in range(TILE_SIZE + 1):
            pos = i * scale
            canvas.create_line(0, pos, TILE_SIZE * scale, pos, fill=CANVAS_GRID_OUTLINE)
            canvas.create_line(pos, 0, pos, TILE_SIZE * scale, fill=CANVAS_GRID_OUTLINE)

        self._draw_swatches()

    def _draw_swatches(self):
        tile = self.project.get_active_tile()
        scale = self.scale
        size, fg_x, bg_x = swatch_layout(scale)
        canvas = self._swatch_canvas
        canvas.delete("all")

        for row in range(TILE_SIZE):
            y0 = row * scale
            y1 = y0 + scale
            fg_y0 = y0 + (scale - size) // 2
            fg_y1 = fg_y0 + size
            bg_y0 = fg_y0
            bg_y1 = fg_y1

            colors = tile["colors"][row]
            canvas.create_rectangle(
                fg_x,
                fg_y0,
                fg_x + size,
                fg_y1,
                fill=rgb_to_hex(colors["fg"]),
                outline=CANVAS_GRID_OUTLINE,
                tags=("swatch", f"fg-{row}"),
            )
            canvas.create_rectangle(
                bg_x,
                bg_y0,
                bg_x + size,
                bg_y1,
                fill=rgb_to_hex(colors["bg"]),
                outline=CANVAS_GRID_OUTLINE,
                tags=("swatch", f"bg-{row}"),
            )

            if row == self._active_row:
                highlight_y0 = y0 + 1
                highlight_y1 = y1 - 1
                canvas.create_rectangle(
                    fg_x - 1,
                    highlight_y0,
                    bg_x + size + 1,
                    highlight_y1,
                    outline=ACCENT_BORDER,
                    width=2,
                )

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

    def _bind_swatch_events(self):
        self._swatch_canvas.bind("<Button-1>", self._on_swatch_click)

    def _on_draw(self, event, bit):
        row, col = pixel_at(event.x, event.y, self.scale)
        for callback in self._pixel_change_callbacks:
            callback(row, col, bit, not self._stroke_active)
        self._stroke_active = True

    def _on_stroke_end(self, _event=None):
        self._stroke_active = False

    def _on_swatch_click(self, event):
        size, fg_x, bg_x = swatch_layout(self.scale)
        row = max(0, min(TILE_SIZE - 1, int(event.y // self.scale)))
        channel = "fg" if event.x < fg_x + size + SWATCH_GAP // 2 else "bg"
        self.set_active_target(row, channel)
        for callback in self._swatch_select_callbacks:
            callback(row, channel)