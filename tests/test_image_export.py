import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from image_export import (
    build_image_export,
    build_local_remap,
    image_export_bytes,
    render_tile_image_export,
)
from image_model import TILE_IMAGE_MAX_UNIQUE_TILES
from tile_model import default_tileset, empty_tile


class TestImageExport(unittest.TestCase):
    def setUp(self):
        self.tiles = default_tileset()
        self.tiles[1] = empty_tile("TIL01")
        self.tiles[1]["pattern"][0][0] = 1

    def test_build_local_remap_first_appearance(self):
        image = {
            "name": "TITLE",
            "width": 2,
            "height": 2,
            "cells": [0, 1, 0, 1],
        }
        ordered, _mapping, local_cells = build_local_remap(image["cells"])
        self.assertEqual(ordered, [0, 1])
        self.assertEqual(local_cells, [0, 1, 0, 1])

    def test_build_image_export_allows_256_unique_tiles(self):
        image = {
            "name": "FULL",
            "width": 16,
            "height": 16,
            "cells": list(range(TILE_IMAGE_MAX_UNIQUE_TILES)),
        }
        payload = build_image_export(image, self.tiles)
        self.assertEqual(payload["unique_count"], TILE_IMAGE_MAX_UNIQUE_TILES)
        self.assertEqual(len(payload["local_tiles"]), TILE_IMAGE_MAX_UNIQUE_TILES)

    def test_image_export_bytes_sizes(self):
        image = {
            "name": "TITLE",
            "width": 2,
            "height": 2,
            "cells": [0, 1, 0, 1],
        }
        payload = build_image_export(image, self.tiles)
        binary = image_export_bytes(image, self.tiles)
        pattern_size = len(payload["local_tiles"]) * 8
        color_size = len(payload["local_tiles"]) * 8
        map_size = image["width"] * image["height"]
        self.assertEqual(len(binary), pattern_size + color_size + map_size)

    def test_render_tile_image_export_includes_sections(self):
        image = {
            "name": "TITLE",
            "width": 2,
            "height": 1,
            "cells": [0, 1],
        }
        text = render_tile_image_export(image, self.tiles)
        self.assertIn("TITLE_PATTERNS", text)
        self.assertIn("TITLE_COLORS", text)
        self.assertIn("TITLE_MAP", text)
        self.assertIn("TITLE_MAPEND", text)


if __name__ == "__main__":
    unittest.main()