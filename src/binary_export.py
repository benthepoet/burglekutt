"""Raw byte output for pattern, color, and index tables."""

from color_export import encode_tile_colors
from pattern_export import encode_tile_pattern


def pattern_table_bytes(tiles):
    """Return 256 × 8 pattern bytes."""
    result = bytearray()
    for tile in tiles:
        result.extend(encode_tile_pattern(tile))
    return bytes(result)


def color_table_bytes(tiles):
    """Return 256 × 8 color-table bytes."""
    result = bytearray()
    for tile in tiles:
        result.extend(encode_tile_colors(tile))
    return bytes(result)


def tileset_bytes(tiles):
    """Return pattern table followed by color table (4096 bytes)."""
    return pattern_table_bytes(tiles) + color_table_bytes(tiles)


def metatile_table_bytes(metatiles):
    """Return N × 5 bytes (flags + four tile indices per metatile)."""
    result = bytearray()
    for metatile in metatiles:
        result.append(metatile["flags"] & 0xFF)
        for cell in metatile["cells"]:
            result.append(cell & 0xFF)
    return bytes(result)


def supertile_table_bytes(supertiles):
    """Return M × 16 bytes (row-major 4×4 metatile indices)."""
    result = bytearray()
    for supertile in supertiles:
        for cell in supertile["cells"]:
            result.append(cell & 0xFF)
    return bytes(result)