"""TMS9918 palette constants, color resolution, and palette sidebar widget."""

import tkinter as tk
from tkinter import ttk

import theme
from tile_model import TILE_SIZE

TI_COLORS = [
    "Transparent",
    "Black",
    "Medium Green",
    "Light Green",
    "Dark Blue",
    "Light Blue",
    "Dark Red",
    "Cyan",
    "Medium Red",
    "Light Red",
    "Dark Yellow",
    "Light Yellow",
    "Dark Green",
    "Magenta",
    "Gray",
    "White",
]

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

PALETTE_SWATCH_SIZE = 24
PALETTE_COLUMNS = 4


def rgb_to_hex(index):
    """Return a Tk fill color for TMS9918 index 1-15; index 0 is neutral grey."""
    if index == 0:
        return "#888888"
    r, g, b = TI_RGB[index]
    return f"#{r:02x}{g:02x}{b:02x}"


def resolve_pixel_color(tile, row, col):
    """Resolve a pattern pixel to a hex color from per-row fg/bg."""
    colors = tile["colors"][row]
    bit = tile["pattern"][row][col]
    color_index = colors["fg"] if bit else colors["bg"]
    return rgb_to_hex(color_index)


def _draw_checkerboard(canvas, size):
    """Draw a small checkerboard for transparent (index 0) swatches."""
    half = size // 2
    light = "#CCCCCC"
    dark = "#999999"
    canvas.create_rectangle(0, 0, half, half, fill=light, outline="")
    canvas.create_rectangle(half, half, size, size, fill=light, outline="")
    canvas.create_rectangle(half, 0, size, half, fill=dark, outline="")
    canvas.create_rectangle(0, half, half, size, fill=dark, outline="")


class PalettePanel(ttk.Frame):
    """Clickable TMS9918 color grid for assigning row fg/bg colors."""

    def __init__(self, parent, window_bg=None):
        super().__init__(parent)
        self._window_bg = window_bg
        self._target_row = None
        self._target_channel = None
        self._color_callbacks = []

        self._target_label = ttk.Label(self, text="Select a row fg/bg swatch")
        self._target_label.pack(anchor=tk.W, pady=(0, 6))

        grid = tk.Frame(self, bg=window_bg or parent.cget("bg"))
        if window_bg:
            theme.register_frame(grid)
        grid.pack()

        for index in range(16):
            row = index // PALETTE_COLUMNS
            col = index % PALETTE_COLUMNS
            cell = tk.Frame(grid, bg=window_bg or parent.cget("bg"))
            if window_bg:
                theme.register_frame(cell)
            cell.grid(row=row, column=col, padx=2, pady=2)

            swatch = tk.Canvas(
                cell,
                width=PALETTE_SWATCH_SIZE,
                height=PALETTE_SWATCH_SIZE,
                highlightthickness=1,
                highlightbackground=theme.CANVAS_GRID_OUTLINE,
                cursor="hand2",
            )
            swatch.pack()
            if index == 0:
                _draw_checkerboard(swatch, PALETTE_SWATCH_SIZE)
            else:
                swatch.create_rectangle(
                    0,
                    0,
                    PALETTE_SWATCH_SIZE,
                    PALETTE_SWATCH_SIZE,
                    fill=rgb_to_hex(index),
                    outline="",
                )
            swatch.bind(
                "<Button-1>",
                lambda _event, color_index=index: self._on_swatch_click(color_index),
            )

            ttk.Label(cell, text=str(index), anchor=tk.CENTER).pack()

    def set_target(self, row, channel):
        """Highlight the active row/channel target for palette assignment."""
        self._target_row = row
        self._target_channel = channel
        channel_label = "foreground" if channel == "fg" else "background"
        self._target_label.config(text=f"Row {row} {channel_label}")

    def clear_target(self):
        self._target_row = None
        self._target_channel = None
        self._target_label.config(text="Select a row fg/bg swatch")

    def has_target(self):
        return self._target_row is not None and self._target_channel is not None

    def get_target(self):
        return self._target_row, self._target_channel

    def on_color_pick(self, callback):
        self._color_callbacks.append(callback)

    def _on_swatch_click(self, color_index):
        if not self.has_target():
            return
        for callback in self._color_callbacks:
            callback(color_index)