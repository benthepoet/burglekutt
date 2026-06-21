import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from palette import resolve_pixel_color, rgb_to_hex
from tile_model import empty_tile


class TestPalette(unittest.TestCase):
    def test_rgb_to_hex_white(self):
        self.assertEqual(rgb_to_hex(15), "#ffffff")

    def test_rgb_to_hex_transparent_placeholder(self):
        self.assertEqual(rgb_to_hex(0), "#888888")

    def test_resolve_pixel_color_uses_fg_for_bit_one(self):
        tile = empty_tile()
        tile["pattern"][2][3] = 1
        tile["colors"][2] = {"fg": 7, "bg": 1}
        self.assertEqual(resolve_pixel_color(tile, 2, 3), rgb_to_hex(7))

    def test_resolve_pixel_color_uses_bg_for_bit_zero(self):
        tile = empty_tile()
        tile["pattern"][2][3] = 0
        tile["colors"][2] = {"fg": 7, "bg": 4}
        self.assertEqual(resolve_pixel_color(tile, 2, 3), rgb_to_hex(4))


if __name__ == "__main__":
    unittest.main()