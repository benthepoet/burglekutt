"""Per-scanline fg/bg colors → TMS9918 color-table bytes."""

from tile_model import TILE_SIZE


def encode_color_row(fg, bg):
    """Pack foreground and background nibbles into one byte."""
    if not 0 <= fg <= 15:
        raise ValueError("foreground color out of range")
    if not 0 <= bg <= 15:
        raise ValueError("background color out of range")
    return (fg << 4) | bg


def encode_tile_colors(tile):
    """Encode one tile dict's colors field to eight bytes."""
    colors = tile["colors"]
    if len(colors) != TILE_SIZE:
        raise ValueError("tile must have {} color rows".format(TILE_SIZE))
    return [
        encode_color_row(row["fg"], row["bg"])
        for row in colors
    ]