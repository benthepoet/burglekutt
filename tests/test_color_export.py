import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from color_export import encode_color_row, encode_tile_colors
from tile_model import empty_tile


class TestColorExport(unittest.TestCase):
    def test_encode_color_row(self):
        self.assertEqual(encode_color_row(15, 1), 0xF1)

    def test_encode_tile_colors(self):
        tile = empty_tile()
        values = encode_tile_colors(tile)
        self.assertEqual(len(values), 8)
        self.assertEqual(values[0], 0xF1)


if __name__ == "__main__":
    unittest.main()