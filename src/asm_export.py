"""Assembly text rendering from project data and format templates."""

from asm_format_schema import load_format
from color_export import encode_tile_colors
from pattern_export import encode_tile_pattern


def _format_bytes(fmt, values):
    """Render a BYTE line from integer values."""
    prefix = fmt["hex_prefix"]
    parts = ["{}{:02x}".format(prefix, value & 0xFF) for value in values]
    return "{}{} {}".format(fmt["indent"], fmt["byte_keyword"], ",".join(parts))


def _render_template(fmt, name, **kwargs):
    template = fmt["templates"].get(name)
    if template is None:
        raise KeyError("missing template: {}".format(name))
    return template.format(
        indent=fmt["indent"],
        comment_prefix=fmt["comment_prefix"],
        byte_keyword=fmt["byte_keyword"],
        **kwargs,
    )


def render_tile_pattern_line(fmt, tile, index=None):
    """Render one tile's pattern as a BYTE line."""
    values = encode_tile_pattern(tile)
    comment = tile["name"]
    if index is not None:
        comment = "{} (tile {})".format(comment, index)
    line = _format_bytes(fmt, values)
    return "{}   {} {}".format(line, fmt["comment_prefix"], comment)


def render_tile_color_line(fmt, tile, index=None):
    """Render one tile's color table as a BYTE line."""
    values = encode_tile_colors(tile)
    comment = "{} color table".format(tile["name"])
    if index is not None:
        comment = "{} (tile {}) color table".format(tile["name"], index)
    line = _format_bytes(fmt, values)
    return "{}   {} {}".format(line, fmt["comment_prefix"], comment)


def render_patterns(fmt, tiles, active_index=None):
    """Render the full PATTERNS block."""
    labels = fmt["labels"]
    lines = [labels["patterns"]]
    for index, tile in enumerate(tiles):
        lines.append(render_tile_pattern_line(fmt, tile, index))
    return "\n".join(lines)


def render_colors(fmt, tiles):
    """Render the full COLORS block."""
    labels = fmt["labels"]
    lines = [labels["colors"]]
    for index, tile in enumerate(tiles):
        lines.append(render_tile_color_line(fmt, tile, index))
    return "\n".join(lines)


def render_metatile_block(fmt, metatile, index=None):
    """Render one metatile (flags byte + cell indices)."""
    lines = []
    flags_line = _format_bytes(fmt, [metatile["flags"]])
    comment = metatile["name"]
    if index is not None:
        comment = "{} (metatile {}) flags".format(comment, index)
    lines.append("{}   {} {}".format(flags_line, fmt["comment_prefix"], comment))

    cells_line = _format_bytes(fmt, metatile["cells"])
    cell_comment = "{} tiles".format(metatile["name"])
    if index is not None:
        cell_comment = "{} (metatile {}) tiles".format(metatile["name"], index)
    lines.append("{}   {} {}".format(cells_line, fmt["comment_prefix"], cell_comment))
    return "\n".join(lines)


def render_metas(fmt, metatiles):
    """Render the METAS block for all defined metatiles."""
    labels = fmt["labels"]
    lines = [labels["metas"]]
    for index, metatile in enumerate(metatiles):
        lines.append(render_metatile_block(fmt, metatile, index))
    lines.append(labels["metas_end"])
    return "\n".join(lines)


def render_supertile_block(fmt, supertile, index=None):
    """Render one supertile as four BYTE rows."""
    lines = []
    cells = supertile["cells"]
    for row in range(4):
        row_values = cells[row * 4 : (row + 1) * 4]
        line = _format_bytes(fmt, row_values)
        comment = "{} row {}".format(supertile["name"], row)
        if index is not None:
            comment = "{} (supertile {}) row {}".format(supertile["name"], index, row)
        lines.append("{}   {} {}".format(line, fmt["comment_prefix"], comment))
    return "\n".join(lines)


def render_supers(fmt, supertiles):
    """Render the SUPERS block for all defined supertiles."""
    labels = fmt["labels"]
    lines = [labels["supers"]]
    for index, supertile in enumerate(supertiles):
        lines.append(render_supertile_block(fmt, supertile, index))
    lines.append(labels["supers_end"])
    return "\n".join(lines)


def render_tileset_export(tiles, fmt=None):
    """Return PATTERNS + COLORS assembly text for the tileset."""
    if fmt is None:
        fmt = load_format()
    return "\n\n".join([render_patterns(fmt, tiles), render_colors(fmt, tiles)])


def render_metatile_export(metatiles, fmt=None):
    """Return METAS assembly text."""
    if fmt is None:
        fmt = load_format()
    if not metatiles:
        return "; No metatiles defined"
    return render_metas(fmt, metatiles)


def render_supertile_export(supertiles, fmt=None):
    """Return SUPERS assembly text."""
    if fmt is None:
        fmt = load_format()
    if not supertiles:
        return "; No supertiles defined"
    return render_supers(fmt, supertiles)