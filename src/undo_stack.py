"""Undo/redo stack for tile snapshots."""


class UndoStack:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self._undo = []
        self._redo = []

    def push(self, snapshot):
        self._undo.append(snapshot)
        if len(self._undo) > self.max_size:
            self._undo.pop(0)
        self._redo.clear()

    def undo(self, current):
        if not self._undo:
            return None
        self._redo.append(current)
        return self._undo.pop()

    def redo(self, current):
        if not self._redo:
            return None
        self._undo.append(current)
        return self._redo.pop()

    def clear(self):
        self._undo.clear()
        self._redo.clear()

    def can_undo(self):
        return bool(self._undo)

    def can_redo(self):
        return bool(self._redo)