import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tile_canvas import (
    TILE_PIXEL_SCALE_DEFAULT,
    TILE_PIXEL_SCALE_MAX,
    TILE_PIXEL_SCALE_MIN,
    canvas_pixel_size,
    clamp_scale,
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


if __name__ == "__main__":
    unittest.main()