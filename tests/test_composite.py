import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from composite import resolve_tile_pixels, tile_is_empty
from palette import rgb_to_hex
from tile_model import TILE_SIZE, empty_tile


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


if __name__ == "__main__":
    unittest.main()