#!/usr/bin/env python3
"""burglekutt tile editor entry point."""

import tkinter as tk

from project import Project
from tileset_editor import TilesetEditorWindow


def main():
    root = tk.Tk()
    project = Project()
    TilesetEditorWindow(root, project)
    root.mainloop()


if __name__ == "__main__":
    main()