"""Tile data structures and defaults."""

import copy

TILE_SIZE = 8
TILE_COUNT = 256
DEFAULT_FG = 15
DEFAULT_BG = 1
DEFAULT_TILE_NAME = "TIL00"
MAX_TILE_NAME_LEN = 32

METATILE_COUNT = 256
METATILE_CELL_COUNT = 4
METATILE_PIXEL_SIZE = 16
DEFAULT_METATILE_NAME = "MT00"

SUPERTILE_COUNT = 256
SUPERTILE_COLS = 4
SUPERTILE_ROWS = 4
SUPERTILE_CELL_COUNT = SUPERTILE_COLS * SUPERTILE_ROWS
SUPERTILE_PIXEL_WIDTH = SUPERTILE_COLS * METATILE_PIXEL_SIZE
SUPERTILE_PIXEL_HEIGHT = SUPERTILE_ROWS * METATILE_PIXEL_SIZE
DEFAULT_SUPERTILE_NAME = "ST00"

METATILE_FLAG_SOLID = 0x01
METATILE_FLAG_HURT = 0x02
METATILE_FLAG_WATER = 0x04
METATILE_FLAG_DOOR = 0x08
METATILE_FLAG_STAIRS = 0x10

METATILE_FLAGS = (
    (METATILE_FLAG_SOLID, "S"),
    (METATILE_FLAG_HURT, "H"),
    (METATILE_FLAG_WATER, "W"),
    (METATILE_FLAG_DOOR, "D"),
    (METATILE_FLAG_STAIRS, "T"),
)


def empty_pattern():
    """Return an 8x8 pattern grid of zeros."""
    return [[0] * TILE_SIZE for _ in range(TILE_SIZE)]


def default_colors():
    """Return eight scanline color entries (fg=15, bg=1)."""
    return [{"fg": DEFAULT_FG, "bg": DEFAULT_BG} for _ in range(TILE_SIZE)]


def empty_tile(name=DEFAULT_TILE_NAME):
    """Return a new empty tile dict."""
    return {
        "name": name,
        "pattern": empty_pattern(),
        "colors": default_colors(),
    }


def copy_tile(tile):
    """Return a deep copy of a tile dict."""
    return copy.deepcopy(tile)


def tile_name_for_index(index):
    """Return the default tile name for a slot index (TIL00..TILFF)."""
    if index < 0 or index >= TILE_COUNT:
        raise ValueError("tile index out of range")
    return "TIL{:02X}".format(index)


def validate_tile_name(name):
    """Return a stripped tile name or raise ValueError."""
    if not isinstance(name, str):
        raise ValueError("tile name must be a string")
    name = name.strip()
    if not name:
        raise ValueError("tile name must not be empty")
    if len(name) > MAX_TILE_NAME_LEN:
        raise ValueError("tile name is too long")
    return name


def default_tileset():
    """Return 256 empty tiles with default slot names."""
    return [empty_tile(tile_name_for_index(index)) for index in range(TILE_COUNT)]


def empty_metatile(name=DEFAULT_METATILE_NAME):
    """Return a new empty metatile dict."""
    return {
        "name": name,
        "flags": 0,
        "cells": [0, 0, 0, 0],
    }


def copy_metatile(metatile):
    """Return a deep copy of a metatile dict."""
    return copy.deepcopy(metatile)


def metatile_name_for_index(index):
    """Return the default metatile name for a slot index (MT00..MTFF)."""
    if index < 0 or index >= METATILE_COUNT:
        raise ValueError("metatile index out of range")
    return "MT{:02X}".format(index)


def validate_metatile_name(name):
    """Return a stripped metatile name or raise ValueError."""
    if not isinstance(name, str):
        raise ValueError("metatile name must be a string")
    name = name.strip()
    if not name:
        raise ValueError("metatile name must not be empty")
    if len(name) > MAX_TILE_NAME_LEN:
        raise ValueError("metatile name is too long")
    return name


def flags_has(flags, mask):
    return bool(flags & mask)


def flags_set(flags, mask, enabled):
    if enabled:
        return flags | mask
    return flags & ~mask


def flags_summary(flags):
    """Return a compact label for enabled metatile flags."""
    labels = [label for mask, label in METATILE_FLAGS if flags_has(flags, mask)]
    return "".join(labels)


def empty_supertile(name=DEFAULT_SUPERTILE_NAME):
    """Return a new empty supertile dict."""
    return {
        "name": name,
        "cells": [0] * SUPERTILE_CELL_COUNT,
    }


def copy_supertile(supertile):
    """Return a deep copy of a supertile dict."""
    return copy.deepcopy(supertile)


def supertile_name_for_index(index):
    """Return the default supertile name for a slot index (ST00..STFF)."""
    if index < 0 or index >= SUPERTILE_COUNT:
        raise ValueError("supertile index out of range")
    return "ST{:02X}".format(index)


def validate_supertile_name(name):
    """Return a stripped supertile name or raise ValueError."""
    if not isinstance(name, str):
        raise ValueError("supertile name must be a string")
    name = name.strip()
    if not name:
        raise ValueError("supertile name must not be empty")
    if len(name) > MAX_TILE_NAME_LEN:
        raise ValueError("supertile name is too long")
    return name