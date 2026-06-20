# AGENTS.md

Guidance for AI agents working on **burglekutt** — a tileset, metatile, and supertile editor for a TI-99/4A Zelda-like game.

## Project summary

Desktop Tkinter app with **three simultaneous editor windows** (tileset, metatile, supertile) for authoring the tile hierarchy used by the game engine. Edits propagate downstream live — change a base tile and every metatile/supertile that references it updates immediately.

| Level | Composition | Pixel size | Purpose |
|-------|-------------|------------|---------|
| **Tileset** | 256 base tiles | — | Full pattern table (one TMS9918 tile per slot) |
| **Base tile** | 8×8 pixels | 8×8 | Single pattern-table entry (index 0–255) |
| **Metatile** | 2×2 base tiles | 16×16 | Reusable terrain/object chunks |
| **Supertile** | 4×5 metatiles | 64×80 | Screen-building blocks for the playfield |

The editor must produce data the game can consume directly — **pattern bytes**, **color-table bytes**, metatile tables, and supertile maps — as assembly `BYTE` blocks (`PATTERNS`, `COLORS`, `METAS`, `SUPERS`).

- **Language:** Python 3.6+ (stdlib only — no pip dependencies)
- **UI:** Tkinter / ttk
- **Entry point:** `python3 src/editor.py` (once created)

User-facing docs belong in `README.md` (create when asked). This file is the agent spec. All conventions for palette, export templates, project JSON, and module layering are defined here and in this repository.

## Target game data shapes

Agents should treat these as the canonical export contract unless the user changes them.

### Tileset

- **Fixed size: 256 tiles** (indices 0–255) — matches a full TMS9918 pattern table
- Slots are never added or removed; the user picks the active slot from a **16×16 tile-picker window**
- Empty slots export as zeroed pattern bytes and a default color table unless the user draws into them

### Base tile (pattern + color table)

Each tileset slot has **two** exported byte blocks for Graphics II:

| Data | Size | Purpose |
|------|------|---------|
| **Pattern** | 8 bytes | One byte per row — bitplane, MSB = leftmost pixel |
| **Color table** | 8 bytes | One byte per row — foreground and background colors for that scanline |

- One tile per tileset slot; tile indices are 0–255
- **Pattern grid** (`pattern`): 8×8 values of `0` or `1`. `0` = use the row's background color; `1` = use the row's foreground color.
- **Line colors** (`colors`): 8 entries, one per row top-to-bottom. Each entry is `{fg, bg}` with TMS9918 indices 0–15.
- **Color byte encoding** (per scanline): `(fg << 4) | bg` — high nibble = foreground, low nibble = background.
- Canvas preview resolves each pixel as `colors[row].fg` if `pattern[row][col] == 1`, else `colors[row].bg`.
- Metatile/supertile composite previews must resolve pixels through each referenced tile's pattern + line colors.

```asm
PATTERNS
    BYTE >00,>10,>30,>7e,>7e,>30,>10,>00   ; tile 0 pattern

COLORS
    BYTE >f1,>f1,>f1,>f1,>f1,>f1,>f1,>f1   ; tile 0 color table (fg=15, bg=1 per row)
```

### Metatile

- 2×2 grid of **base tile indices** (4 bytes)
- Row-major order: top-left, top-right, bottom-left, bottom-right

```asm
METAS
    BYTE >01,>01,>01,>01   ; metatile 0
    BYTE >02,>02,>02,>02   ; metatile 1
```

### Supertile

- 4×5 grid of **metatile indices** (20 bytes)
- Row-major order: four columns across, five rows down

```asm
SUPERS
    BYTE >03,>00,>00,>01   ; row 0
    BYTE >03,>04,>01,>02   ; row 1
    BYTE >02,>02,>01,>00   ; row 2
    BYTE >01,>01,>03,>03   ; row 3
    BYTE >00,>00,>00,>00   ; row 4
```

### Playfield (future)

- Dimensions TBD — define when map editing is scoped
- Each supertile covers 8×10 characters (64×80 pixels)

## Repository layout (target)

Greenfield repo — grow into this structure incrementally:

