import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from project import ChangeEvent, Project
from tile_model import (
    METATILE_FLAG_SOLID,
    SUPERTILE_CELL_COUNT,
    TILE_COUNT,
    copy_tile,
    empty_tile,
    metatile_name_for_index,
    supertile_name_for_index,
    tile_name_for_index,
)


class TestProject(unittest.TestCase):
    def test_starts_with_256_tiles_and_default_metatile(self):
        project = Project()
        self.assertEqual(len(project.tiles), TILE_COUNT)
        self.assertEqual(project.active_tile_index, 0)
        self.assertEqual(project.get_active_tile()["name"], tile_name_for_index(0))
        self.assertEqual(len(project.metatiles), 1)
        self.assertEqual(project.get_active_metatile()["name"], metatile_name_for_index(0))
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

    def test_set_pixel_can_defer_notification(self):
        project = Project()
        events = []
        project.add_listener(events.append)
        self.assertTrue(project.set_pixel(0, 0, 1, notify=False))
        self.assertEqual(len(events), 0)
        project.notify_active_tile_changed()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, ChangeEvent.TILE_CHANGED)

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

    def test_set_active_tile_index_notifies(self):
        project = Project()
        events = []
        project.add_listener(events.append)
        self.assertTrue(project.set_active_tile_index(5))
        self.assertEqual(project.active_tile_index, 5)
        self.assertEqual(events[-1].kind, ChangeEvent.ACTIVE_TILE_CHANGED)
        self.assertFalse(project.set_active_tile_index(5))

    def test_duplicate_tile_copies_pattern_and_keeps_dest_name(self):
        project = Project()
        project.set_pixel(0, 0, 1)
        project.duplicate_tile(0, 10)
        self.assertEqual(project.get_tile(10)["pattern"][0][0], 1)
        self.assertEqual(project.get_tile(10)["name"], tile_name_for_index(10))

    def test_rename_tile(self):
        project = Project()
        self.assertTrue(project.rename_tile(0, "WALL"))
        self.assertEqual(project.get_tile(0)["name"], "WALL")
        with self.assertRaises(ValueError):
            project.rename_tile(0, "   ")

    def test_add_and_remove_metatile(self):
        project = Project()
        project.add_metatile()
        self.assertEqual(len(project.metatiles), 2)
        self.assertEqual(project.active_metatile_index, 1)
        project.remove_metatile(0)
        self.assertEqual(len(project.metatiles), 1)
        self.assertEqual(project.active_metatile_index, 0)

    def test_set_metatile_cell_and_flag(self):
        project = Project()
        project.set_metatile_cell(0, 2, 9)
        self.assertEqual(project.get_metatile(0)["cells"][2], 9)
        project.set_metatile_flag(0, METATILE_FLAG_SOLID, True)
        self.assertEqual(project.get_metatile(0)["flags"], METATILE_FLAG_SOLID)

    def test_set_active_metatile_index_notifies(self):
        project = Project()
        project.add_metatile()
        events = []
        project.add_listener(events.append)
        project.set_active_metatile_index(0)
        self.assertEqual(events[-1].kind, ChangeEvent.ACTIVE_METATILE_CHANGED)

    def test_add_and_remove_supertile(self):
        project = Project()
        project.add_supertile()
        self.assertEqual(len(project.supertiles), 1)
        self.assertEqual(project.active_supertile_index, 0)
        self.assertEqual(
            project.get_active_supertile()["name"],
            supertile_name_for_index(0),
        )
        project.add_supertile()
        self.assertEqual(project.active_supertile_index, 1)
        project.remove_supertile(0)
        self.assertEqual(len(project.supertiles), 1)
        self.assertEqual(project.active_supertile_index, 0)

    def test_set_supertile_cell_and_rename(self):
        project = Project()
        project.add_supertile()
        project.add_metatile()
        project.set_supertile_cell(0, 3, 1)
        self.assertEqual(project.get_supertile(0)["cells"][3], 1)
        self.assertEqual(len(project.get_supertile(0)["cells"]), SUPERTILE_CELL_COUNT)
        self.assertTrue(project.rename_supertile(0, "ROOM_A"))
        self.assertEqual(project.get_supertile(0)["name"], "ROOM_A")

    def test_set_active_supertile_index_notifies(self):
        project = Project()
        project.add_supertile()
        project.add_supertile()
        events = []
        project.add_listener(events.append)
        project.set_active_supertile_index(0)
        self.assertEqual(events[-1].kind, ChangeEvent.ACTIVE_SUPERTILE_CHANGED)

    def test_supertiles_referencing_metatile(self):
        project = Project()
        project.add_supertile()
        project.set_supertile_cell(0, 0, 0)
        self.assertEqual(project.supertiles_referencing_metatile(0), [0])


if __name__ == "__main__":
    unittest.main()