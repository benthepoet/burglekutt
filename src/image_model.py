"""Tile image structs, validation, and unique-tile budget checks."""

import copy

from tile_model import TILE_COUNT

TILE_IMAGE_MAX_UNIQUE_TILES = TILE_COUNT
DEFAULT_TILE_IMAGE_NAME = "IMG00"
MAX_TILE_IMAGE_NAME_LEN = 32


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


def copy_tile_image(image):
    """Return a deep copy of a tile image dict."""
    return copy.deepcopy(image)


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


def validate_tile_image_dimensions(width, height):
    """Return validated width/height or raise ValueError."""
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValueError("tile image width and height must be integers")
    if width < 1 or height < 1:
        raise ValueError("tile image width and height must be at least 1")
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