```
src/
  editor.py              # App entry: shared project, launches all editor windows
  project.py             # Single project state + change notifications
  tileset_editor.py      # Tileset editor window
  metatile_editor.py     # Metatile editor window
  supertile_editor.py    # Supertile editor window
  tile_canvas.py         # 8×8 grid + per-row fg/bg swatch column
  tile_picker.py         # 16×16 tile-picker window (256 thumbnails)
  composite.py           # Resolve metatile/supertile preview pixels from project
  tile_model.py          # Tile / metatile / supertile data structures, validation
  palette.py             # TMS9918 color constants and swatch helpers
  pattern_export.py      # 8×8 bitplane → 8 pattern bytes
  color_export.py        # Per-line fg/bg → 8 color-table bytes
  asm_export.py          # Assembly text rendering
  asm_format_schema.py   # Load export format directories
  binary_export.py       # Raw byte output

formats/
  ti99_default/          # TI-99 BYTE export (default)
  generic_db/            # Alternate db/$XX style

tests/
  test_*.py              # unittest suite (no pytest)

docs/                    # Optional design notes (only when user asks)
```

Keep business logic out of `editor.py` when it can live in pure, testable modules.

## Commands

```bash
# Run the editor (once entry point exists)
python3 src/editor.py

# Run all tests (required before finishing substantive changes)
python3 -m unittest discover -s tests

# Debug logging (convention — define env var when adding diagnostics)
TILE_EDITOR_DEBUG=1 python3 src/editor.py
```

No linter, formatter, or CI config yet. Match existing style in touched files.

## TMS9918 palette

Canonical color indices for pattern, color-table, and UI swatches. Define RGB tuples in `palette.py`. Color 0 is transparent (checkerboard in the UI).

| # | Name | RGB (display) | Notes |
|---|------|---------------|-------|
| 0 | Transparent | — | Checkerboard in UI |
| 1 | Black | (0, 0, 0) | |
| 2 | Medium Green | (33, 200, 66) | |
| 3 | Light Green | (66, 220, 99) | |
| 4 | Dark Blue | (66, 66, 200) | |
| 5 | Light Blue | (99, 99, 255) | |
| 6 | Dark Red | (200, 66, 66) | |
| 7 | Cyan | (33, 200, 200) | |
| 8 | Medium Red | (200, 66, 66) | |
| 9 | Light Red | (255, 99, 99) | |
| 10 | Dark Yellow | (200, 200, 66) | |
| 11 | Light Yellow | (200, 200, 99) | |
| 12 | Dark Green | (66, 200, 66) | |
| 13 | Magenta | (200, 66, 200) | |
| 14 | Gray | (200, 200, 200) | |
| 15 | White | (255, 255, 255) | |

## Multi-window layout

**All three editors are open at the same time.** There is no mode switching — tileset, metatile, and supertile authoring happen in separate windows that share one in-memory project and **update each other live**.

| Window | Primary canvas | Edits |
|--------|----------------|-------|
| **Tileset editor** | 8×8 grid + per-row fg/bg swatches | `tiles[i].pattern`, `tiles[i].colors[8]` |
| **Metatile editor** | 16×16 composite preview + 2×2 cell picker | `metatiles[i].cells[4]` |
| **Supertile editor** | 64×80 composite preview + 4×5 cell picker | `supertiles[i].cells[20]` |

On launch, open all three editor windows (and keep them open). Use a **Window** menu on each (or a small app coordinator) to raise/hide editors. Closing one editor must not exit the app unless it is the last window — prefer **File → Exit** to quit.

### Live downstream updates

All windows bind to a single `Project` instance (`project.py`). Any edit propagates downstream immediately — no manual refresh button.

```
Tile edit (slot i)
  → tile picker thumbnail i
  → every metatile whose cells reference i
  → every supertile whose cells reference those metatiles

Metatile edit (slot j)
  → metatile j preview
  → every supertile whose cells reference j

Supertile edit (slot k)
  → supertile k preview only
```

Implementation requirements:

- **One source of truth** — `Project` holds `tiles[256]`, `metatiles[]`, `supertiles[]`; editor windows never keep private copies of data they display.
- **Change notifications** — after any mutation, call `project.notify(ChangeEvent)` (e.g. `tile_changed(i)`, `metatile_changed(j)`, `supertile_changed(k)`). Listeners re-render only what they show.
- **Composite resolution** — `composite.py` resolves metatile/supertile pixels by walking tile indices → pattern + line colors. Used by metatile/supertile windows and tile-picker thumbnails.
- **Debouncing optional** — per-pixel tile drawing may batch notifications until mouse-release; color-table and index assignment changes notify immediately.
- **Export panels** — each editor window has its own live ASM/binary panel for its level; all panels update when relevant data changes.

### UI conventions

