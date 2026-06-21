# burglekutt

A desktop authoring toolchain for a TI-99/4A Zelda-like game. **burglekutt** lets you draw TMS9918 Graphics II tiles, compose them into metatiles and supertiles, and export assembly or binary data your game can load directly.

The tile editor is **complete**. A map/screen editor (placing supertiles on playfields) is planned as a follow-on app in this repo.

## Requirements

- Python **3.6+**
- **Tkinter** (stdlib; usually included with Python on Linux/macOS/Windows)
- No pip dependencies

## Quick start

```bash
# Launch the tile editor (opens three windows)
python3 src/editor.py

# Run tests
python3 -m unittest discover -s tests
```

On first launch you get three editor windows at once:

| Window | Tint | Purpose |
|--------|------|---------|
| **Tileset** | Green | Draw 256 base tiles (8×8, per-scanline colors) |
| **Metatile** | Warm | Compose 2×2 tile chunks with collision flags |
| **Supertile** | Blue | Compose 4×4 metatile blocks (64×64 px) |

Edits cascade live — change a base tile and every metatile/supertile that references it updates immediately.

## Workflow

### Tileset editor

1. Draw on the 8×8 grid: **left-click** sets a pixel to foreground, **right-click** to background.
2. Click a row's **fg/bg swatch** to open the TMS9918 palette popup for that scanline.
3. Use **Tiles → Select Tile…** (or the tile picker window) to switch among 256 slots (`TIL00`–`TILFF`).
4. **Edit → Undo/Redo** (10-step history per tile), **Clear Tile**, **Duplicate to…**, **Rename…**.

**Colors menu**

- **Fill All Rows…** — pick foreground and background in a dialog, apply to all 8 scanlines.
- **Copy Row Colors…** — copy one row's fg/bg to any other rows.

**View menu** — zoom the draw canvas in/out (+/− keys when the canvas has focus).

### Metatile editor

- **Add / Remove / Rename** metatiles (up to 256).
- Set **flags**: Solid, Hurt, Water, Door, Stairs.
- Click a **cell** in the 2×2 picker to assign a base tile via the shared tile picker.
- Removing a metatile warns if supertiles still reference it.

### Supertile editor

- **Add / Remove / Rename** supertiles (up to 256).
- Click a **cell** in the 4×4 picker to assign a metatile via the metatile picker.
- Starts with an empty supertile list until you click **Add**.

## Project files

**File → New / Load Project / Save Project** works from any editor window.

Projects are JSON (version 1) containing `tiles` (always 256), `metatiles`, and `supertiles`. Unknown keys are ignored on load so future map data can coexist.

## Export

Each editor has **Export → Save Assembly…** and **Save Binary…**. These open a **preview window** first — review the generated output, then **Copy Assembly**, **Save to file**, or **Close**. Nothing is written to disk until you confirm save in the preview.

| Editor | Assembly sections | Binary |
|--------|-------------------|--------|
| Tileset | `PATTERNS`, `COLORS` | Pattern table + color table (4096 bytes) |
| Metatile | `METAS` … `METASEND` | N × 5 bytes |
| Supertile | `SUPERS` … `SUPERSEND` | M × 16 bytes |

Default format: TI-99 `BYTE >xx` dialect (`formats/ti99_default/`).

## Keyboard shortcuts

**Help → Keyboard Shortcuts…** in any editor lists shortcuts for that window.

### All editors

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New project |
| Ctrl+O | Load project |
| Ctrl+S | Save project |
| Ctrl+Q | Exit |
| Ctrl+1 / 2 / 3 | Focus tileset / metatile / supertile window |
| Ctrl+Shift+A | Save assembly… (opens preview) |
| Ctrl+Shift+B | Save binary… (opens preview) |

### Tileset editor

| Shortcut | Action |
|----------|--------|
| Ctrl+Z | Undo |
| Ctrl+Y / Ctrl+Shift+Z | Redo |
| Ctrl+Backspace | Clear tile |
| Ctrl+D | Duplicate to… |
| Ctrl+T | Select tile… |
| Ctrl+Shift+F | Fill all rows… |
| Ctrl+Shift+R | Copy row colors… |
| + / = / − | Zoom in/out (canvas focused) |

### Metatile / Supertile editors

| Shortcut | Action |
|----------|--------|
| F2 | Rename (list focused) |
| Delete | Remove (list focused) |

### Export preview window

| Shortcut | Action |
|----------|--------|
| Ctrl+S | Save to file |
| Escape | Close |

## Data model (summary)

```
Tile (8×8)     → 8 pattern bytes + 8 color-table bytes per slot
Metatile (2×2) → 1 flags byte + 4 tile indices
Supertile (4×4)→ 16 metatile indices (64×64 px composite)
```

Metatile flags are a bitfield (solid, hurt, water, door, stairs). Color bytes use `(fg << 4) | bg` per scanline. Pattern bytes are MSB-left bitplanes.

See `AGENTS.md` for the full export contract, JSON schema, and agent/developer conventions.

## Repository layout

```
src/
  editor.py              # App entry point
  tileset_editor.py      # Tileset window
  metatile_editor.py     # Metatile window
  supertile_editor.py    # Supertile window
  project.py             # Shared project state
  project_io.py          # JSON save/load
  composite.py           # Metatile/supertile pixel resolution
  export_preview.py      # Export preview window
  …                      # canvas, pickers, export encoders, theme, etc.
formats/ti99_default/    # Default ASM export dialect
tests/                   # unittest suite
```

## License

MIT — see [LICENSE](LICENSE).