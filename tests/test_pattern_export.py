import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pattern_export import encode_pattern, encode_pattern_row, encode_tile_pattern
from tile_model import empty_tile


class TestPatternExport(unittest.TestCase):
    def test_encode_row_msb_left(self):
        row = [1, 0, 0, 0, 0, 0, 0, 1]
        self.assertEqual(encode_pattern_row(row), 0x81)

    def test_encode_pattern_eight_rows(self):
        tile = empty_tile()
        tile["pattern"][0] = [1, 0, 0, 0, 0, 0, 0, 1]
        tile["pattern"][4] = [0, 1, 1, 1, 1, 1, 1, 0]
        values = encode_tile_pattern(tile)
        self.assertEqual(len(values), 8)
        self.assertEqual(values[0], 0x81)
        self.assertEqual(values[4], 0x7E)
        self.assertEqual(values[1], 0)

    def test_encode_pattern_grid(self):
        pattern = [[0] * 8 for _ in range(8)]
        pattern[3][7] = 1
        self.assertEqual(encode_pattern(pattern)[3], 0x01)


if __name__ == "__main__":
    unittest.main()