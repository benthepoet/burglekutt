import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from asm_export import (
    render_metatile_export,
    render_supertile_export,
    render_tileset_export,
)
from project import Project
from tile_model import empty_supertile, metatile_name_for_index


class TestAsmExport(unittest.TestCase):
    def test_tileset_export_contains_patterns_and_colors(self):
        project = Project()
        text = render_tileset_export(project.tiles)
        self.assertIn("PATTERNS", text)
        self.assertIn("COLORS", text)
        self.assertIn("BYTE >f1", text)

    def test_metatile_export_contains_flags_and_cells(self):
        project = Project()
        project.metatiles[0]["flags"] = 0x01
        text = render_metatile_export(project.metatiles)
        self.assertIn("METAS", text)
        self.assertIn("METASEND", text)
        self.assertIn("BYTE >01", text)

    def test_supertile_export_contains_rows(self):
        project = Project()
        project.add_supertile()
        text = render_supertile_export(project.supertiles)
        self.assertIn("SUPERS", text)
        self.assertIn("SUPERSEND", text)
        self.assertIn("row 0", text)

    def test_empty_supertile_export_message(self):
        text = render_supertile_export([])
        self.assertIn("No supertiles", text)


if __name__ == "__main__":
    unittest.main()