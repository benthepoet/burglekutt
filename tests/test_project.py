import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from project import ChangeEvent, Project
from tile_model import DEFAULT_TILE_NAME, copy_tile, empty_tile


class TestProject(unittest.TestCase):
    def test_starts_with_one_tile(self):
        project = Project()
        self.assertEqual(len(project.tiles), 1)
        self.assertEqual(project.active_tile_index, 0)
        self.assertEqual(project.get_active_tile()["name"], DEFAULT_TILE_NAME)
        self.assertEqual(project.metatiles, [])
        self.assertEqual(project.supertiles, [])

    def test_notify_calls_listeners(self):
        project = Project()
        events = []
        project.add_listener(events.append)
        event = ChangeEvent(ChangeEvent.TILE_CHANGED, 0)
        project.notify(event)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, ChangeEvent.TILE_CHANGED)

    def test_set_pixel_notifies_on_change(self):
        project = Project()
        events = []
        project.add_listener(events.append)
        self.assertTrue(project.set_pixel(1, 2, 1))
        self.assertEqual(project.get_active_tile()["pattern"][1][2], 1)
        self.assertEqual(len(events), 1)
        self.assertFalse(project.set_pixel(1, 2, 1))

    def test_set_row_color_updates_fg_or_bg(self):
        project = Project()
        project.set_row_color(3, fg=7)
        self.assertEqual(project.get_active_tile()["colors"][3]["fg"], 7)
        project.set_row_color(3, bg=4)
        self.assertEqual(project.get_active_tile()["colors"][3]["bg"], 4)

    def test_clear_active_tile_zeros_pattern(self):
        project = Project()
        project.set_pixel(0, 0, 1)
        project.clear_active_tile()
        self.assertEqual(project.get_active_tile()["pattern"][0][0], 0)
        self.assertEqual(project.get_active_tile()["colors"][0]["fg"], 15)

    def test_replace_active_tile(self):
        project = Project()
        replacement = empty_tile("TIL01")
        replacement["pattern"][0][0] = 1
        project.replace_active_tile(copy_tile(replacement))
        self.assertEqual(project.get_active_tile()["name"], "TIL01")
        self.assertEqual(project.get_active_tile()["pattern"][0][0], 1)


if __name__ == "__main__":
    unittest.main()