- **Tileset window:** palette (left), tile canvas + export (center), tile index + **Select Tile…** (sidebar)
- **Metatile window:** metatile list + add/remove/rename (left), 2×2 picker + composite + export (center)
- **Supertile window:** supertile list + add/remove/rename (left), 4×5 picker + composite + export (center)
- **Shared:** status bar per window showing that editor's active slot; **File** menu (New/Load/Save/Exit) on each window or one coordinator — must not desync project state
- **No Mode menu** — replaced by **Window** menu (focus Tileset / Metatile / Supertile)
- Zoom: each pixel at least 16–20 screen pixels on the tileset draw grid

### Tile editing canvas (tileset mode)

The tile canvas is a single composite widget: the 8×8 draw area on the left, and a **per-row color column** on the right.

```
┌────────────────┬─────┐
│                │ FG BG│  row 0
│                │ ■  ■ │
│    8 × 8       │ ■  ■ │  row 1
│    pixel       │ ■  ■ │  row 2
│    grid        │  …   │
│                │ ■  ■ │  row 7
└────────────────┴─────┘
```

- **Eight rows** of swatches, each vertically aligned with the corresponding pattern row.
- **Two squares per row** on the right: left = foreground, right = background.
- Each square shows the current TMS9918 color for that row (`colors[row].fg` / `colors[row].bg`).
- Click a swatch to select it as the palette target; the next palette click assigns that color to the row's fg or bg.
- Drawing on the grid: left click/drag = set pixel to `1` (foreground), right click/drag = set pixel to `0` (background).
- The grid renders resolved colors per pixel using that row's fg/bg pair.
- Highlight the active row (selected swatch pair or last-edited row) so fg/bg edits are unambiguous.

### Tile picker window (tileset mode)

A separate window for choosing which of the 256 tileset slots to edit.

```
┌─ Select Tile ─────────────────────┐
│  0   1   2   3  …  14  15        │
│ ┌──┬──┬──┬──┬     ┬──┬──┐       │
│ │  │  │  │  │ ... │  │  │  row 0 │
│ ├──┼──┼──┼──┼     ┼──┼──┤       │
│ │  │  │  │  │ ... │  │  │  row 1 │
│ │  │  │  │  │     │  │  │        │
│ │  │  │  │  │ ... │  │  │  ...   │
│ └──┴──┴──┴──┴     ┴──┴──┘ row 15 │
│ 16  17  18  …              255   │
└───────────────────────────────────┘
```

- **Layout:** 16 columns × 16 rows = 256 cells, index **row-major** (0 top-left → 255 bottom-right).
- **Cell content:** scaled thumbnail of the tile (resolved pattern + per-line colors); empty slots show a neutral placeholder.
- **Selection:** click a cell to make it the active edit slot; close or keep the window open (user preference — default: stay open, non-modal `Toplevel`).
- **Highlight:** clearly mark the currently active slot; optional hover shows index/name (`TIL00`–`TILFF`).
- **Open from:** **Select Tile…** button (tileset mode sidebar) and/or **Tiles → Select Tile…** menu item.
- **Status bar:** always show active tile index and name (e.g. `Tile 42 / TIL2A`).
- **Reuse:** same picker when the metatile editor assigns a base-tile index — title differs (`Select Tile for Cell` vs `Select Tile to Edit`). Metatile picker for supertile cells is a separate control (list or grid of metatile thumbnails).

Thumbnail size should be readable but compact enough that the full 16×16 grid fits without scrolling on a typical display (e.g. 2× or 3× scale per pixel).

## Development phases

Build **one phase at a time**. After each phase, stop and report completion before starting the next unless the user says to continue.

### Phase 1: Shell + tileset canvas

- `editor.py` creates shared `Project` and opens the **tileset editor** window (metatile/supertile windows stubbed or hidden until later phases)
- 8×8 drawing canvas with visible grid and zoom
- Status bar, menu skeleton (File, Window, Help)
- Single in-memory tile in shared project

**Deliverable:** `python3 src/editor.py` runs and shows the tileset editor with an empty 8×8 grid.

### Phase 2: Palette + drawing + line colors

- TMS9918 palette sidebar (left) for choosing colors
- Tile canvas: 8×8 grid with **two fg/bg swatch squares per row** on the right, aligned to scanlines
- Click swatch → palette click assigns fg or bg for that row; default all rows to fg=15, bg=1
- Left/right mouse sets pattern bits (1/0); grid renders resolved TMS9918 colors per row
- Undo/redo (≥10 steps), clear tile (resets pattern and optionally line colors)

### Phase 3: Tileset management + tile picker

