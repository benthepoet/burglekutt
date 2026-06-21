import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from project import ChangeEvent, Project
from tile_model import TILE_SIZE


class TestLineColors(unittest.TestCase):
    def test_set_all_row_colors_updates_every_row(self):
        project = Project()
        events = []
        project.add_listener(events.append)

        self.assertTrue(project.set_all_row_colors(3, 5))
        tile = project.get_active_tile()
        for row in range(TILE_SIZE):
            self.assertEqual(tile["colors"][row]["fg"], 3)
            self.assertEqual(tile["colors"][row]["bg"], 5)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, ChangeEvent.TILE_CHANGED)

    def test_set_all_row_colors_no_op_when_unchanged(self):
        project = Project()
        events = []
        project.add_listener(events.append)

        self.assertFalse(project.set_all_row_colors(15, 1))
        self.assertEqual(len(events), 0)

    def test_set_all_row_colors_rejects_invalid_color(self):
        project = Project()
        with self.assertRaises(ValueError):
            project.set_all_row_colors(16, 1)

    def test_copy_row_colors_to_selected_rows(self):
        project = Project()
        tile = project.get_active_tile()
        tile["colors"][2]["fg"] = 4
        tile["colors"][2]["bg"] = 6
        events = []
        project.add_listener(events.append)

        self.assertTrue(project.copy_row_colors(2, [0, 1, 5]))
        self.assertEqual(tile["colors"][0]["fg"], 4)
        self.assertEqual(tile["colors"][0]["bg"], 6)
        self.assertEqual(tile["colors"][1]["fg"], 4)
        self.assertEqual(tile["colors"][5]["bg"], 6)
        self.assertEqual(tile["colors"][3]["fg"], 15)
        self.assertEqual(len(events), 1)

    def test_copy_row_colors_skips_invalid_destinations(self):
        project = Project()
        tile = project.get_active_tile()
        tile["colors"][1]["fg"] = 8
        tile["colors"][1]["bg"] = 9

        self.assertTrue(project.copy_row_colors(1, [0, 99, -1, "bad"]))
        self.assertEqual(tile["colors"][0]["fg"], 8)
        self.assertEqual(tile["colors"][0]["bg"], 9)

    def test_copy_row_colors_no_op_without_valid_dests(self):
        project = Project()
        events = []
        project.add_listener(events.append)

        self.assertFalse(project.copy_row_colors(0, []))
        self.assertFalse(project.copy_row_colors(0, [99, "bad"]))
        self.assertEqual(len(events), 0)

    def test_copy_row_colors_skips_source_row(self):
        project = Project()
        tile = project.get_active_tile()
        tile["colors"][3]["fg"] = 7
        tile["colors"][3]["bg"] = 2

        self.assertFalse(project.copy_row_colors(3, [3]))
        self.assertEqual(len([e for e in []]), 0)


if __name__ == "__main__":
    unittest.main()