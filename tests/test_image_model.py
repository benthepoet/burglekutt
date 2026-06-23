import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from image_model import (
    TILE_IMAGE_MAX_UNIQUE_TILES,
    TileImageUniqueTileLimitError,
    count_unique_tiles,
    empty_tile_image,
    unique_tile_indices,
    validate_tile_image,
    validate_unique_tile_count,
)


class TestImageModel(unittest.TestCase):
    def test_empty_tile_image_defaults(self):
        image = empty_tile_image()
        self.assertEqual(image["name"], "IMG00")
        self.assertEqual(image["width"], 1)
        self.assertEqual(image["height"], 1)
        self.assertEqual(image["cells"], [0])

    def test_unique_tile_indices_first_appearance_order(self):
        cells = [0, 1, 0, 2, 1, 3]
        self.assertEqual(unique_tile_indices(cells), [0, 1, 2, 3])

    def test_count_unique_tiles(self):
        self.assertEqual(count_unique_tiles([0, 0, 1, 1, 2]), 3)

    def test_validate_unique_tile_count_allows_256(self):
        cells = list(range(TILE_IMAGE_MAX_UNIQUE_TILES))
        self.assertEqual(validate_unique_tile_count(cells), TILE_IMAGE_MAX_UNIQUE_TILES)

    def test_validate_unique_tile_count_rejects_over_limit(self):
        cells = [0, 1, 2]
        with self.assertRaises(TileImageUniqueTileLimitError) as ctx:
            validate_unique_tile_count(cells, limit=2)
        self.assertIn("3", str(ctx.exception))
        self.assertIn("2", str(ctx.exception))
        self.assertIn("768", str(ctx.exception))

    def test_validate_tile_image_allows_all_256_globals(self):
        image = {
            "name": "TITLE",
            "width": 16,
            "height": 16,
            "cells": list(range(TILE_IMAGE_MAX_UNIQUE_TILES)),
        }
        validate_tile_image(image)
        self.assertEqual(count_unique_tiles(image["cells"]), TILE_IMAGE_MAX_UNIQUE_TILES)

    def test_large_grid_with_few_unique_tiles_is_valid(self):
        image = empty_tile_image("LOGO", width=32, height=24)
        validate_tile_image(image)
        self.assertEqual(len(image["cells"]), 32 * 24)
        self.assertEqual(count_unique_tiles(image["cells"]), 1)


if __name__ == "__main__":
    unittest.main()