- 256 fixed tile slots in memory (indices 0–255; default names `TIL00`–`TILFF`)
- **Tile picker window:** 16×16 thumbnail grid; click to switch active edit slot
- Thumbnails live-update when a tile is edited; highlight active slot
- Clear tile, duplicate-to-slot (destination chosen via tile picker), optional per-tile rename
- No add/remove — slot count is always 256

### Phase 4: Metatile editor window + live tile cascade

- Open **metatile editor** alongside tileset editor (both visible by default)
- `project.notify` wiring: tile edits refresh metatile composites that reference the changed tile
- 2×2 picker: each cell shows a base-tile preview; click to assign tile index via shared **16×16 tile picker**
- Metatile list with add/remove/rename
- Live 16×16 composite preview

### Phase 5: Supertile editor window + full cascade

- Open **supertile editor** alongside the other two editors
- Tile edits cascade through metatiles into supertiles; metatile edits cascade into supertiles
- 4×5 picker over metatile previews; click cell to assign metatile index
- Supertile list with add/remove/rename
- Live 64×80 composite preview

### Phase 6: Project I/O + export

- Save/load JSON project (see schema below)
- Assembly export via `formats/` templates (`BYTE >xx,>yy,…`)
- Binary export for raw pattern bytes, color-table bytes, and index tables
- Separate export sections: `PATTERNS`, `COLORS`, `METAS`, `SUPERS`

### Phase 7: Playfield preview (optional)

- Map editor placing supertile indices on a grid (dimensions TBD)
- Full-screen composite preview
- Export playfield byte table

### Phase 8: Polish

- Keyboard shortcuts, ttk styling
- Bulk line-color tools (copy row colors, fill all rows, apply fg/bg to selection)
- Help → About

## Project JSON (target schema)

Versioned JSON project file:

```json
{
  "version": 1,
  "tiles": [
    {
      "name": "TIL00",
      "pattern": [[0, 1, ...], ...],
      "colors": [
        {"fg": 15, "bg": 1},
        {"fg": 15, "bg": 1},
        {"fg": 15, "bg": 1},
        {"fg": 15, "bg": 1},
        {"fg": 15, "bg": 1},
        {"fg": 15, "bg": 1},
        {"fg": 15, "bg": 1},
        {"fg": 15, "bg": 1}
      ]
    }
  ],
  "metatiles": [
    {
      "name": "MT00",
      "cells": [0, 0, 0, 0]
    }
  ],
  "supertiles": [
    {
      "name": "ST00",
      "cells": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
  ],
  "playfield": null
}
```

- `tiles`: always 256 entries on save (pad with empty tiles if needed)
- `pattern`: 8×8 grid of bit values `0` or `1`
- `colors`: **required** — exactly 8 entries of `{fg, bg}` (one per scanline, top to bottom); each value 0–15
- `cells`: indices into the parent level's table (metatile cells: 4; supertile cells: 20)
- On load: pad missing `colors` to 8 rows with default `{fg: 15, bg: 1}`; coerce invalid pattern values to 0/1
- Validate indices on load; reject or clamp with a visible warning

## Export formats

ASM output is driven by template directories in `formats/`. Each format is a folder containing:

- `format.json` — dialect (`BYTE`, `>xx` hex prefix, indent, comment prefix) and label patterns
- `*.tpl` — `str.format()` templates rendered by `asm_export.py`

Default `ti99_default` should emit game-ready blocks:

```asm
PATTERNS
    BYTE >00,>10,>30,>7e,>7e,>30,>10,>00
    ; ... 256 tiles × 8 bytes ...

COLORS
    BYTE >f1,>f1,>f1,>f1,>f1,>f1,>f1,>f1
    ; ... 256 tiles × 8 bytes ...

METAS
    BYTE >01,>01,>01,>01

SUPERS
    BYTE >03,>00,>00,>01
    BYTE >03,>04,>01,>02
    ; ... 5 rows × 4 bytes ...
```

**Binary layout** for a full tileset export:

1. Pattern table — 256 × 8 = 2048 bytes
2. Color table — 256 × 8 = 2048 bytes

Label patterns (suggested defaults — adjust if user specifies otherwise):

| Resource | Label pattern |
|----------|---------------|
| Pattern table | `PATTERNS` |
| Color table | `COLORS` |
| Tile pattern (single) | `{tile_name}` or `TIL_{index:02d}` |
| Tile colors (single) | `{tile_name}_COL` or `TIL_{index:02d}_COL` |
| Metatile block | `{meta_name}` or `MT_{index:02d}` |
| Supertile block | `{super_name}` or `ST_{index:02d}` |

