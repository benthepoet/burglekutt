"""Per-window backgrounds and shared UI chrome."""

import tkinter as tk
from tkinter import ttk

TILESET_WINDOW_BG = "#E8F5E9"
TILESET_BUTTON_BORDER = "#A5D6A7"
TILESET_BUTTON_LIGHT = "#F1F8F2"
TILESET_BUTTON_DARK = "#81C784"

METATILE_WINDOW_BG = "#FFF7ED"
SUPERTILE_WINDOW_BG = "#EEF4FF"
TILE_PICKER_BG = "#FEF3C7"

CANVAS_BG = "#777777"
CANVAS_GRID_OUTLINE = "#555555"
PANEL_BG = "#FFFFFF"
PANEL_TITLE_FG = "#111827"
PANEL_TITLE_FONT = ("Arial", 11, "bold")
TEXT_FG = "#1F2937"
BUTTON_DISABLED_BG = "#E5E7EB"
BUTTON_DISABLED_FG = "#9CA3AF"
BUTTON_DISABLED_BORDER = "#D1D5DB"
ACCENT_BORDER = "#2563EB"

_themed_frames = []
_ui_style = None


def register_frame(frame, root, window_bg):
    """Track a frame for a specific top-level window."""
    entry = (frame, root, window_bg)
    if entry not in _themed_frames:
        _themed_frames.append(entry)
    try:
        frame.configure(bg=window_bg)
    except tk.TclError:
        pass


def unregister_frame(frame):
    """Stop applying window theme to a frame."""
    _themed_frames[:] = [entry for entry in _themed_frames if entry[0] is not frame]


def _button_border_colors(window_bg):
    if window_bg == METATILE_WINDOW_BG:
        return "#C4B5A5", "#FFF8F0", "#DFC8B5"
    if window_bg == SUPERTILE_WINDOW_BG:
        return "#A8B4C8", "#F4F8FF", "#C5D4E8"
    if window_bg == TILE_PICKER_BG:
        return "#D4C48A", "#FFFBEB", "#C8B870"
    return TILESET_BUTTON_BORDER, TILESET_BUTTON_LIGHT, TILESET_BUTTON_DARK


def _configure_theme_style(style, style_name, background, *, button=False, foreground=None, font=None):
    options = {"background": background}
    if foreground is not None:
        options["foreground"] = foreground
    if font is not None:
        options["font"] = font
    bordercolor = lightcolor = darkcolor = None
    if button:
        bordercolor, lightcolor, darkcolor = _button_border_colors(background)
        options.update(
            {
                "bordercolor": bordercolor,
                "lightcolor": lightcolor,
                "darkcolor": darkcolor,
            }
        )
    try:
        style.configure(style_name, **options)
    except tk.TclError:
        return
    if button:
        enabled_fg = foreground if foreground is not None else TEXT_FG
        style.map(
            style_name,
            background=[
                ("disabled", BUTTON_DISABLED_BG),
                ("active", background),
                ("pressed", background),
                ("!disabled", background),
            ],
            foreground=[
                ("disabled", BUTTON_DISABLED_FG),
                ("!disabled", enabled_fg),
            ],
            bordercolor=[
                ("disabled", BUTTON_DISABLED_BORDER),
                ("!disabled", bordercolor),
            ],
            lightcolor=[
                ("disabled", BUTTON_DISABLED_BORDER),
                ("!disabled", lightcolor),
            ],
            darkcolor=[
                ("disabled", BUTTON_DISABLED_BORDER),
                ("!disabled", darkcolor),
            ],
        )


def apply_window_theme(root, window_bg):
    """Apply tinted window background and ttk styles for one top-level window."""
    global _ui_style
    if _ui_style is None:
        _ui_style = ttk.Style(root)

    root.configure(bg=window_bg)
    for frame, frame_root, frame_bg in _themed_frames:
        if frame_root == root:
            try:
                frame.configure(bg=frame_bg)
            except tk.TclError:
                pass

    text_fg = TEXT_FG
    for name in ("TFrame", "TLabelframe"):
        _configure_theme_style(_ui_style, name, window_bg)
    for name in ("TLabel", "TCheckbutton"):
        _configure_theme_style(_ui_style, name, window_bg, foreground=text_fg)
    _configure_theme_style(
        _ui_style,
        "TLabelframe.Label",
        window_bg,
        foreground=PANEL_TITLE_FG,
        font=PANEL_TITLE_FONT,
    )
    _configure_theme_style(_ui_style, "TButton", window_bg, button=True, foreground=text_fg)
    _configure_theme_style(_ui_style, "TMenubutton", window_bg, button=True, foreground=text_fg)