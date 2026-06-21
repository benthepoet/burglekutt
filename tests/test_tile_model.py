import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tile_model import (
    DEFAULT_TILE_NAME,
    TILE_SIZE,
    copy_tile,
    default_colors,
    empty_pattern,
    empty_tile,
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


if __name__ == "__main__":
    unittest.main()