Each editor window's export panel shows that level's data (and full-table export where appropriate). Provide **Copy Assembly** and **Save Binary…** buttons on each panel.

## Architecture guidelines

### Layering

| Layer | Module | Responsibility |
|-------|--------|----------------|
| App entry | `editor.py` | Create `Project`, open all editor windows, app lifecycle |
| Shared state | `project.py` | Single project, mutations, `notify()` / listener registry |
| Editors | `tileset_editor.py`, `metatile_editor.py`, `supertile_editor.py` | One window each; subscribe to project changes |
| Data model | `tile_model.py` | Structs, validation, deep copy helpers |
| Compositing | `composite.py` | Metatile/supertile pixel resolution from tile data |
| Canvas | `tile_canvas.py` | 8×8 tile grid + per-row fg/bg column |
| Tile picker | `tile_picker.py` | 16×16 thumbnail grid window, selection callback |
| Palette | `palette.py` | Color constants, swatch widgets |
| Pattern bytes | `pattern_export.py` | 8×8 bitplane → 8-byte TMS9918 pattern encoding |
| Color bytes | `color_export.py` | 8 `{fg, bg}` rows → 8-byte color-table encoding |
| ASM export | `asm_export.py` | Pure rendering from model dicts |
| Formats | `asm_format_schema.py` | Scan `formats/*/format.json`, load `.tpl` |
| Binary | `binary_export.py` | Raw bytes for patterns and index tables |

### Data invariants

Preserve unless the user explicitly changes product behavior:

1. **Index integrity** — Metatile cells reference valid tile indices (0–255); supertile cells reference valid metatile indices. Clearing or overwriting a referenced tile must warn.
2. **Fixed geometry** — Tileset = 256 slots; base = 8×8; metatile = 2×2; supertile = 4×5. Do not parameterize without user request.
3. **Row-major order** — All cell arrays index left-to-right, top-to-bottom.
4. **Pattern encoding** — Bitplane only (0/1 per pixel); MSB-left per row, 8 bytes per tile — must match VDP layout.
5. **Color encoding** — Exactly 8 color bytes per tile; byte `n` = `(fg << 4) | bg` for row `n`; must match Graphics II color-table layout.
6. **Deep copy** — Mutate snapshots via `copy.deepcopy` or dedicated helpers before commit.
7. **Live cascade** — Editor windows read from `Project` only; never stale cached composites after upstream edits. Tests in `test_composite.py` cover invalidation logic without Tk.

### Testing

- Framework: `unittest` (stdlib)
- Tests import from `src/` via `sys.path.insert`
- Headless UI tests: create editor with `create_ui=False`, `root.withdraw()`, destroy in `tearDown`
- Pure logic (pattern encoding, index validation, export text) must have tests without Tk

| Area | Test file (create as needed) |
|------|------------------------------|
| Pattern byte encoding | `test_pattern_export.py` |
| Color byte encoding | `test_color_export.py` |
| Model validation | `test_tile_model.py` |
| Metatile/supertile composition | `test_composite.py` |
| ASM export | `test_asm_export.py` |
| Format templates | `test_asm_format.py` |
| Binary export | `test_binary_export.py` |

## Coding guidelines

- **Minimal diffs** — Small, focused changes; no drive-by refactors.
- **No new dependencies** — Stdlib only (Tkinter, json, unittest, copy, os).
- **Naming** — `snake_case`, private helpers prefixed `_`, constants `UPPER_SNAKE`.
- **Tk callbacks** — Handlers bound to keys/protocols accept `event=None`.
- **UI refresh** — Mutate via `Project` methods, then `notify()`. Each listener updates list → canvas → export panel → status bar. Downstream windows must subscribe, not poll on focus.
- **Reuse** — Share helpers across modules in this repo (`palette.py`, `pattern_export.py`, `color_export.py`, `composite.py`) rather than duplicating logic in editor windows.

## What not to do

- Do not add pip/package dependencies without explicit user approval.
- Do not introduce Pygame, Pillow, Qt, or web UI frameworks.
- Do not create markdown files the user did not ask for (except this file).
- Do not skip running tests after substantive changes.
- Do not break index references silently on delete — always warn.
- Do not change the 256-tile / 2×2 / 4×5 geometry without user approval.
- Do not replace multi-window editors with a single mode-switching UI unless the user asks.
- Do not let editor windows hold divergent copies of tile/metatile/supertile data.
- Do not reference or depend on code, docs, or conventions from outside this repository in project files unless the user explicitly asks.

## License

MIT — see `LICENSE`.