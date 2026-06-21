"""Dialogs for bulk line-color editing."""

import tkinter as tk
from tkinter import ttk

import theme
from palette import PalettePanel, _draw_checkerboard, rgb_to_hex
from tile_model import DEFAULT_BG, DEFAULT_FG, TILE_SIZE

PREVIEW_SWATCH_SIZE = 28


def _draw_color_preview(canvas, color_index):
    canvas.delete("all")
    if color_index == 0:
        _draw_checkerboard(canvas, PREVIEW_SWATCH_SIZE)
    else:
        canvas.create_rectangle(
            0,
            0,
            PREVIEW_SWATCH_SIZE,
            PREVIEW_SWATCH_SIZE,
            fill=rgb_to_hex(color_index),
            outline="",
        )


class FillAllRowsDialog:
    """Pick fg/bg and apply to all scanlines on the active tile."""

    def __init__(self, parent, initial_fg, initial_bg, on_apply, window_bg):
        self._parent = parent
        self._on_apply = on_apply
        self._window_bg = window_bg
        self._styles = theme.window_styles(window_bg)
        self._fg = initial_fg
        self._bg = initial_bg

        self.root = tk.Toplevel(parent)
        self.root.title("Fill All Rows")
        self.root.transient(parent)
        theme.apply_window_theme(self.root, window_bg)
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", self.close)
        self.root.grab_set()
        self.root.focus_force()

    def _build_ui(self):
        frame = tk.Frame(self.root, bg=self._window_bg)
        theme.register_frame(frame, self.root, self._window_bg)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ttk.Label(
            frame,
            text="Set foreground and background for all 8 scanlines.",
            style=self._styles.label,
        ).pack(anchor=tk.W, pady=(0, 8))

        self._build_color_section(frame, "Foreground", "fg")
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        self._build_color_section(frame, "Background", "bg")

        buttons = ttk.Frame(frame, style=self._styles.frame)
        buttons.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(
            buttons,
            text="Apply",
            command=self._apply,
            style=self._styles.button,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            buttons,
            text="Cancel",
            command=self.close,
            style=self._styles.button,
        ).pack(side=tk.LEFT)

    def _build_color_section(self, parent, label, channel):
        section = ttk.Labelframe(
            parent,
            text=label,
            padding=8,
            style=self._styles.labelframe,
        )
        section.pack(fill=tk.X)

        header = ttk.Frame(section, style=self._styles.frame)
        header.pack(fill=tk.X, pady=(0, 6))

        preview = tk.Canvas(
            header,
            width=PREVIEW_SWATCH_SIZE,
            height=PREVIEW_SWATCH_SIZE,
            highlightthickness=1,
            highlightbackground=theme.CANVAS_GRID_OUTLINE,
        )
        preview.pack(side=tk.LEFT)

        value_label = ttk.Label(header, style=self._styles.label)
        value_label.pack(side=tk.LEFT, padx=(8, 0))

        if channel == "fg":
            self._fg_preview = preview
            self._fg_label = value_label
            _draw_color_preview(preview, self._fg)
            value_label.config(text="Color {}".format(self._fg))
        else:
            self._bg_preview = preview
            self._bg_label = value_label
            _draw_color_preview(preview, self._bg)
            value_label.config(text="Color {}".format(self._bg))

        panel = PalettePanel(section, window_bg=self._window_bg, require_target=False)
        panel.pack()
        if channel == "fg":
            panel.on_color_pick(self._on_fg_pick)
        else:
            panel.on_color_pick(self._on_bg_pick)

    def _on_fg_pick(self, color_index):
        self._fg = color_index
        _draw_color_preview(self._fg_preview, color_index)
        self._fg_label.config(text="Color {}".format(color_index))

    def _on_bg_pick(self, color_index):
        self._bg = color_index
        _draw_color_preview(self._bg_preview, color_index)
        self._bg_label.config(text="Color {}".format(color_index))

    def _apply(self):
        self._on_apply(self._fg, self._bg)
        self.close()

    def close(self, _event=None):
        try:
            self.root.grab_release()
        except tk.TclError:
            pass
        self.root.destroy()


