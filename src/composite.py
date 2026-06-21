"""Resolve tile pixels for thumbnails and composite previews."""

from palette import resolve_pixel_color
from tile_model import (
    METATILE_PIXEL_SIZE,
    SUPERTILE_COLS,
    SUPERTILE_PIXEL_HEIGHT,
    SUPERTILE_PIXEL_WIDTH,
    TILE_SIZE,
)


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


def resolve_metatile_pixels(metatile, tiles):
    """Return a 16x16 grid of hex colors from a 2x2 metatile."""
    pixels = []
    for row in range(16):
        meta_row = row // TILE_SIZE
        tile_row = row % TILE_SIZE
        row_pixels = []
        for col in range(16):
            meta_col = col // TILE_SIZE
            tile_col = col % TILE_SIZE
            cell_index = meta_row * 2 + meta_col
            tile = tiles[metatile["cells"][cell_index]]
            row_pixels.append(resolve_pixel_color(tile, tile_row, tile_col))
        pixels.append(row_pixels)
    return pixels


def metatile_references_tile(metatile, tile_index):
    return tile_index in metatile["cells"]


def metatiles_referencing_tile(metatiles, tile_index):
    return [
        index
        for index, metatile in enumerate(metatiles)
        if metatile_references_tile(metatile, tile_index)
    ]


def resolve_supertile_pixels(supertile, metatiles, tiles):
    """Return a 64x64 grid of hex colors from a 4x4 supertile."""
    meta_cache = {}
    pixels = []
    for row in range(SUPERTILE_PIXEL_HEIGHT):
        super_row = row // METATILE_PIXEL_SIZE
        meta_row = row % METATILE_PIXEL_SIZE
        row_pixels = []
        for col in range(SUPERTILE_PIXEL_WIDTH):
            super_col = col // METATILE_PIXEL_SIZE
            meta_col = col % METATILE_PIXEL_SIZE
            cell_index = super_row * SUPERTILE_COLS + super_col
            meta_index = supertile["cells"][cell_index]
            if meta_index not in meta_cache:
                meta_cache[meta_index] = resolve_metatile_pixels(
                    metatiles[meta_index],
                    tiles,
                )
            row_pixels.append(meta_cache[meta_index][meta_row][meta_col])
        pixels.append(row_pixels)
    return pixels


def supertile_references_metatile(supertile, metatile_index):
    return metatile_index in supertile["cells"]


def supertiles_referencing_metatile(supertiles, metatile_index):
    return [
        index
        for index, supertile in enumerate(supertiles)
        if supertile_references_metatile(supertile, metatile_index)
    ]