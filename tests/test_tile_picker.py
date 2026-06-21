import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tile_picker import (
    PICKER_CELL_GAP,
    PICKER_COLUMNS,
    PICKER_TILE_SCALE_DEFAULT,
    cell_pixel_size,
    grid_pos_to_index,
    index_to_grid_pos,
    picker_grid_size,
)


class TestTilePicker(unittest.TestCase):
    def test_index_to_grid_pos(self):
        self.assertEqual(index_to_grid_pos(0), (0, 0))
        self.assertEqual(index_to_grid_pos(15), (0, 15))
        self.assertEqual(index_to_grid_pos(16), (1, 0))
        self.assertEqual(index_to_grid_pos(255), (15, 15))

    def test_grid_pos_to_index(self):
        self.assertEqual(grid_pos_to_index(0, 0), 0)
        self.assertEqual(grid_pos_to_index(0, 15), 15)
        self.assertEqual(grid_pos_to_index(15, 15), 255)

    def test_picker_grid_size_default(self):
        cell = cell_pixel_size(PICKER_TILE_SCALE_DEFAULT)
        width, height = picker_grid_size(PICKER_TILE_SCALE_DEFAULT)
        expected = PICKER_COLUMNS * cell + (PICKER_COLUMNS - 1) * PICKER_CELL_GAP
        self.assertEqual(width, expected)
        self.assertEqual(height, expected)


if __name__ == "__main__":
    unittest.main()