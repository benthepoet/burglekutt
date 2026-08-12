import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from image_editor_window import tile_image_cell_at, tile_image_pixel_at


class TestImageEditorGeometry(unittest.TestCase):
    def test_tile_image_cell_at(self):
        scale = 2
        cell = 8 * scale
        self.assertEqual(tile_image_cell_at(0, 0, 4, 3, scale), 0)
        self.assertEqual(tile_image_cell_at(cell, 0, 4, 3, scale), 1)
        self.assertEqual(tile_image_cell_at(0, cell, 4, 3, scale), 4)
        self.assertEqual(tile_image_cell_at(cell * 3, cell * 2, 4, 3, scale), 11)
        self.assertIsNone(tile_image_cell_at(-1, 0, 4, 3, scale))
        self.assertIsNone(tile_image_cell_at(cell * 4, 0, 4, 3, scale))
        self.assertIsNone(tile_image_cell_at(0, cell * 3, 4, 3, scale))

    def test_tile_image_pixel_at(self):
        scale = 2
        cell = 8 * scale
        self.assertEqual(tile_image_pixel_at(0, 0, 4, 3, scale), (0, 0, 0))
        self.assertEqual(tile_image_pixel_at(scale, 0, 4, 3, scale), (0, 0, 1))
        self.assertEqual(tile_image_pixel_at(0, scale, 4, 3, scale), (0, 1, 0))
        self.assertEqual(
            tile_image_pixel_at(cell + scale, cell + scale * 2, 4, 3, scale),
            (5, 2, 1),
        )
        self.assertIsNone(tile_image_pixel_at(cell * 4, 0, 4, 3, scale))


if __name__ == "__main__":
    unittest.main()
