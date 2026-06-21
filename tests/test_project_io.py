import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from project import Project
from project_io import (
    PROJECT_VERSION,
    load_project,
    parse_project_dict,
    project_to_dict,
    save_project,
)
from tile_model import TILE_COUNT, tile_name_for_index


class TestProjectIO(unittest.TestCase):
    def test_round_trip_dict(self):
        project = Project()
        project.set_pixel(0, 0, 1)
        project.metatiles[0]["flags"] = 0x05
        project.add_supertile()

        data = project_to_dict(project)
        self.assertEqual(data["version"], PROJECT_VERSION)
        self.assertEqual(len(data["tiles"]), TILE_COUNT)

        restored = Project()
        restored.load_from_dict(parse_project_dict(data))
        self.assertEqual(
            restored.get_active_tile()["pattern"][0][0],
            project.get_active_tile()["pattern"][0][0],
        )
        self.assertEqual(restored.metatiles[0]["flags"], 0x05)
        self.assertEqual(len(restored.supertiles), 1)

    def test_save_and_load_file(self):
        project = Project()
        project.tiles[2]["name"] = "WALL"
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.json")
            save_project(path, project)
            data = load_project(path)
            self.assertEqual(data["tiles"][2]["name"], "WALL")

    def test_load_pads_missing_tiles(self):
        data = parse_project_dict({"version": 1, "tiles": []})
        self.assertEqual(len(data["tiles"]), TILE_COUNT)
        self.assertEqual(data["tiles"][0]["name"], tile_name_for_index(0))

    def test_reject_too_many_metatiles(self):
        metatiles = [{"name": "MT{:02X}".format(i), "flags": 0, "cells": [0, 0, 0, 0]} for i in range(257)]
        with self.assertRaises(ValueError):
            parse_project_dict({"version": 1, "metatiles": metatiles})


if __name__ == "__main__":
    unittest.main()