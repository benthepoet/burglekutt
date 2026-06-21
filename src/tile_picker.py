"""16x16 tile picker window for selecting tileset slots."""

import tkinter as tk

from composite import resolve_tile_pixels
from project import ChangeEvent
import theme

PICKER_TILE_SCALE_DEFAULT = 3
PICKER_TILE_SCALE_MIN = 2
PICKER_CELL_GAP = 2
PICKER_COLUMNS = 16
PICKER_ROWS = 16
def clamp_picker_scale(scale):
    return max(PICKER_TILE_SCALE_MIN, scale)


def index_to_grid_pos(index):
    """Return (row, col) for a tile index in the 16x16 grid."""
    return index // PICKER_COLUMNS, index % PICKER_COLUMNS


def grid_pos_to_index(row, col):
    """Return the tile index for a grid row/col."""
    return row * PICKER_COLUMNS + col


def cell_pixel_size(scale):
    return 8 * clamp_picker_scale(scale)


def picker_grid_size(scale):
    """Return (width, height) of the full 16x16 picker grid in pixels."""
    cell = cell_pixel_size(scale)
    stride = cell + PICKER_CELL_GAP
    extent = PICKER_COLUMNS * cell + (PICKER_COLUMNS - 1) * PICKER_CELL_GAP
    return extent, extent


class TilePickerWindow:
    """Non-modal tile picker for edit or one-shot assignment flows."""

    def __init__(
        self,
        parent,
        project,
        mode="edit",
        title=None,
        on_select=None,
        on_close=None,
    ):
        self.parent = parent
        self.project = project
        self.mode = mode
        self.on_select = on_select
        self._on_close = on_close
        self.scale = PICKER_TILE_SCALE_DEFAULT

        self.window = tk.Toplevel(parent)
        if title is None:
            title = "Select Tile for Cell" if mode == "assign" else "Select Tile"
        self.window.title("burglekutt — {}".format(title))
        self._picker_bg = theme.TILE_PICKER_BG
        self.window.configure(bg=self._picker_bg)
        self.window.transient(parent)

        shell = tk.Frame(self.window, bg=self._picker_bg, padx=8, pady=8)
        shell.pack(fill=tk.BOTH, expand=True)

        grid_width, grid_height = picker_grid_size(self.scale)
        self.canvas = tk.Canvas(
            shell,
            width=grid_width,
            height=grid_height,
            bg=self._picker_bg,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)

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
        self.canvas.delete("all")
        cell = cell_pixel_size(self.scale)
        stride = cell + PICKER_CELL_GAP

        for index in range(PICKER_ROWS * PICKER_COLUMNS):
            row, col = index_to_grid_pos(index)
            x0 = col * stride
            y0 = row * stride
            x1 = x0 + cell
            y1 = y0 + cell

            tile = self.project.get_tile(index)
            pixels = resolve_tile_pixels(tile)
            pixel_scale = self.scale
            for prow in range(8):
                for pcol in range(8):
                    px0 = x0 + pcol * pixel_scale
                    py0 = y0 + prow * pixel_scale
                    px1 = px0 + pixel_scale
                    py1 = py0 + pixel_scale
                    self.canvas.create_rectangle(
                        px0,
                        py0,
                        px1,
                        py1,
                        fill=pixels[prow][pcol],
                        outline="",
                    )

            if index == self.project.active_tile_index and self.mode == "edit":
                self.canvas.create_rectangle(
                    x0 - 1,
                    y0 - 1,
                    x1 + 1,
                    y1 + 1,
                    outline=theme.ACCENT_BORDER,
                    width=3,
                )

    def _index_at(self, x, y):
        cell = cell_pixel_size(self.scale)
        stride = cell + PICKER_CELL_GAP
        col = int(x // stride)
        row = int(y // stride)
        if col < 0 or col >= PICKER_COLUMNS or row < 0 or row >= PICKER_ROWS:
            return None
        if x - col * stride >= cell or y - row * stride >= cell:
            return None
        return grid_pos_to_index(row, col)

    def _on_click(self, event):
        index = self._index_at(event.x, event.y)
        if index is None:
            return
        if self.mode == "assign":
            if self.on_select is not None:
                self.on_select(index)
            self.close()
            return
        self.project.set_active_tile_index(index)

    def _on_motion(self, event):
        index = self._index_at(event.x, event.y)
        if index is None:
            self._update_status()
            return
        tile = self.project.get_tile(index)
        self._status_label.config(text="Tile {} / {}".format(index, tile["name"]))

    def _on_leave(self, _event=None):
        self._update_status()

    def _update_status(self):
        if self.mode == "assign":
            self._status_label.config(text="Click a destination tile slot")
            return
        tile = self.project.get_active_tile()
        index = self.project.active_tile_index
        self._status_label.config(text="Tile {} / {}".format(index, tile["name"]))

    def _on_project_change(self, event):
        if event.kind in (ChangeEvent.TILE_CHANGED, ChangeEvent.ACTIVE_TILE_CHANGED):
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