class CopyRowColorsDialog:
    """Copy one row's fg/bg to a subset of destination rows."""

    def __init__(self, parent, tile, default_source_row, on_apply, window_bg):
        self._parent = parent
        self._tile = tile
        self._on_apply = on_apply
        self._window_bg = window_bg
        self._styles = theme.window_styles(window_bg)
        self._source_row = default_source_row
        self._dest_vars = []

        self.root = tk.Toplevel(parent)
        self.root.title("Copy Row Colors")
        self.root.transient(parent)
        theme.apply_window_theme(self.root, window_bg)
        self._build_ui()
        self._update_source_preview()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", self.close)
        self.root.grab_set()
        self.root.focus_force()

    def _build_ui(self):
        frame = tk.Frame(self.root, bg=self._window_bg)
        theme.register_frame(frame, self.root, self._window_bg)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        source_frame = ttk.Labelframe(
            frame,
            text="Source row",
            padding=8,
            style=self._styles.labelframe,
        )
        source_frame.pack(fill=tk.X, pady=(0, 8))

        source_row = ttk.Frame(source_frame, style=self._styles.frame)
        source_row.pack(fill=tk.X)

        ttk.Label(source_row, text="Row:", style=self._styles.label).pack(
            side=tk.LEFT
        )
        self._source_var = tk.IntVar(value=self._source_row)
        source_spin = tk.Spinbox(
            source_row,
            from_=0,
            to=TILE_SIZE - 1,
            width=4,
            textvariable=self._source_var,
            command=self._on_source_change,
        )
        source_spin.pack(side=tk.LEFT, padx=(4, 8))
        source_spin.bind("<KeyRelease>", self._on_source_change)

        self._source_fg_preview = tk.Canvas(
            source_row,
            width=PREVIEW_SWATCH_SIZE,
            height=PREVIEW_SWATCH_SIZE,
            highlightthickness=1,
            highlightbackground=theme.CANVAS_GRID_OUTLINE,
        )
        self._source_fg_preview.pack(side=tk.LEFT, padx=(0, 4))
        self._source_bg_preview = tk.Canvas(
            source_row,
            width=PREVIEW_SWATCH_SIZE,
            height=PREVIEW_SWATCH_SIZE,
            highlightthickness=1,
            highlightbackground=theme.CANVAS_GRID_OUTLINE,
        )
        self._source_bg_preview.pack(side=tk.LEFT)

        dest_frame = ttk.Labelframe(
            frame,
            text="Destination rows",
            padding=8,
            style=self._styles.labelframe,
        )
        dest_frame.pack(fill=tk.X, pady=(0, 8))

        helpers = ttk.Frame(dest_frame, style=self._styles.frame)
        helpers.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(
            helpers,
            text="All",
            command=self._select_all,
            style=self._styles.button,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            helpers,
            text="None",
            command=self._select_none,
            style=self._styles.button,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            helpers,
            text="All except source",
            command=self._select_all_except_source,
            style=self._styles.button,
        ).pack(side=tk.LEFT)

        checks = ttk.Frame(dest_frame, style=self._styles.frame)
        checks.pack(fill=tk.X)
        for row in range(TILE_SIZE):
            var = tk.BooleanVar(value=False)
            self._dest_vars.append(var)
            ttk.Checkbutton(
                checks,
                text=str(row),
                variable=var,
                command=self._update_apply_state,
                style=self._styles.checkbutton,
            ).grid(row=row // 4, column=row % 4, sticky=tk.W, padx=4, pady=2)

        buttons = ttk.Frame(frame, style=self._styles.frame)
        buttons.pack(fill=tk.X)
        self._apply_button = ttk.Button(
            buttons,
            text="Apply",
            command=self._apply,
            style=self._styles.button,
            state=tk.DISABLED,
        )
        self._apply_button.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            buttons,
            text="Cancel",
            command=self.close,
            style=self._styles.button,
        ).pack(side=tk.LEFT)

    def _on_source_change(self, _event=None):
        try:
            row = int(self._source_var.get())
        except (tk.TclError, ValueError):
            return
        if not 0 <= row < TILE_SIZE:
            return
        self._source_row = row
        self._update_source_preview()

    def _update_source_preview(self):
        colors = self._tile["colors"][self._source_row]
        _draw_color_preview(self._source_fg_preview, colors["fg"])
        _draw_color_preview(self._source_bg_preview, colors["bg"])

    def _selected_destinations(self):
        return [index for index, var in enumerate(self._dest_vars) if var.get()]

    def _update_apply_state(self):
        state = tk.NORMAL if self._selected_destinations() else tk.DISABLED
        self._apply_button.config(state=state)

    def _select_all(self):
        for var in self._dest_vars:
            var.set(True)
        self._update_apply_state()

    def _select_none(self):
        for var in self._dest_vars:
            var.set(False)
        self._update_apply_state()

    def _select_all_except_source(self):
        for index, var in enumerate(self._dest_vars):
            var.set(index != self._source_row)
        self._update_apply_state()

    def _apply(self):
        dest_rows = self._selected_destinations()
        if not dest_rows:
            return
        self._on_apply(self._source_row, dest_rows)
        self.close()

    def close(self, _event=None):
        try:
            self.root.grab_release()
        except tk.TclError:
            pass
        self.root.destroy()


def default_fill_colors(tile, active_row=None):
    """Return initial fg/bg for Fill All Rows."""
    if active_row is not None and 0 <= active_row < TILE_SIZE:
        colors = tile["colors"][active_row]
        return colors["fg"], colors["bg"]
    return DEFAULT_FG, DEFAULT_BG