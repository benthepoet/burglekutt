"""8x8 tile drawing canvas."""

import tkinter as tk

from theme import CANVAS_BG, CANVAS_GRID_OUTLINE
from tile_model import TILE_SIZE

TILE_PIXEL_SCALE_DEFAULT = 32
TILE_PIXEL_SCALE_MIN = 24
TILE_PIXEL_SCALE_MAX = 48

# TMS9918 display RGB (index 0 unused for resolved pixels)
TI_RGB = [
    (0, 0, 0),
    (0, 0, 0),
    (33, 200, 66),
    (66, 220, 99),
    (66, 66, 200),
    (99, 99, 255),
    (200, 66, 66),
    (33, 200, 200),
    (200, 66, 66),
    (255, 99, 99),
    (200, 200, 66),
    (200, 200, 99),
    (66, 200, 66),
    (200, 66, 200),
    (200, 200, 200),
    (255, 255, 255),
]


def canvas_pixel_size(scale):
    """Return (width, height) in pixels for an 8x8 grid at the given scale."""
    return TILE_SIZE * scale, TILE_SIZE * scale


def clamp_scale(scale):
    return max(TILE_PIXEL_SCALE_MIN, min(TILE_PIXEL_SCALE_MAX, scale))


def _rgb_to_hex(index):
    r, g, b = TI_RGB[index]
    return f"#{r:02x}{g:02x}{b:02x}"


def _resolve_pixel_color(tile, row, col):
    colors = tile["colors"][row]
    bit = tile["pattern"][row][col]
    color_index = colors["fg"] if bit else colors["bg"]
    return _rgb_to_hex(color_index)


class TileCanvas(tk.Frame):
    """Composite widget: 8x8 pattern grid (fg/bg column added in Phase 2)."""

    def __init__(self, parent, project, scale=TILE_PIXEL_SCALE_DEFAULT, window_bg=None):
        super().__init__(parent, bg=window_bg or parent.cget("bg"))
        self.project = project
        self.scale = clamp_scale(scale)

        width, height = canvas_pixel_size(self.scale)
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=CANVAS_BG,
            highlightthickness=0,
        )
        self.canvas.pack()

        self._draw_empty()

    def set_scale(self, scale):
        self.scale = clamp_scale(scale)
        width, height = canvas_pixel_size(self.scale)
        self.canvas.configure(width=width, height=height)
        self.refresh()

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
                fill = _resolve_pixel_color(tile, row, col)
                canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="")

        for i in range(TILE_SIZE + 1):
            pos = i * scale
            canvas.create_line(0, pos, TILE_SIZE * scale, pos, fill=CANVAS_GRID_OUTLINE)
            canvas.create_line(pos, 0, pos, TILE_SIZE * scale, fill=CANVAS_GRID_OUTLINE)

    def _draw_empty(self):
        self.canvas.delete("all")
        width, height = canvas_pixel_size(self.scale)
        self.canvas.create_rectangle(0, 0, width, height, fill=CANVAS_BG, outline="")