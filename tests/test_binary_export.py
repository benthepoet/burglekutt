import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from binary_export import (
    color_table_bytes,
    metatile_table_bytes,
    pattern_table_bytes,
    supertile_table_bytes,
    tileset_bytes,
)
from project import Project
from tile_model import TILE_COUNT, empty_supertile, metatile_name_for_index


class TestBinaryExport(unittest.TestCase):
    def test_pattern_table_size(self):
        project = Project()
        data = pattern_table_bytes(project.tiles)
        self.assertEqual(len(data), TILE_COUNT * 8)

    def test_color_table_size(self):
        project = Project()
        data = color_table_bytes(project.tiles)
        self.assertEqual(len(data), TILE_COUNT * 8)

    def test_tileset_bytes_concatenates_tables(self):
        project = Project()
        data = tileset_bytes(project.tiles)
        self.assertEqual(len(data), TILE_COUNT * 16)

    def test_metatile_table_bytes(self):
        project = Project()
        project.metatiles[0]["flags"] = 0x03
        project.metatiles[0]["cells"] = [1, 2, 3, 4]
        data = metatile_table_bytes(project.metatiles)
        self.assertEqual(data, bytes([0x03, 1, 2, 3, 4]))

    def test_supertile_table_bytes(self):
        supertiles = [empty_supertile(metatile_name_for_index(0))]
        supertiles[0]["cells"] = list(range(16))
        data = supertile_table_bytes(supertiles)
        self.assertEqual(len(data), 16)
        self.assertEqual(data[0], 0)
        self.assertEqual(data[15], 15)


if __name__ == "__main__":
    unittest.main()