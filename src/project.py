"""Shared project state for all editor windows."""

from tile_model import default_colors, empty_pattern, empty_tile


class ChangeEvent:
    TILE_CHANGED = "tile_changed"

    def __init__(self, kind, index=0):
        self.kind = kind
        self.index = index


class Project:
    def __init__(self):
        self.tiles = [empty_tile()]
        self.active_tile_index = 0
        self.metatiles = []
        self.supertiles = []
        self._listeners = []

    def get_active_tile(self):
        return self.tiles[self.active_tile_index]

    def add_listener(self, callback):
        self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify(self, event):
        for callback in list(self._listeners):
            callback(event)

    def set_pixel(self, row, col, bit):
        tile = self.get_active_tile()
        if tile["pattern"][row][col] == bit:
            return False
        tile["pattern"][row][col] = bit
        self.notify(ChangeEvent(ChangeEvent.TILE_CHANGED, self.active_tile_index))
        return True

    def set_row_color(self, row, fg=None, bg=None):
        tile = self.get_active_tile()
        colors = tile["colors"][row]
        changed = False
        if fg is not None and colors["fg"] != fg:
            colors["fg"] = fg
            changed = True
        if bg is not None and colors["bg"] != bg:
            colors["bg"] = bg
            changed = True
        if changed:
            self.notify(ChangeEvent(ChangeEvent.TILE_CHANGED, self.active_tile_index))
        return changed

    def clear_active_tile(self, reset_colors=False):
        tile = self.get_active_tile()
        tile["pattern"] = empty_pattern()
        if reset_colors:
            tile["colors"] = default_colors()
        self.notify(ChangeEvent(ChangeEvent.TILE_CHANGED, self.active_tile_index))

    def replace_active_tile(self, tile):
        self.tiles[self.active_tile_index] = tile
        self.notify(ChangeEvent(ChangeEvent.TILE_CHANGED, self.active_tile_index))