"""Keyboard shortcut bindings shared across editor windows."""

import tkinter as tk
from tkinter import messagebox

COMMON_HELP = """\
File (all editors)
  Ctrl+N       New project
  Ctrl+O       Load project
  Ctrl+S       Save project
  Ctrl+Q       Exit

Window
  Ctrl+1       Tileset editor
  Ctrl+2       Metatile editor
  Ctrl+3       Supertile editor

Export (focused editor)
  Ctrl+Shift+A   Save assembly…
  Ctrl+Shift+B   Save binary…

Export preview
  Ctrl+S         Save to file
"""

TILESET_HELP = """\
Tileset editor
  Ctrl+Z         Undo
  Ctrl+Y         Redo
  Ctrl+Shift+Z   Redo
  Ctrl+Backspace Clear tile
  Ctrl+D         Duplicate to…
  Ctrl+T         Select tile…
  Ctrl+Shift+F   Fill all rows…
  Ctrl+Shift+R   Copy row colors…
  +  /  =        Zoom in (canvas focused)
  -              Zoom out (canvas focused)
"""

METATILE_HELP = """\
Metatile editor
  F2             Rename metatile
  Delete         Remove metatile
"""

SUPERTILE_HELP = """\
Supertile editor
  F2             Rename supertile
  Delete         Remove supertile
"""


def bind_sequence(root, sequence, callback):
    """Bind a keyboard sequence on a top-level window."""
    root.bind(sequence, lambda _event=None: callback())


APP_FILE_SEQUENCES = (
    "<Control-n>",
    "<Control-N>",
    "<Control-o>",
    "<Control-O>",
    "<Control-s>",
    "<Control-S>",
    "<Control-q>",
    "<Control-Q>",
)

APP_WINDOW_SEQUENCES = (
    "<Control-1>",
    "<Control-2>",
    "<Control-3>",
)

APP_EXPORT_SEQUENCES = (
    "<Control-Shift-a>",
    "<Control-Shift-A>",
    "<Control-Shift-b>",
    "<Control-Shift-B>",
)


def bind_app_shortcuts(app_root, coordinator):
    """App-wide file shortcuts (bind_all so they work in any widget)."""
    if coordinator is None:
        return
    file_pairs = (
        ("<Control-n>", coordinator.new_project),
        ("<Control-N>", coordinator.new_project),
        ("<Control-o>", coordinator.load_project_dialog),
        ("<Control-O>", coordinator.load_project_dialog),
        ("<Control-s>", coordinator.save_project_dialog),
        ("<Control-S>", coordinator.save_project_dialog),
        ("<Control-q>", coordinator.exit_all),
        ("<Control-Q>", coordinator.exit_all),
    )
    window_pairs = (
        ("<Control-1>", coordinator.focus_tileset),
        ("<Control-2>", coordinator.focus_metatile),
        ("<Control-3>", coordinator.focus_supertile),
    )
    export_pairs = (
        ("<Control-Shift-a>", coordinator.preview_assembly_shortcut),
        ("<Control-Shift-A>", coordinator.preview_assembly_shortcut),
        ("<Control-Shift-b>", coordinator.preview_binary_shortcut),
        ("<Control-Shift-B>", coordinator.preview_binary_shortcut),
    )

    def _bind_all(pairs):
        for sequence, callback in pairs:
            app_root.bind_all(
                sequence,
                lambda event, handler=callback: _app_shortcut_handler(handler, event),
            )

    _bind_all(file_pairs)
    _bind_all(window_pairs)
    _bind_all(export_pairs)


def unbind_app_shortcuts(app_root):
    """Remove app-wide shortcut bindings."""
    for sequence in APP_FILE_SEQUENCES + APP_WINDOW_SEQUENCES + APP_EXPORT_SEQUENCES:
        try:
            app_root.unbind_all(sequence)
        except tk.TclError:
            pass


def _app_shortcut_handler(callback, _event=None):
    callback()
    return "break"


def bind_common(root, coordinator):
    """Per-window shortcuts (file/window bindings use bind_app_shortcuts)."""
    del root, coordinator


def bind_tileset(root, editor):
    """Tileset-specific editing shortcuts."""
    pairs = (
        ("<Control-z>", editor._undo),
        ("<Control-y>", editor._redo),
        ("<Control-Y>", editor._redo),
        ("<Control-Shift-Z>", editor._redo),
        ("<Control-Shift-z>", editor._redo),
        ("<Control-BackSpace>", editor._clear_tile),
        ("<Control-d>", editor._duplicate_tile),
        ("<Control-D>", editor._duplicate_tile),
        ("<Control-t>", editor._open_tile_picker),
        ("<Control-T>", editor._open_tile_picker),
        ("<Control-Shift-F>", editor._fill_all_rows),
        ("<Control-Shift-f>", editor._fill_all_rows),
        ("<Control-Shift-R>", editor._copy_row_colors),
        ("<Control-Shift-r>", editor._copy_row_colors),
    )
    for sequence, callback in pairs:
        bind_sequence(root, sequence, callback)


def bind_canvas_zoom(canvas, zoom_in, zoom_out):
    """+/- zoom on the tile draw canvas when it has focus."""
    for sequence in ("<Key-plus>", "<Key-equal>", "<KP_Add>"):
        canvas.bind(sequence, lambda _event=None: zoom_in())
    for sequence in ("<Key-minus>", "<KP_Subtract>"):
        canvas.bind(sequence, lambda _event=None: zoom_out())


def show_shortcuts_help(parent, text):
    """Show a shortcuts reference dialog."""
    messagebox.showinfo("Keyboard Shortcuts", text, parent=parent)