import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from image_model import (
    TILE_IMAGE_MAX_CELLS,
    TILE_IMAGE_MAX_UNIQUE_TILES,
    TileImageUniqueTileLimitError,
    assign_tile_image_cell,
    count_unique_tiles,
    empty_tile_image,
    ensure_unique_cell_tile,
    next_unreferenced_tile_index,
    resize_tile_image,
    tile_image_name_for_index,
    unique_tile_indices,
    unused_tile_image_name,
    validate_tile_image,
    validate_unique_tile_count,
    validate_unique_tile_image_name,
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

    def test_full_256_cell_grid_is_valid(self):
        image = empty_tile_image("LOGO", width=16, height=16)
        validate_tile_image(image)
        self.assertEqual(len(image["cells"]), TILE_IMAGE_MAX_CELLS)
        self.assertEqual(count_unique_tiles(image["cells"]), 1)

    def test_dimensions_reject_more_than_256_cells(self):
        with self.assertRaises(ValueError) as ctx:
            empty_tile_image("TITLE", width=32, height=24)
        self.assertIn("768", str(ctx.exception))
        self.assertIn("256", str(ctx.exception))
        with self.assertRaises(ValueError):
            resize_tile_image(empty_tile_image("IMG", width=8, height=8), 32, 24)

    def test_assign_tile_image_cell(self):
        image = empty_tile_image("IMG", width=2, height=1)
        assign_tile_image_cell(image, 1, 7)
        self.assertEqual(image["cells"], [0, 7])

    def test_assign_tile_image_cell_rejects_over_limit(self):
        image = empty_tile_image("IMG", width=3, height=1)
        image["cells"] = [0, 1, 0]
        with self.assertRaises(TileImageUniqueTileLimitError):
            assign_tile_image_cell(image, 2, 2, limit=2)
        self.assertEqual(image["cells"], [0, 1, 0])

    def test_resize_tile_image_preserves_overlap(self):
        image = empty_tile_image("IMG", width=2, height=2)
        image["cells"] = [1, 2, 3, 4]
        resize_tile_image(image, 3, 2)
        self.assertEqual(image["width"], 3)
        self.assertEqual(image["height"], 2)
        self.assertEqual(image["cells"], [1, 2, 0, 3, 4, 0])
        resize_tile_image(image, 2, 1)
        self.assertEqual(image["cells"], [1, 2])

    def test_ensure_unique_cell_tile_forks_shared_cell(self):
        image = empty_tile_image("IMG", width=2, height=1)
        tile_index, source = ensure_unique_cell_tile(image, 0)
        self.assertEqual(source, 0)
        self.assertEqual(tile_index, 1)
        self.assertEqual(image["cells"], [1, 0])
        tile_index, source = ensure_unique_cell_tile(image, 0)
        self.assertIsNone(source)
        self.assertEqual(tile_index, 1)

    def test_ensure_unique_cell_tile_keeps_shared_when_budget_full(self):
        image = {
            "name": "IMG",
            "width": TILE_IMAGE_MAX_UNIQUE_TILES + 1,
            "height": 1,
            "cells": list(range(TILE_IMAGE_MAX_UNIQUE_TILES)) + [0],
        }
        self.assertIsNone(next_unreferenced_tile_index(image["cells"]))
        tile_index, source = ensure_unique_cell_tile(image, TILE_IMAGE_MAX_UNIQUE_TILES)
        self.assertEqual(tile_index, 0)
        self.assertIsNone(source)
        self.assertEqual(image["cells"][-1], 0)

    def test_unused_tile_image_name_skips_taken(self):
        images = [empty_tile_image("IMG00"), empty_tile_image("IMG01")]
        self.assertEqual(unused_tile_image_name(images), "IMG02")
        self.assertEqual(tile_image_name_for_index(15), "IMG0F")

    def test_validate_unique_tile_image_name(self):
        images = [empty_tile_image("TITLE"), empty_tile_image("LOGO")]
        self.assertEqual(validate_unique_tile_image_name("HUD", images), "HUD")
        self.assertEqual(
            validate_unique_tile_image_name("TITLE", images, skip_index=0),
            "TITLE",
        )
        with self.assertRaises(ValueError):
            validate_unique_tile_image_name("LOGO", images)


if __name__ == "__main__":
    unittest.main()