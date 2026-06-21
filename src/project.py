"""Shared project state for all editor windows."""

from tile_model import empty_tile


class ChangeEvent:
    TILE_CHANGED = "tile_changed"

    def __init__(self, kind, index=0):
        self.kind = kind
        self.index = index


class Project:
    def __init__(self):
        self.tiles = [empty_tile()]
        self.active_tile_index = 0
        self.metatiles = []
        self.supertiles = []
        self._listeners = []

    def get_active_tile(self):
        return self.tiles[self.active_tile_index]

    def add_listener(self, callback):
        self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify(self, event):
        for callback in list(self._listeners):
            callback(event)