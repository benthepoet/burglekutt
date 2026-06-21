"""TMS9918 palette constants, color resolution, and palette popup widget."""

import tkinter as tk

import theme

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


class PalettePanel(tk.Frame):
    """Clickable TMS9918 color grid."""

    def __init__(self, parent, window_bg=None, *, require_target=True):
        bg = window_bg or parent.cget("bg")
        super().__init__(parent, bg=bg)
        self._window_bg = window_bg
        self._require_target = require_target
        self._target_row = None
        self._target_channel = None
        self._color_callbacks = []

        grid = tk.Frame(self, bg=bg)
        grid.pack()

        for index in range(16):
            row = index // PALETTE_COLUMNS
            col = index % PALETTE_COLUMNS
            cell = tk.Frame(grid, bg=bg)
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
                "<ButtonRelease-1>",
                lambda _event, color_index=index: self._on_swatch_click(color_index),
            )

            tk.Label(
                cell,
                text=str(index),
                bg=bg,
                fg=theme.TEXT_FG,
                anchor=tk.CENTER,
            ).pack()

    def set_target(self, row, channel):
        self._target_row = row
        self._target_channel = channel

    def clear_target(self):
        self._target_row = None
        self._target_channel = None

    def has_target(self):
        return self._target_row is not None and self._target_channel is not None

    def get_target(self):
        return self._target_row, self._target_channel

    def on_color_pick(self, callback):
        self._color_callbacks.append(callback)

    def _on_swatch_click(self, color_index):
        if self._require_target and not self.has_target():
            return
        for callback in self._color_callbacks:
            callback(color_index)


class PalettePopup:
    """Transient palette window opened from a row fg/bg swatch click."""

    def __init__(self, parent, row, channel, on_color_pick, on_close=None, x_root=None, y_root=None):
        self._parent = parent
        self._on_color_pick = on_color_pick
        self._on_close = on_close
        self._closed = False
        self._window = tk.Toplevel(parent)
        channel_label = "foreground" if channel == "fg" else "background"
        self._window.title(f"Row {row} {channel_label}")

        picker_bg = theme.TILE_PICKER_BG
        self._window.configure(bg=picker_bg)
        self._window.transient(parent)

        shell = tk.Frame(self._window, bg=picker_bg, padx=8, pady=8)
        shell.pack()

        tk.Label(
            shell,
            text=f"Row {row} — {channel_label}",
            bg=picker_bg,
            fg=theme.PANEL_TITLE_FG,
            font=theme.PANEL_TITLE_FONT,
        ).pack(anchor=tk.W, pady=(0, 8))

        self._panel = PalettePanel(shell, window_bg=picker_bg, require_target=False)
        self._panel.pack()
        self._panel.set_target(row, channel)
        self._panel.on_color_pick(self._handle_pick)

        self._window.protocol("WM_DELETE_WINDOW", self.close)
        self._window.bind("<Escape>", lambda _event: self.close())

        self._window.update_idletasks()
        self._place_window(x_root, y_root)

    def _place_window(self, x_root, y_root):
        width = self._window.winfo_width()
        height = self._window.winfo_height()
        if x_root is not None and y_root is not None:
            x = x_root + 12
            y = y_root - height // 2
        else:
            parent_x = self._parent.winfo_rootx()
            parent_y = self._parent.winfo_rooty()
            parent_w = self._parent.winfo_width()
            parent_h = self._parent.winfo_height()
            x = parent_x + (parent_w - width) // 2
            y = parent_y + (parent_h - height) // 2
        self._window.geometry(f"+{x}+{y}")
        self._window.grab_set()
        self._window.focus_force()

    def _handle_pick(self, color_index):
        if self._closed:
            return
        self._window.after_idle(lambda: self._apply_pick(color_index))

    def _apply_pick(self, color_index):
        if self._closed:
            return
        self._on_color_pick(color_index)
        self.close()

    def close(self):
        if self._closed:
            return
        self._closed = True
        window = self._window
        self._window = None
        try:
            window.grab_release()
        except tk.TclError:
            pass
        try:
            window.destroy()
        except tk.TclError:
            pass
        if self._on_close:
            self._on_close()