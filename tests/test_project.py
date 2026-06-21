import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from project import ChangeEvent, Project
from tile_model import DEFAULT_TILE_NAME


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


if __name__ == "__main__":
    unittest.main()