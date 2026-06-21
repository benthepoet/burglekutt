"""Resolve tile pixels for thumbnails and composite previews."""

from palette import resolve_pixel_color
from tile_model import TILE_SIZE


def resolve_tile_pixels(tile):
    """Return an 8x8 grid of hex colors resolved from pattern + line colors."""
    pixels = []
    for row in range(TILE_SIZE):
        row_pixels = []
        for col in range(TILE_SIZE):
            row_pixels.append(resolve_pixel_color(tile, row, col))
        pixels.append(row_pixels)
    return pixels


def tile_is_empty(tile):
    """Return True when every pattern bit in the tile is zero."""
    return all(bit == 0 for row in tile["pattern"] for bit in row)