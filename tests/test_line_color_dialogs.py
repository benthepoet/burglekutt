import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from line_color_dialogs import default_fill_colors
from tile_model import DEFAULT_BG, DEFAULT_FG, empty_tile


class TestLineColorDialogs(unittest.TestCase):
    def test_default_fill_colors_uses_active_row(self):
        tile = empty_tile()
        tile["colors"][4]["fg"] = 6
        tile["colors"][4]["bg"] = 8
        fg, bg = default_fill_colors(tile, active_row=4)
        self.assertEqual(fg, 6)
        self.assertEqual(bg, 8)

    def test_default_fill_colors_fallback(self):
        tile = empty_tile()
        fg, bg = default_fill_colors(tile, active_row=None)
        self.assertEqual(fg, DEFAULT_FG)
        self.assertEqual(bg, DEFAULT_BG)


if __name__ == "__main__":
    unittest.main()