import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tile_canvas import (
    SWATCH_GAP,
    SWATCH_SIDE_PADDING,
    TILE_PIXEL_SCALE_DEFAULT,
    TILE_PIXEL_SCALE_MAX,
    TILE_PIXEL_SCALE_MIN,
    canvas_pixel_size,
    clamp_scale,
    pixel_at,
    swatch_column_width,
    swatch_layout,
    swatch_size,
)
from tile_model import TILE_SIZE


class TestTileCanvas(unittest.TestCase):
    def test_canvas_pixel_size_default(self):
        width, height = canvas_pixel_size(TILE_PIXEL_SCALE_DEFAULT)
        self.assertEqual(width, TILE_SIZE * 32)
        self.assertEqual(height, TILE_SIZE * 32)

    def test_canvas_pixel_size_min(self):
        width, height = canvas_pixel_size(TILE_PIXEL_SCALE_MIN)
        self.assertEqual(width, 192)
        self.assertEqual(height, 192)

    def test_clamp_scale(self):
        self.assertEqual(clamp_scale(10), TILE_PIXEL_SCALE_MIN)
        self.assertEqual(clamp_scale(100), TILE_PIXEL_SCALE_MAX)
        self.assertEqual(clamp_scale(32), 32)

    def test_pixel_at_maps_coordinates(self):
        self.assertEqual(pixel_at(0, 0, 32), (0, 0))
        self.assertEqual(pixel_at(31, 31, 32), (0, 0))
        self.assertEqual(pixel_at(32, 32, 32), (1, 1))
        self.assertEqual(pixel_at(999, 999, 32), (7, 7))

    def test_swatch_size_respects_minimum(self):
        self.assertEqual(swatch_size(32), 20)
        self.assertEqual(swatch_size(48), 24)

    def test_swatch_layout_includes_side_padding(self):
        size, fg_x, bg_x = swatch_layout(32)
        self.assertEqual(fg_x, SWATCH_SIDE_PADDING)
        self.assertEqual(bg_x, SWATCH_SIDE_PADDING + size + SWATCH_GAP)
        self.assertEqual(swatch_column_width(32), 2 * SWATCH_SIDE_PADDING + 2 * size + SWATCH_GAP)


if __name__ == "__main__":
    unittest.main()