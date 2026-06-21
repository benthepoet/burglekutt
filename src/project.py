"""Shared project state for all editor windows."""

from tile_model import (
    METATILE_COUNT,
    TILE_COUNT,
    copy_metatile,
    copy_tile,
    default_colors,
    default_tileset,
    empty_metatile,
    empty_pattern,
    empty_tile,
    flags_set,
    metatile_name_for_index,
    tile_name_for_index,
    validate_metatile_name,
    validate_tile_name,
)


class ChangeEvent:
    TILE_CHANGED = "tile_changed"
    ACTIVE_TILE_CHANGED = "active_tile_changed"
    METATILE_CHANGED = "metatile_changed"
    ACTIVE_METATILE_CHANGED = "active_metatile_changed"

    def __init__(self, kind, index=0):
        self.kind = kind
        self.index = index


class Project:
    def __init__(self):
        self.tiles = default_tileset()
        self.active_tile_index = 0
        self.metatiles = [empty_metatile(metatile_name_for_index(0))]
        self.active_metatile_index = 0
        self.supertiles = []
        self._listeners = []

    def get_tile(self, index):
        if index < 0 or index >= TILE_COUNT:
            raise IndexError("tile index out of range")
        return self.tiles[index]

    def get_active_tile(self):
        return self.tiles[self.active_tile_index]

    def get_metatile(self, index):
        if index < 0 or index >= len(self.metatiles):
            raise IndexError("metatile index out of range")
        return self.metatiles[index]

    def get_active_metatile(self):
        if not self.metatiles:
            raise IndexError("no metatiles defined")
        return self.metatiles[self.active_metatile_index]

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

    def set_active_metatile_index(self, index):
        if index < 0 or index >= len(self.metatiles):
            raise IndexError("metatile index out of range")
        if index == self.active_metatile_index:
            return False
        self.active_metatile_index = index
        self.notify(ChangeEvent(ChangeEvent.ACTIVE_METATILE_CHANGED, index))
        return True

    def add_metatile(self):
        if len(self.metatiles) >= METATILE_COUNT:
            raise ValueError("metatile limit reached")
        index = len(self.metatiles)
        self.metatiles.append(empty_metatile(metatile_name_for_index(index)))
        self.active_metatile_index = index
        self.notify(ChangeEvent(ChangeEvent.METATILE_CHANGED, index))
        self.notify(ChangeEvent(ChangeEvent.ACTIVE_METATILE_CHANGED, index))

    def remove_metatile(self, index):
        if index < 0 or index >= len(self.metatiles):
            raise IndexError("metatile index out of range")
        del self.metatiles[index]
        if not self.metatiles:
            self.active_metatile_index = 0
        elif self.active_metatile_index >= len(self.metatiles):
            self.active_metatile_index = len(self.metatiles) - 1
        elif index < self.active_metatile_index:
            self.active_metatile_index -= 1
        self.notify(ChangeEvent(ChangeEvent.METATILE_CHANGED, index))
        if self.metatiles:
            self.notify(
                ChangeEvent(
                    ChangeEvent.ACTIVE_METATILE_CHANGED,
                    self.active_metatile_index,
                )
            )

    def supertiles_referencing_metatile(self, metatile_index):
        refs = []
        for super_index, supertile in enumerate(self.supertiles):
            if metatile_index in supertile["cells"]:
                refs.append(super_index)
        return refs

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

    def rename_metatile(self, index, name):
        validated = validate_metatile_name(name)
        metatile = self.get_metatile(index)
        if metatile["name"] == validated:
            return False
        metatile["name"] = validated
        self.notify(ChangeEvent(ChangeEvent.METATILE_CHANGED, index))
        return True

    def set_metatile_cell(self, meta_index, cell_index, tile_index):
        if tile_index < 0 or tile_index >= TILE_COUNT:
            raise IndexError("tile index out of range")
        metatile = self.get_metatile(meta_index)
        if metatile["cells"][cell_index] == tile_index:
            return False
        metatile["cells"][cell_index] = tile_index
        self.notify(ChangeEvent(ChangeEvent.METATILE_CHANGED, meta_index))
        return True

    def set_metatile_flag(self, meta_index, mask, enabled):
        metatile = self.get_metatile(meta_index)
        new_flags = flags_set(metatile["flags"], mask, enabled)
        if new_flags == metatile["flags"]:
            return False
        metatile["flags"] = new_flags
        self.notify(ChangeEvent(ChangeEvent.METATILE_CHANGED, meta_index))
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