"""Tile image structs, validation, and unique-tile budget checks."""

import copy

from tile_model import TILE_COUNT

TILE_IMAGE_MAX_UNIQUE_TILES = TILE_COUNT
TILE_IMAGE_MAX_CELLS = TILE_COUNT
DEFAULT_TILE_IMAGE_NAME = "IMG00"
DEFAULT_TILE_IMAGE_WIDTH = 16
DEFAULT_TILE_IMAGE_HEIGHT = 16
MAX_TILE_IMAGE_NAME_LEN = 32
MAX_TILE_IMAGES = TILE_COUNT


class TileImageUniqueTileLimitError(ValueError):
    """Raised when a tile image references more than 256 unique global tiles."""


def empty_tile_image(name=DEFAULT_TILE_IMAGE_NAME, width=1, height=1):
    """Return a new tile image dict with all cells set to tile index 0."""
    width, height = validate_tile_image_dimensions(width, height)
    return {
        "name": name,
        "width": width,
        "height": height,
        "cells": [0] * (width * height),
    }


def default_tile_image():
    """Return the default 16×16 IMG00 tile image."""
    return empty_tile_image(
        DEFAULT_TILE_IMAGE_NAME,
        DEFAULT_TILE_IMAGE_WIDTH,
        DEFAULT_TILE_IMAGE_HEIGHT,
    )


def copy_tile_image(image):
    """Return a deep copy of a tile image dict."""
    return copy.deepcopy(image)


def tile_image_name_for_index(index):
    """Return the default tile image name for a slot index (IMG00..IMGFF)."""
    if index < 0 or index >= MAX_TILE_IMAGES:
        raise ValueError("tile image index out of range")
    return "IMG{:02X}".format(index)


def unused_tile_image_name(images):
    """Return the next unused default tile image name."""
    used = {image["name"] for image in images}
    for index in range(MAX_TILE_IMAGES):
        name = tile_image_name_for_index(index)
        if name not in used:
            return name
    raise ValueError("tile image name limit reached")


def validate_tile_image_name(name):
    """Return a stripped tile image name or raise ValueError."""
    if not isinstance(name, str):
        raise ValueError("tile image name must be a string")
    name = name.strip()
    if not name:
        raise ValueError("tile image name must not be empty")
    if len(name) > MAX_TILE_IMAGE_NAME_LEN:
        raise ValueError("tile image name is too long")
    return name


def validate_unique_tile_image_name(name, images, skip_index=None):
    """Validate a name and reject duplicates in images."""
    name = validate_tile_image_name(name)
    for index, image in enumerate(images):
        if skip_index is not None and index == skip_index:
            continue
        if image["name"] == name:
            raise ValueError("tile image name already exists")
    return name


def validate_tile_image_dimensions(width, height):
    """Return validated width/height or raise ValueError."""
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValueError("tile image width and height must be integers")
    if width < 1 or height < 1:
        raise ValueError("tile image width and height must be at least 1")
    cell_count = width * height
    if cell_count > TILE_IMAGE_MAX_CELLS:
        raise ValueError(
            "tile image is {} tiles ({}×{}); memory-reduced Graphics II allows at most {} "
            "tiles (not a larger grid that would need more than 256 unique tiles)".format(
                cell_count, width, height, TILE_IMAGE_MAX_CELLS
            )
        )
    return width, height


def validate_tile_index(index):
    """Return a validated global tile index or raise ValueError."""
    if not isinstance(index, int):
        raise ValueError("tile index must be an integer")
    if index < 0 or index >= TILE_COUNT:
        raise ValueError("tile index out of range")
    return index


def unique_tile_indices(cells):
    """Return unique global tile indices in first-appearance row-major order."""
    seen = []
    seen_set = set()
    for index in cells:
        validate_tile_index(index)
        if index not in seen_set:
            seen.append(index)
            seen_set.add(index)
    return seen


def count_unique_tiles(cells):
    """Return how many distinct global tile indices appear in cells."""
    return len(unique_tile_indices(cells))


def validate_unique_tile_count(cells, *, limit=TILE_IMAGE_MAX_UNIQUE_TILES):
    """Raise TileImageUniqueTileLimitError if cells use more than limit unique tiles."""
    unique_count = count_unique_tiles(cells)
    if unique_count > limit:
        raise TileImageUniqueTileLimitError(
            "tile image uses {} unique tiles; memory-reduced Graphics II allows at most {} "
            "(not the 768-tile full Graphics II layout)".format(
                unique_count, limit
            )
        )
    return unique_count


def validate_tile_image(image):
    """Validate a tile image dict and return it unchanged."""
    if not isinstance(image, dict):
        raise ValueError("tile image must be a dict")
    name = validate_tile_image_name(image.get("name", ""))
    width, height = validate_tile_image_dimensions(
        image.get("width"), image.get("height")
    )
    cells = image.get("cells")
    if not isinstance(cells, list):
        raise ValueError("tile image cells must be a list")
    expected = width * height
    if len(cells) != expected:
        raise ValueError(
            "tile image cells length must be width * height (expected {}, got {})".format(
                expected, len(cells)
            )
        )
    for index in cells:
        validate_tile_index(index)
    validate_unique_tile_count(cells)
    return image


def assign_tile_image_cell(image, cell_index, tile_index, *, limit=TILE_IMAGE_MAX_UNIQUE_TILES):
    """Assign a global tile index to a cell, enforcing the unique-tile budget."""
    cells = list(image["cells"])
    if cell_index < 0 or cell_index >= len(cells):
        raise IndexError("tile image cell index out of range")
    tile_index = validate_tile_index(tile_index)
    cells[cell_index] = tile_index
    validate_unique_tile_count(cells, limit=limit)
    image["cells"] = cells
    return image


def next_unreferenced_tile_index(cells):
    """Return the lowest tileset index not used in cells, or None if all 256 are used."""
    used = set(unique_tile_indices(cells))
    for index in range(TILE_COUNT):
        if index not in used:
            return index
    return None


def ensure_unique_cell_tile(image, cell_index):
    """Give a shared cell its own tileset slot so drawing does not edit other cells.

    Returns (tile_index, source_index). source_index is the tile to copy from
    when a new slot was allocated; None if the cell already had a private tile
    or the 256-unique budget is exhausted (paint the shared tile in place).
    """
    cells = image["cells"]
    if cell_index < 0 or cell_index >= len(cells):
        raise IndexError("tile image cell index out of range")
    current = validate_tile_index(cells[cell_index])
    if cells.count(current) <= 1:
        return current, None
    free = next_unreferenced_tile_index(cells)
    if free is None:
        return current, None
    cells = list(cells)
    cells[cell_index] = free
    image["cells"] = cells
    return free, current


def resize_tile_image(image, width, height, fill=0):
    """Resize a tile image, copying overlapping cells and filling new ones."""
    width, height = validate_tile_image_dimensions(width, height)
    fill = validate_tile_index(fill)
    old_width = image["width"]
    old_height = image["height"]
    old_cells = image["cells"]
    cells = []
    for row in range(height):
        for col in range(width):
            if row < old_height and col < old_width:
                cells.append(old_cells[row * old_width + col])
            else:
                cells.append(fill)
    validate_unique_tile_count(cells)
    image["width"] = width
    image["height"] = height
    image["cells"] = cells
    return image