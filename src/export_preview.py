"""On-demand export preview window (assembly or binary)."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import theme
from asm_export import (
    render_metatile_export,
    render_supertile_export,
    render_tileset_export,
)
from binary_export import (
    metatile_table_bytes,
    supertile_table_bytes,
    tileset_bytes,
)

SCOPE_TILESET = "tileset"
SCOPE_METATILE = "metatile"
SCOPE_SUPERTILE = "supertile"

MODE_ASSEMBLY = "assembly"
MODE_BINARY = "binary"


def generate_export(project, scope):
    """Return assembly text, binary bytes, and default filenames for a scope."""
    if scope == SCOPE_TILESET:
        assembly = render_tileset_export(project.tiles)
        binary = tileset_bytes(project.tiles)
        default_asm = "patterns_colors.asm"
        default_bin = "tileset.bin"
        label = "PATTERNS / COLORS"
    elif scope == SCOPE_METATILE:
        assembly = render_metatile_export(project.metatiles)
        binary = metatile_table_bytes(project.metatiles)
        default_asm = "metas.asm"
        default_bin = "metas.bin"
        label = "METAS"
    elif scope == SCOPE_SUPERTILE:
        assembly = render_supertile_export(project.supertiles)
        binary = supertile_table_bytes(project.supertiles)
        default_asm = "supers.asm"
        default_bin = "supers.bin"
        label = "SUPERS"
    else:
        raise ValueError("unknown export scope: {}".format(scope))
    return assembly, binary, default_asm, default_bin, label


def format_binary_preview(data, bytes_per_line=16):
    """Format raw bytes as a hex dump for preview."""
    if not data:
        return "; (empty — 0 bytes)"
    lines = ["; {} bytes".format(len(data))]
    for offset in range(0, len(data), bytes_per_line):
        chunk = data[offset : offset + bytes_per_line]
        hex_part = " ".join("{:02X}".format(byte) for byte in chunk)
        lines.append("{:04X}: {}".format(offset, hex_part))
    return "\n".join(lines)


class ExportPreviewWindow:
    """Modal-ish preview of generated export before save/copy."""

    def __init__(self, parent, project, scope, mode, window_bg):
        self._parent = parent
        self._project = project
        self._scope = scope
        self._mode = mode
        self._window_bg = window_bg
        self._styles = theme.window_styles(window_bg)

        assembly, binary, default_asm, default_bin, label = generate_export(
            project,
            scope,
        )
        self._assembly_text = assembly
        self._binary_data = binary
        self._default_asm = default_asm
        self._default_bin = default_bin
        self._label = label

        if mode == MODE_ASSEMBLY:
            self._preview_text = assembly
        else:
            self._preview_text = format_binary_preview(binary)

        self.root = tk.Toplevel(parent)
        kind = "Assembly" if mode == MODE_ASSEMBLY else "Binary"
        self.root.title("burglekutt — Export Preview ({})".format(kind))
        self.root.transient(parent)
        theme.apply_window_theme(self.root, window_bg)

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", self.close)
        self.root.bind("<Control-s>", self._save_shortcut)
        self.root.bind("<Control-S>", self._save_shortcut)
        self.root.grab_set()
        self.root.focus_force()

    def _build_ui(self):
        frame = tk.Frame(self.root, bg=self._window_bg)
        theme.register_frame(frame, self.root, self._window_bg)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ttk.Label(
            frame,
            text="{} — review before saving".format(self._label),
            style=self._styles.label,
        ).pack(anchor=tk.W, pady=(0, 6))

        text_frame = tk.Frame(frame, bg=theme.PANEL_BG)
        theme.register_frame(text_frame, self.root, self._window_bg)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(
            text_frame,
            orient=tk.VERTICAL,
            style=self._styles.scrollbar,
        )
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._text = tk.Text(
            text_frame,
            width=80,
            height=24,
            wrap=tk.NONE,
            bg=theme.PANEL_BG,
            fg=theme.TEXT_FG,
            insertbackground=theme.TEXT_FG,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=theme.CANVAS_GRID_OUTLINE,
            font=("Courier", 10),
            yscrollcommand=scroll.set,
        )
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self._text.yview)
        self._text.insert("1.0", self._preview_text)
        self._text.config(state=tk.DISABLED)

        buttons = ttk.Frame(frame, style=self._styles.frame)
        buttons.pack(fill=tk.X, pady=(8, 0))

        if self._mode == MODE_ASSEMBLY:
            ttk.Button(
                buttons,
                text="Copy Assembly",
                command=self._copy,
                style=self._styles.button,
            ).pack(side=tk.LEFT, padx=(0, 4))

        save_label = "Save Assembly…" if self._mode == MODE_ASSEMBLY else "Save Binary…"
        ttk.Button(
            buttons,
            text=save_label,
            command=self._save,
            style=self._styles.button,
        ).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(
            buttons,
            text="Close",
            command=self.close,
            style=self._styles.button,
        ).pack(side=tk.LEFT)

        self.root.minsize(520, 360)

    def _copy(self):
        self._parent.clipboard_clear()
        self._parent.clipboard_append(self._assembly_text)
        self._parent.update_idletasks()

    def _save_shortcut(self, _event=None):
        self._save()
        return "break"

    def _save(self):
        if self._mode == MODE_ASSEMBLY:
            path = filedialog.asksaveasfilename(
                parent=self.root,
                title="Save Assembly",
                defaultextension=".asm",
                initialfile=self._default_asm,
                filetypes=[
                    ("Assembly", "*.asm"),
                    ("Text", "*.txt"),
                    ("All", "*.*"),
                ],
            )
            if not path:
                return
            try:
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(self._assembly_text)
            except OSError as exc:
                messagebox.showerror("Save Assembly", str(exc), parent=self.root)
        else:
            path = filedialog.asksaveasfilename(
                parent=self.root,
                title="Save Binary",
                defaultextension=".bin",
                initialfile=self._default_bin,
                filetypes=[("Binary", "*.bin"), ("All", "*.*")],
            )
            if not path:
                return
            try:
                with open(path, "wb") as handle:
                    handle.write(self._binary_data)
            except OSError as exc:
                messagebox.showerror("Save Binary", str(exc), parent=self.root)

    def close(self, _event=None):
        try:
            self.root.grab_release()
        except tk.TclError:
            pass
        self.root.destroy()

    def focus(self):
        self.root.lift()
        self.root.focus_force()


def show_export_preview(parent, project, scope, mode, window_bg):
    """Open an export preview window for the given scope and mode."""
    return ExportPreviewWindow(parent, project, scope, mode, window_bg)