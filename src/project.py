"""Shared project state for all editor windows."""

from tile_model import (
    TILE_COUNT,
    copy_tile,
    default_colors,
    default_tileset,
    empty_pattern,
    empty_tile,
    tile_name_for_index,
    validate_tile_name,
)


class ChangeEvent:
    TILE_CHANGED = "tile_changed"
    ACTIVE_TILE_CHANGED = "active_tile_changed"

    def __init__(self, kind, index=0):
        self.kind = kind
        self.index = index


class Project:
    def __init__(self):
        self.tiles = default_tileset()
        self.active_tile_index = 0
        self.metatiles = []
        self.supertiles = []
        self._listeners = []

    def get_tile(self, index):
        if index < 0 or index >= TILE_COUNT:
            raise IndexError("tile index out of range")
        return self.tiles[index]

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

    def set_active_tile_index(self, index):
        if index < 0 or index >= TILE_COUNT:
            raise IndexError("tile index out of range")
        if index == self.active_tile_index:
            return False
        self.active_tile_index = index
        self.notify(ChangeEvent(ChangeEvent.ACTIVE_TILE_CHANGED, index))
        return True

    def duplicate_tile(self, src_index, dst_index):
        if src_index < 0 or src_index >= TILE_COUNT:
            raise IndexError("source tile index out of range")
        if dst_index < 0 or dst_index >= TILE_COUNT:
            raise IndexError("destination tile index out of range")
        copied = copy_tile(self.tiles[src_index])
        copied["name"] = tile_name_for_index(dst_index)
        self.tiles[dst_index] = copied
        self.notify(ChangeEvent(ChangeEvent.TILE_CHANGED, dst_index))

    def rename_tile(self, index, name):
        validated = validate_tile_name(name)
        tile = self.get_tile(index)
        if tile["name"] == validated:
            return False
        tile["name"] = validated
        self.notify(ChangeEvent(ChangeEvent.TILE_CHANGED, index))
        return True

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