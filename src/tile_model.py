"""Tile data structures and defaults."""

import copy

TILE_SIZE = 8
TILE_COUNT = 256
DEFAULT_FG = 15
DEFAULT_BG = 1
DEFAULT_TILE_NAME = "TIL00"
MAX_TILE_NAME_LEN = 32


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