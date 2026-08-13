"""JSON project save/load."""

import json

from image_model import (
    MAX_TILE_IMAGES,
    empty_tile_image,
    validate_tile_image_dimensions,
    validate_tile_index,
    validate_unique_tile_count,
    validate_unique_tile_image_name,
)
from tile_model import (
    METATILE_COUNT,
    SUPERTILE_CELL_COUNT,
    SUPERTILE_COUNT,
    TILE_COUNT,
    TILE_SIZE,
    default_colors,
    empty_metatile,
    empty_pattern,
    empty_supertile,
    empty_tile,
    metatile_name_for_index,
    supertile_name_for_index,
    tile_name_for_index,
    validate_metatile_name,
    validate_supertile_name,
    validate_tile_name,
)

PROJECT_VERSION = 2


def _coerce_bit(value):
    return 1 if value else 0


def _normalize_pattern(raw):
    pattern = empty_pattern()
    if not isinstance(raw, list):
        return pattern
    for row in range(TILE_SIZE):
        if row >= len(raw):
            break
        src_row = raw[row]
        if not isinstance(src_row, list):
            continue
        for col in range(TILE_SIZE):
            if col >= len(src_row):
                break
            pattern[row][col] = _coerce_bit(src_row[col])
    return pattern


def _normalize_colors(raw):
    colors = default_colors()
    if not isinstance(raw, list):
        return colors
    for row in range(TILE_SIZE):
        if row >= len(raw):
            break
        entry = raw[row]
        if not isinstance(entry, dict):
            continue
        fg = entry.get("fg", colors[row]["fg"])
        bg = entry.get("bg", colors[row]["bg"])
        if isinstance(fg, int) and 0 <= fg <= 15:
            colors[row]["fg"] = fg
        if isinstance(bg, int) and 0 <= bg <= 15:
            colors[row]["bg"] = bg
    return colors


def _normalize_tile(raw, index):
    tile = empty_tile(tile_name_for_index(index))
    if not isinstance(raw, dict):
        return tile
    try:
        tile["name"] = validate_tile_name(raw.get("name", tile["name"]))
    except ValueError:
        tile["name"] = tile_name_for_index(index)
    tile["pattern"] = _normalize_pattern(raw.get("pattern"))
    tile["colors"] = _normalize_colors(raw.get("colors"))
    return tile


def _normalize_metatile(raw, index, tile_count=TILE_COUNT):
    metatile = empty_metatile(metatile_name_for_index(index))
    if not isinstance(raw, dict):
        return metatile
    try:
        metatile["name"] = validate_metatile_name(
            raw.get("name", metatile["name"])
        )
    except ValueError:
        metatile["name"] = metatile_name_for_index(index)
    flags = raw.get("flags", 0)
    if isinstance(flags, int) and 0 <= flags <= 255:
        metatile["flags"] = flags
    cells = raw.get("cells", metatile["cells"])
    if isinstance(cells, list):
        for cell_index in range(4):
            if cell_index >= len(cells):
                break
            value = cells[cell_index]
            if isinstance(value, int) and 0 <= value < tile_count:
                metatile["cells"][cell_index] = value
    return metatile


def _normalize_supertile(raw, index, metatile_count):
    supertile = empty_supertile(supertile_name_for_index(index))
    if not isinstance(raw, dict):
        return supertile
    try:
        supertile["name"] = validate_supertile_name(
            raw.get("name", supertile["name"])
        )
    except ValueError:
        supertile["name"] = supertile_name_for_index(index)
    cells = raw.get("cells", supertile["cells"])
    if isinstance(cells, list):
        for cell_index in range(SUPERTILE_CELL_COUNT):
            if cell_index >= len(cells):
                break
            value = cells[cell_index]
            if (
                isinstance(value, int)
                and metatile_count > 0
                and 0 <= value < metatile_count
            ):
                supertile["cells"][cell_index] = value
    return supertile


def _normalize_tile_image(raw, images_so_far):
    if not isinstance(raw, dict):
        raise ValueError("tile image must be an object")
    name = validate_unique_tile_image_name(
        raw.get("name", "IMG00"), images_so_far
    )
    width, height = validate_tile_image_dimensions(
        raw.get("width"), raw.get("height")
    )
    raw_cells = raw.get("cells", [])
    if not isinstance(raw_cells, list):
        raw_cells = []
    cells = []
    expected = width * height
    for index in range(expected):
        if index < len(raw_cells):
            try:
                cells.append(validate_tile_index(raw_cells[index]))
                continue
            except ValueError:
                pass
        cells.append(0)
    validate_unique_tile_count(cells)
    image = empty_tile_image(name, width, height)
    image["cells"] = cells
    return image


def project_to_dict(project):
    """Serialize a Project to a versioned JSON-friendly dict."""
    return {
        "version": PROJECT_VERSION,
        "tiles": project.tiles,
        "metatiles": project.metatiles,
        "supertiles": project.supertiles,
        "tile_images": project.tile_images,
    }


def parse_project_dict(data):
    """Parse and validate project JSON data."""
    if not isinstance(data, dict):
        raise ValueError("project root must be an object")

    version = data.get("version", 1)
    if not isinstance(version, int) or version < 1:
        raise ValueError("unsupported project version")

    raw_tiles = data.get("tiles", [])
    tiles = []
    if isinstance(raw_tiles, list):
        for index in range(TILE_COUNT):
            if index < len(raw_tiles):
                tiles.append(_normalize_tile(raw_tiles[index], index))
            else:
                tiles.append(empty_tile(tile_name_for_index(index)))
    else:
        tiles = [empty_tile(tile_name_for_index(index)) for index in range(TILE_COUNT)]

    raw_metatiles = data.get("metatiles", [])
    if not isinstance(raw_metatiles, list):
        raw_metatiles = []
    if len(raw_metatiles) > METATILE_COUNT:
        raise ValueError("too many metatiles")
    metatiles = [
        _normalize_metatile(raw_metatiles[index], index)
        for index in range(len(raw_metatiles))
    ]

    raw_supertiles = data.get("supertiles", [])
    if not isinstance(raw_supertiles, list):
        raw_supertiles = []
    if len(raw_supertiles) > SUPERTILE_COUNT:
        raise ValueError("too many supertiles")
    metatile_count = len(metatiles)
    supertiles = [
        _normalize_supertile(raw_supertiles[index], index, metatile_count)
        for index in range(len(raw_supertiles))
    ]

    raw_images = data.get("tile_images", [])
    if not isinstance(raw_images, list):
        raw_images = []
    if len(raw_images) > MAX_TILE_IMAGES:
        raise ValueError("too many tile images")
    tile_images = []
    for raw in raw_images:
        tile_images.append(_normalize_tile_image(raw, tile_images))

    return {
        "version": PROJECT_VERSION,
        "tiles": tiles,
        "metatiles": metatiles,
        "supertiles": supertiles,
        "tile_images": tile_images,
    }


def load_project(path):
    """Load a project JSON file and return a normalized dict."""
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return parse_project_dict(data)


def save_project(path, project):
    """Write a project JSON file."""
    payload = project_to_dict(project)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")