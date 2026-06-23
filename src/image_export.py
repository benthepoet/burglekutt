"""Tile-image dedupe, local remap, and export bytes + assembly."""

from asm_export import _format_bytes, render_tile_color_line, render_tile_pattern_line
from asm_format_schema import load_format
from color_export import encode_tile_colors
from image_model import (
    TILE_IMAGE_MAX_UNIQUE_TILES,
    TileImageUniqueTileLimitError,
    unique_tile_indices,
    validate_tile_image,
)
from pattern_export import encode_tile_pattern


def build_local_remap(cells):
    """Build local tile order and remapped layout indices.

    Returns (ordered_global_indices, global_to_local, local_cells).
    Local order follows first appearance in row-major scan.
    """
    ordered_globals = unique_tile_indices(cells)
    if len(ordered_globals) > TILE_IMAGE_MAX_UNIQUE_TILES:
        raise TileImageUniqueTileLimitError(
            "tile image uses {} unique tiles; memory-reduced Graphics II allows at most {} "
            "(not the 768-tile full Graphics II layout)".format(
                len(ordered_globals), TILE_IMAGE_MAX_UNIQUE_TILES
            )
        )
    global_to_local = {
        global_index: local_index
        for local_index, global_index in enumerate(ordered_globals)
    }
    local_cells = [global_to_local[global_index] for global_index in cells]
    return ordered_globals, global_to_local, local_cells


def build_image_export(image, tiles):
    """Return export payload for one tile image.

    Payload keys: ordered_globals, local_cells, local_tiles, unique_count.
    """
    validate_tile_image(image)
    ordered_globals, _global_to_local, local_cells = build_local_remap(image["cells"])
    local_tiles = [tiles[global_index] for global_index in ordered_globals]
    return {
        "ordered_globals": ordered_globals,
        "local_cells": local_cells,
        "local_tiles": local_tiles,
        "unique_count": len(ordered_globals),
        "width": image["width"],
        "height": image["height"],
        "name": image["name"],
    }


def image_pattern_bytes(local_tiles):
    """Return N × 8 pattern bytes for the deduped local tileset."""
    result = bytearray()
    for tile in local_tiles:
        result.extend(encode_tile_pattern(tile))
    return bytes(result)


def image_color_bytes(local_tiles):
    """Return N × 8 color-table bytes for the deduped local tileset."""
    result = bytearray()
    for tile in local_tiles:
        result.extend(encode_tile_colors(tile))
    return bytes(result)


def image_map_bytes(local_cells, width):
    """Return W × H layout bytes grouped row-major."""
    result = bytearray()
    for row_start in range(0, len(local_cells), width):
        row = local_cells[row_start : row_start + width]
        for value in row:
            result.append(value & 0xFF)
    return bytes(result)


def image_export_bytes(image, tiles):
    """Return concatenated pattern + color + map bytes for one tile image."""
    payload = build_image_export(image, tiles)
    return (
        image_pattern_bytes(payload["local_tiles"])
        + image_color_bytes(payload["local_tiles"])
        + image_map_bytes(payload["local_cells"], payload["width"])
    )


def _image_label(name, suffix):
    return "{}_{}".format(name, suffix)


def render_image_map(fmt, image_name, local_cells, width, height):
    """Render the layout map as one BYTE row per image row."""
    lines = [_image_label(image_name, "MAP")]
    for row in range(height):
        row_start = row * width
        row_values = local_cells[row_start : row_start + width]
        line = _format_bytes(fmt, row_values)
        lines.append(
            "{}   {} row {}".format(line, fmt["comment_prefix"], row)
        )
    lines.append(_image_label(image_name, "MAPEND"))
    return "\n".join(lines)


def render_tile_image_export(image, tiles, fmt=None):
    """Return PATTERNS + COLORS + MAP assembly text for one tile image."""
    if fmt is None:
        fmt = load_format()
    payload = build_image_export(image, tiles)
    image_name = payload["name"]
    lines = [_image_label(image_name, "PATTERNS")]
    for local_index, tile in enumerate(payload["local_tiles"]):
        global_index = payload["ordered_globals"][local_index]
        comment = "{} (local {}, global TIL{:02X})".format(
            tile["name"], local_index, global_index
        )
        pattern_line = render_tile_pattern_line(fmt, tile)
        lines.append(
            "{}   {} {}".format(pattern_line, fmt["comment_prefix"], comment)
        )

    lines.append("")
    lines.append(_image_label(image_name, "COLORS"))
    for local_index, tile in enumerate(payload["local_tiles"]):
        global_index = payload["ordered_globals"][local_index]
        comment = "{} (local {}, global TIL{:02X}) color table".format(
            tile["name"], local_index, global_index
        )
        color_line = render_tile_color_line(fmt, tile)
        lines.append(
            "{}   {} {}".format(color_line, fmt["comment_prefix"], comment)
        )

    lines.append("")
    lines.append(
        render_image_map(
            fmt,
            image_name,
            payload["local_cells"],
            payload["width"],
            payload["height"],
        )
    )
    return "\n".join(lines)