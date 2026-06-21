import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from composite import (
    metatile_references_tile,
    metatiles_referencing_tile,
    resolve_metatile_pixels,
    resolve_supertile_pixels,
    resolve_tile_pixels,
    supertile_references_metatile,
    supertiles_referencing_metatile,
    tile_is_empty,
)
from palette import rgb_to_hex
from tile_model import (
    SUPERTILE_PIXEL_HEIGHT,
    SUPERTILE_PIXEL_WIDTH,
    TILE_SIZE,
    empty_metatile,
    empty_supertile,
    empty_tile,
)


class TestComposite(unittest.TestCase):
    def test_resolve_tile_pixels_uses_fg_and_bg(self):
        tile = empty_tile()
        tile["pattern"][0][0] = 1
        tile["pattern"][1][1] = 0
        tile["colors"][0] = {"fg": 7, "bg": 1}
        tile["colors"][1] = {"fg": 7, "bg": 4}
        pixels = resolve_tile_pixels(tile)
        self.assertEqual(len(pixels), TILE_SIZE)
        self.assertEqual(len(pixels[0]), TILE_SIZE)
        self.assertEqual(pixels[0][0], rgb_to_hex(7))
        self.assertEqual(pixels[1][1], rgb_to_hex(4))

    def test_tile_is_empty(self):
        self.assertTrue(tile_is_empty(empty_tile()))

    def test_tile_is_not_empty_when_pattern_has_bits(self):
        tile = empty_tile()
        tile["pattern"][3][2] = 1
        self.assertFalse(tile_is_empty(tile))

    def test_resolve_metatile_pixels(self):
        tiles = [empty_tile() for _ in range(4)]
        tiles[0]["pattern"][0][0] = 1
        tiles[0]["colors"][0] = {"fg": 7, "bg": 1}
        tiles[3]["pattern"][7][7] = 1
        tiles[3]["colors"][7] = {"fg": 4, "bg": 1}
        metatile = empty_metatile()
        metatile["cells"] = [0, 1, 2, 3]
        pixels = resolve_metatile_pixels(metatile, tiles)
        self.assertEqual(len(pixels), 16)
        self.assertEqual(pixels[0][0], rgb_to_hex(7))
        self.assertEqual(pixels[15][15], rgb_to_hex(4))

    def test_metatiles_referencing_tile(self):
        metatiles = [
            empty_metatile(),
            empty_metatile(),
        ]
        metatiles[0]["cells"] = [1, 2, 3, 4]
        metatiles[1]["cells"] = [5, 1, 0, 0]
        self.assertTrue(metatile_references_tile(metatiles[0], 2))
        self.assertEqual(metatiles_referencing_tile(metatiles, 1), [0, 1])

    def test_resolve_supertile_pixels(self):
        tiles = [empty_tile() for _ in range(5)]
        tiles[0]["pattern"][0][0] = 1
        tiles[0]["colors"][0] = {"fg": 7, "bg": 1}
        tiles[4]["pattern"][7][7] = 1
        tiles[4]["colors"][7] = {"fg": 4, "bg": 1}
        metatiles = [empty_metatile() for _ in range(5)]
        metatiles[0]["cells"] = [0, 1, 2, 3]
        metatiles[4]["cells"] = [4, 4, 4, 4]
        supertile = empty_supertile()
        supertile["cells"] = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 4]
        pixels = resolve_supertile_pixels(supertile, metatiles, tiles)
        self.assertEqual(len(pixels), SUPERTILE_PIXEL_HEIGHT)
        self.assertEqual(len(pixels[0]), SUPERTILE_PIXEL_WIDTH)
        self.assertEqual(pixels[0][0], rgb_to_hex(7))
        self.assertEqual(pixels[63][63], rgb_to_hex(4))

    def test_supertiles_referencing_metatile(self):
        supertiles = [empty_supertile(), empty_supertile()]
        supertiles[0]["cells"][0] = 2
        supertiles[1]["cells"][15] = 2
        self.assertTrue(supertile_references_metatile(supertiles[0], 2))
        self.assertEqual(supertiles_referencing_metatile(supertiles, 2), [0, 1])


if __name__ == "__main__":
    unittest.main()