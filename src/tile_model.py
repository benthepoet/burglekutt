"""Tile data structures and defaults."""

import copy

TILE_SIZE = 8
DEFAULT_FG = 15
DEFAULT_BG = 1
DEFAULT_TILE_NAME = "TIL00"


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