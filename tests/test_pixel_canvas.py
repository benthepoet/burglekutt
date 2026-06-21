import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pixel_canvas import hex_color_to_rgb, ppm_bytes_from_pixels


class TestPixelCanvas(unittest.TestCase):
    def test_hex_color_to_rgb(self):
        self.assertEqual(hex_color_to_rgb("#ff8040"), (255, 128, 64))

    def test_ppm_bytes_from_pixels_scales_grid(self):
        pixels = [["#000000", "#ffffff"], ["#ff0000", "#00ff00"]]
        ppm = ppm_bytes_from_pixels(pixels, scale=2)
        self.assertTrue(ppm.startswith(b"P6\n4 4\n255\n"))
        self.assertEqual(len(ppm) - len(b"P6\n4 4\n255\n"), 4 * 4 * 3)


if __name__ == "__main__":
    unittest.main()