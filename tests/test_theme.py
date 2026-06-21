import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import theme


class TestTheme(unittest.TestCase):
    def test_style_prefix_per_window_tint(self):
        self.assertEqual(theme.style_prefix(theme.TILESET_WINDOW_BG), "Tileset")
        self.assertEqual(theme.style_prefix(theme.METATILE_WINDOW_BG), "Metatile")
        self.assertEqual(theme.style_prefix(theme.SUPERTILE_WINDOW_BG), "Supertile")
        self.assertEqual(theme.style_prefix(theme.TILE_PICKER_BG), "Picker")

    def test_ttk_style_uses_namespaced_prefix(self):
        self.assertEqual(
            theme.ttk_style(theme.METATILE_WINDOW_BG, "TLabelframe"),
            "Metatile.TLabelframe",
        )
        self.assertEqual(
            theme.ttk_style(theme.SUPERTILE_WINDOW_BG, "TButton"),
            "Supertile.TButton",
        )

    def test_window_styles_exposes_widget_style_names(self):
        styles = theme.window_styles(theme.TILESET_WINDOW_BG)
        self.assertEqual(styles.labelframe, "Tileset.TLabelframe")
        self.assertEqual(styles.button, "Tileset.TButton")


if __name__ == "__main__":
    unittest.main()