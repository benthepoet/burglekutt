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
_configured_style_prefixes = set()


def style_prefix(window_bg):
    """Return the ttk style namespace for a window tint."""
    if window_bg == METATILE_WINDOW_BG:
        return "Metatile"
    if window_bg == SUPERTILE_WINDOW_BG:
        return "Supertile"
    if window_bg == TILE_PICKER_BG:
        return "Picker"
    return "Tileset"


def ttk_style(window_bg, base_name):
    """Return a namespaced ttk style (e.g. Metatile.TLabelframe)."""
    return "{}.{}".format(style_prefix(window_bg), base_name)


class WindowStyles:
    """Namespaced ttk style names for one editor window tint."""

    def __init__(self, window_bg):
        prefix = style_prefix(window_bg)
        self.frame = "{}.TFrame".format(prefix)
        self.labelframe = "{}.TLabelframe".format(prefix)
        self.labelframe_label = "{}.TLabelframe.Label".format(prefix)
        self.label = "{}.TLabel".format(prefix)
        self.button = "{}.TButton".format(prefix)
        self.checkbutton = "{}.TCheckbutton".format(prefix)
        self.scrollbar = "{}.TScrollbar".format(prefix)


def window_styles(window_bg):
    return WindowStyles(window_bg)


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


def _clone_style_layout(style, prefixed_name, base_name):
    try:
        style.layout(prefixed_name, style.layout(base_name))
    except tk.TclError:
        pass


def _clone_scrollbar_layouts(style, window_bg):
    """Scrollbar layouts are orientation-prefixed (Vertical.TScrollbar, etc.)."""
    prefixed_scrollbar = ttk_style(window_bg, "TScrollbar")
    for orientation in ("Vertical", "Horizontal"):
        _clone_style_layout(
            style,
            "{}.{}".format(orientation, prefixed_scrollbar),
            "{}.TScrollbar".format(orientation),
        )


def _ensure_window_ttk_styles(root, window_bg):
    """Configure namespaced ttk styles once per window tint."""
    global _ui_style
    prefix = style_prefix(window_bg)
    if prefix in _configured_style_prefixes:
        return
    if _ui_style is None:
        _ui_style = ttk.Style(root)
    _configured_style_prefixes.add(prefix)

    text_fg = TEXT_FG
    widget_bases = (
        "TFrame",
        "TLabelframe",
        "TLabel",
        "TCheckbutton",
        "TButton",
    )
    for base in widget_bases:
        prefixed = ttk_style(window_bg, base)
        _clone_style_layout(_ui_style, prefixed, base)
    _clone_style_layout(
        _ui_style,
        ttk_style(window_bg, "TLabelframe.Label"),
        "TLabelframe.Label",
    )
    _clone_scrollbar_layouts(_ui_style, window_bg)

    for base in ("TFrame", "TLabelframe", "TScrollbar"):
        _configure_theme_style(_ui_style, ttk_style(window_bg, base), window_bg)
    for base in ("TLabel", "TCheckbutton"):
        _configure_theme_style(
            _ui_style,
            ttk_style(window_bg, base),
            window_bg,
            foreground=text_fg,
        )
    _configure_theme_style(
        _ui_style,
        ttk_style(window_bg, "TLabelframe.Label"),
        window_bg,
        foreground=PANEL_TITLE_FG,
        font=PANEL_TITLE_FONT,
    )
    _configure_theme_style(
        _ui_style,
        ttk_style(window_bg, "TButton"),
        window_bg,
        button=True,
        foreground=text_fg,
    )


def apply_window_theme(root, window_bg):
    """Apply tinted backgrounds and register per-window ttk styles."""
    _ensure_window_ttk_styles(root, window_bg)
    root.configure(bg=window_bg)
    for frame, frame_root, frame_bg in _themed_frames:
        if frame_root == root:
            try:
                frame.configure(bg=frame_bg)
            except tk.TclError:
                pass