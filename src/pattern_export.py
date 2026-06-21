"""8×8 pattern grid → TMS9918 pattern bytes."""

from tile_model import TILE_SIZE


def encode_pattern_row(row):
    """Encode one row of eight bits; MSB is the leftmost pixel."""
    if len(row) != TILE_SIZE:
        raise ValueError("pattern row must have {} columns".format(TILE_SIZE))
    byte = 0
    for col, bit in enumerate(row):
        if bit not in (0, 1):
            raise ValueError("pattern bits must be 0 or 1")
        if bit:
            byte |= 1 << (7 - col)
    return byte


def encode_pattern(pattern):
    """Encode an 8×8 pattern grid to eight bytes."""
    if len(pattern) != TILE_SIZE:
        raise ValueError("pattern must have {} rows".format(TILE_SIZE))
    return [encode_pattern_row(row) for row in pattern]


def encode_tile_pattern(tile):
    """Encode one tile dict's pattern field."""
    return encode_pattern(tile["pattern"])