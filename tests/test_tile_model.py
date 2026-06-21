import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tile_model import (
    DEFAULT_TILE_NAME,
    METATILE_FLAG_HURT,
    METATILE_FLAG_SOLID,
    SUPERTILE_CELL_COUNT,
    SUPERTILE_PIXEL_HEIGHT,
    SUPERTILE_PIXEL_WIDTH,
    TILE_COUNT,
    TILE_SIZE,
    copy_tile,
    default_colors,
    default_tileset,
    empty_metatile,
    empty_pattern,
    empty_supertile,
    empty_tile,
    flags_has,
    flags_set,
    flags_summary,
    metatile_name_for_index,
    supertile_name_for_index,
    tile_name_for_index,
    validate_tile_name,
)


class TestTileModel(unittest.TestCase):
    def test_empty_pattern_size(self):
        pattern = empty_pattern()
        self.assertEqual(len(pattern), TILE_SIZE)
        for row in pattern:
            self.assertEqual(len(row), TILE_SIZE)
            self.assertTrue(all(bit == 0 for bit in row))

    def test_default_colors(self):
        colors = default_colors()
        self.assertEqual(len(colors), TILE_SIZE)
        for entry in colors:
            self.assertEqual(entry, {"fg": 15, "bg": 1})

    def test_empty_tile_defaults(self):
        tile = empty_tile()
        self.assertEqual(tile["name"], DEFAULT_TILE_NAME)
        self.assertEqual(len(tile["pattern"]), TILE_SIZE)
        self.assertEqual(len(tile["colors"]), TILE_SIZE)

    def test_copy_tile_is_independent(self):
        tile = empty_tile()
        copied = copy_tile(tile)
        copied["pattern"][0][0] = 1
        copied["colors"][0]["fg"] = 3
        self.assertEqual(tile["pattern"][0][0], 0)
        self.assertEqual(tile["colors"][0]["fg"], 15)

    def test_tile_name_for_index(self):
        self.assertEqual(tile_name_for_index(0), "TIL00")
        self.assertEqual(tile_name_for_index(42), "TIL2A")
        self.assertEqual(tile_name_for_index(255), "TILFF")

    def test_default_tileset_has_256_named_slots(self):
        tiles = default_tileset()
        self.assertEqual(len(tiles), TILE_COUNT)
        self.assertEqual(tiles[0]["name"], "TIL00")
        self.assertEqual(tiles[255]["name"], "TILFF")

    def test_validate_tile_name(self):
        self.assertEqual(validate_tile_name("  ROCK  "), "ROCK")
        with self.assertRaises(ValueError):
            validate_tile_name("   ")

    def test_empty_metatile_defaults(self):
        metatile = empty_metatile()
        self.assertEqual(metatile["name"], "MT00")
        self.assertEqual(metatile["flags"], 0)
        self.assertEqual(metatile["cells"], [0, 0, 0, 0])

    def test_metatile_name_for_index(self):
        self.assertEqual(metatile_name_for_index(0), "MT00")
        self.assertEqual(metatile_name_for_index(255), "MTFF")

    def test_flags_helpers(self):
        flags = flags_set(0, METATILE_FLAG_SOLID, True)
        flags = flags_set(flags, METATILE_FLAG_HURT, True)
        self.assertTrue(flags_has(flags, METATILE_FLAG_SOLID))
        self.assertEqual(flags_summary(flags), "SH")

    def test_empty_supertile_defaults(self):
        supertile = empty_supertile()
        self.assertEqual(supertile["name"], "ST00")
        self.assertEqual(len(supertile["cells"]), SUPERTILE_CELL_COUNT)
        self.assertEqual(supertile["cells"], [0] * SUPERTILE_CELL_COUNT)

    def test_supertile_geometry_constants(self):
        self.assertEqual(SUPERTILE_CELL_COUNT, 16)
        self.assertEqual(SUPERTILE_PIXEL_WIDTH, 64)
        self.assertEqual(SUPERTILE_PIXEL_HEIGHT, 64)

    def test_supertile_name_for_index(self):
        self.assertEqual(supertile_name_for_index(0), "ST00")
        self.assertEqual(supertile_name_for_index(255), "STFF")


if __name__ == "__main__":
    unittest.main()