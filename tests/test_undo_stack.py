import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from undo_stack import UndoStack


class TestUndoStack(unittest.TestCase):
    def _snapshot(self, value):
        return {"value": value}

    def test_push_undo_redo(self):
        stack = UndoStack(max_size=10)
        stack.push(self._snapshot(1))
        restored = stack.undo(self._snapshot(2))
        self.assertEqual(restored["value"], 1)
        redone = stack.redo(self._snapshot(1))
        self.assertEqual(redone["value"], 2)

    def test_max_size_evicts_oldest(self):
        stack = UndoStack(max_size=3)
        for value in range(5):
            stack.push(self._snapshot(value))
        self.assertEqual(stack.undo(self._snapshot(99))["value"], 4)
        self.assertEqual(stack.undo(self._snapshot(99))["value"], 3)
        self.assertEqual(stack.undo(self._snapshot(99))["value"], 2)
        self.assertIsNone(stack.undo(self._snapshot(99)))

    def test_push_clears_redo(self):
        stack = UndoStack()
        stack.push(self._snapshot(1))
        stack.undo(self._snapshot(2))
        self.assertTrue(stack.can_redo())
        stack.push(self._snapshot(3))
        self.assertFalse(stack.can_redo())

    def test_clear(self):
        stack = UndoStack()
        stack.push(self._snapshot(1))
        stack.clear()
        self.assertFalse(stack.can_undo())
        self.assertFalse(stack.can_redo())


if __name__ == "__main__":
    unittest.main()