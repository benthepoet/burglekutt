"""Shared project state for all editor windows."""

from tile_model import (
    METATILE_COUNT,
    SUPERTILE_COUNT,
    TILE_COUNT,
    TILE_SIZE,
    copy_metatile,
    copy_tile,
    default_colors,
    default_tileset,
    empty_metatile,
    empty_pattern,
    empty_supertile,
    empty_tile,
    flags_set,
    metatile_name_for_index,
    supertile_name_for_index,
    tile_name_for_index,
    validate_metatile_name,
    validate_supertile_name,
    validate_tile_name,
)


class ChangeEvent:
    TILE_CHANGED = "tile_changed"
    ACTIVE_TILE_CHANGED = "active_tile_changed"
    METATILE_CHANGED = "metatile_changed"
    ACTIVE_METATILE_CHANGED = "active_metatile_changed"
    SUPERTILE_CHANGED = "supertile_changed"
    ACTIVE_SUPERTILE_CHANGED = "active_supertile_changed"
    PROJECT_LOADED = "project_loaded"

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
        self.active_supertile_index = 0
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

    def get_supertile(self, index):
        if index < 0 or index >= len(self.supertiles):
            raise IndexError("supertile index out of range")
        return self.supertiles[index]

    def get_active_supertile(self):
        if not self.supertiles:
            raise IndexError("no supertiles defined")
        return self.supertiles[self.active_supertile_index]

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

    def set_active_supertile_index(self, index):
        if index < 0 or index >= len(self.supertiles):
            raise IndexError("supertile index out of range")
        if index == self.active_supertile_index:
            return False
        self.active_supertile_index = index
        self.notify(ChangeEvent(ChangeEvent.ACTIVE_SUPERTILE_CHANGED, index))
        return True

    def add_supertile(self):
        if len(self.supertiles) >= SUPERTILE_COUNT:
            raise ValueError("supertile limit reached")
        index = len(self.supertiles)
        self.supertiles.append(empty_supertile(supertile_name_for_index(index)))
        self.active_supertile_index = index
        self.notify(ChangeEvent(ChangeEvent.SUPERTILE_CHANGED, index))

    def remove_supertile(self, index):
        if index < 0 or index >= len(self.supertiles):
            raise IndexError("supertile index out of range")
        del self.supertiles[index]
        if not self.supertiles:
            self.active_supertile_index = 0
        elif self.active_supertile_index >= len(self.supertiles):
            self.active_supertile_index = len(self.supertiles) - 1
        elif index < self.active_supertile_index:
            self.active_supertile_index -= 1
        self.notify(ChangeEvent(ChangeEvent.SUPERTILE_CHANGED, index))
        if self.supertiles:
            self.notify(
                ChangeEvent(
                    ChangeEvent.ACTIVE_SUPERTILE_CHANGED,
                    self.active_supertile_index,
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

    def rename_supertile(self, index, name):
        validated = validate_supertile_name(name)
        supertile = self.get_supertile(index)
        if supertile["name"] == validated:
            return False
        supertile["name"] = validated
        self.notify(ChangeEvent(ChangeEvent.SUPERTILE_CHANGED, index))
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

    def set_supertile_cell(self, super_index, cell_index, metatile_index):
        if metatile_index < 0 or metatile_index >= len(self.metatiles):
            raise IndexError("metatile index out of range")
        supertile = self.get_supertile(super_index)
        if supertile["cells"][cell_index] == metatile_index:
            return False
        supertile["cells"][cell_index] = metatile_index
        self.notify(ChangeEvent(ChangeEvent.SUPERTILE_CHANGED, super_index))
        return True

    def set_pixel(self, row, col, bit, notify=True):
        tile = self.get_active_tile()
        if tile["pattern"][row][col] == bit:
            return False
        tile["pattern"][row][col] = bit
        if notify:
            self.notify(ChangeEvent(ChangeEvent.TILE_CHANGED, self.active_tile_index))
        return True

    def notify_active_tile_changed(self):
        """Emit TILE_CHANGED for the active tile without mutating data."""
        self.notify(ChangeEvent(ChangeEvent.TILE_CHANGED, self.active_tile_index))

    def _validate_color_index(self, value, name):
        if not isinstance(value, int) or not 0 <= value <= 15:
            raise ValueError("{} color out of range".format(name))

    def _validate_row_index(self, row):
        if not isinstance(row, int) or not 0 <= row < TILE_SIZE:
            raise ValueError("row index out of range")

    def set_row_color(self, row, fg=None, bg=None):
        self._validate_row_index(row)
        tile = self.get_active_tile()
        colors = tile["colors"][row]
        changed = False
        if fg is not None:
            self._validate_color_index(fg, "foreground")
            if colors["fg"] != fg:
                colors["fg"] = fg
                changed = True
        if bg is not None:
            self._validate_color_index(bg, "background")
            if colors["bg"] != bg:
                colors["bg"] = bg
                changed = True
        if changed:
            self.notify(ChangeEvent(ChangeEvent.TILE_CHANGED, self.active_tile_index))
        return changed

    def set_all_row_colors(self, fg, bg):
        """Set foreground and background on all scanlines of the active tile."""
        self._validate_color_index(fg, "foreground")
        self._validate_color_index(bg, "background")
        tile = self.get_active_tile()
        changed = False
        for row in range(TILE_SIZE):
            colors = tile["colors"][row]
            if colors["fg"] != fg or colors["bg"] != bg:
                colors["fg"] = fg
                colors["bg"] = bg
                changed = True
        if changed:
            self.notify(ChangeEvent(ChangeEvent.TILE_CHANGED, self.active_tile_index))
        return changed

    def copy_row_colors(self, source_row, dest_rows):
        """Copy fg/bg from source_row to each valid destination row."""
        self._validate_row_index(source_row)
        tile = self.get_active_tile()
        source = tile["colors"][source_row]
        fg = source["fg"]
        bg = source["bg"]
        changed = False
        for dest in dest_rows:
            if not isinstance(dest, int) or not 0 <= dest < TILE_SIZE:
                continue
            if dest == source_row:
                continue
            colors = tile["colors"][dest]
            if colors["fg"] != fg or colors["bg"] != bg:
                colors["fg"] = fg
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

    def load_from_dict(self, data):
        """Replace project data from a normalized project dict."""
        self.tiles = data["tiles"]
        self.metatiles = data["metatiles"]
        self.supertiles = data["supertiles"]
        self.active_tile_index = 0
        self.active_metatile_index = 0 if self.metatiles else 0
        self.active_supertile_index = 0 if self.supertiles else 0
        self.notify(ChangeEvent(ChangeEvent.PROJECT_LOADED))

    def reset(self):
        """Reset to a new empty project."""
        self.tiles = default_tileset()
        self.active_tile_index = 0
        self.metatiles = [empty_metatile(metatile_name_for_index(0))]
        self.active_metatile_index = 0
        self.supertiles = []
        self.active_supertile_index = 0
        self.notify(ChangeEvent(ChangeEvent.PROJECT_LOADED))