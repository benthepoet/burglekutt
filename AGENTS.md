# AGENTS.md

Guidance for AI agents working on **burglekutt** — a TI-99/4A Zelda-like game authoring toolchain (Python + Tkinter).

## Project summary

This repository contains **two apps**, developed in sequence:

| App | Entry point | Status |
|-----|-------------|--------|
| **Tile editor** | `python3 src/editor.py` | **Current work** — tileset, metatile, supertile authoring |
| **Map/screen editor** | `python3 src/map_editor.py` | **Follow-on** — after tile editor is complete |

The tile editor is a desktop app with **three simultaneous windows** (tileset, metatile, supertile). Edits propagate downstream live — change a base tile and every metatile/supertile that references it updates immediately.

| Level | Composition | Pixel size | Purpose |
|-------|-------------|------------|---------|
| **Tileset** | 256 base tiles | — | Full pattern table (one TMS9918 tile per slot) |
| **Base tile** | 8×8 pixels | 8×8 | Single pattern-table entry (index 0–255) |
| **Metatile set** | up to 256 metatiles | — | Composed chunks referencing base tiles |
| **Metatile** | 2×2 base tiles | 16×16 | Reusable terrain/object chunks |
| **Supertile set** | up to 256 supertiles | — | Composed blocks referencing metatiles |
| **Supertile** | 4×5 metatiles | 64×80 | Screen-building blocks for the playfield |

The editor must produce data the game can consume directly — **pattern bytes**, **color-table bytes**, metatile tables, and supertile maps — as assembly `BYTE` blocks (`PATTERNS`, `COLORS`, `METAS`, `SUPERS`).

- **Language:** Python 3.6+ (stdlib only — no pip dependencies)
- **UI:** Tkinter / ttk

User-facing docs belong in `README.md` (create when asked). This file is the agent spec. All conventions for palette, export templates, project JSON, and module layering are defined here and in this repository.

**Scope rule:** Implement tile-editor phases first. Do not start map/screen editor work until tile-editor phases are complete (through Phase 7 Polish) unless the user explicitly says otherwise.

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

### Metatile set

- **Up to 256 metatiles** (indices 0–255); default names `MT00`–`MTFF`
- Add and remove metatiles in the metatile editor; block add when count would exceed 256
- Indices are dense: `0 .. count-1`. Removing a metatile reindexes or compacts — warn if any supertile still references it
- Export emits **5 bytes** per defined metatile: 1 header byte + 4 tile-index bytes (not padded to 256 unless export format requires it)

### Metatile

Each metatile record is **5 bytes** in export order:

| Byte | Field | Purpose |
|------|-------|---------|
| 0 | **Flags** | Collision/behavior type for the game engine |
| 1–4 | **Cells** | 2×2 grid of base tile indices |

**Cells** — row-major order: top-left, top-right, bottom-left, bottom-right. Each value must be a valid tile index (0–255).

**Flags byte** — bitfield; multiple attributes can be set. The metatile editor exposes these as checkboxes (or equivalent). Refine bit meanings with the game engine as needed; default definitions:

| Bit | Mask | Meaning |
|-----|------|---------|
| 0 | `>01` | **Solid** — blocks movement |
| 1 | `>02` | **Hurt** — damages the player on contact |
| 2 | `>04` | **Water** — swim/wade behavior |
| 3 | `>08` | **Door** — doorway / transition trigger |
| 4 | `>10` | **Stairs** — elevation change |
| 5–7 | — | Reserved (0) |

Example: solid rock = `>01`; lava (solid + hurt) = `>03`; open water = `>04`.

```asm
METAS
    BYTE >01              ; metatile 0 flags: solid
    BYTE >00,>00,>01,>00  ; metatile 0 tiles
    BYTE >03              ; metatile 1 flags: solid + hurt
    BYTE >02,>02,>02,>02  ; metatile 1 tiles
    ; ... up to 256 metatiles × 5 bytes ...
METASEND
```

The game reads the flags byte at runtime for collision and interaction; graphics come from the four tile indices only.

### Supertile set

- **Up to 256 supertiles** (indices 0–255); default names `ST00`–`STFF`
- Add and remove supertiles in the supertile editor; block add when count would exceed 256
- Indices are dense: `0 .. count-1`
- Export emits 20 bytes per defined supertile

### Supertile

- 4×5 grid of **metatile indices** (20 bytes per supertile)
- Row-major order: four columns across, five rows down
- Each cell value must be a valid metatile index for the current project (`0 .. metatile_count-1`)

```asm
SUPERS
    BYTE >03,>00,>00,>01   ; row 0
    BYTE >03,>04,>01,>02   ; row 1
    BYTE >02,>02,>01,>00   ; row 2
    BYTE >01,>01,>03,>03   ; row 3
    BYTE >00,>00,>00,>00   ; row 4
    ; ... up to 256 supertiles × 20 bytes ...
SUPERSEND
```

### Screens & world (map editor — follow-on)

Screen layout and overworld map editing are **out of scope** for the tile editor. They belong to the map/screen editor app (see below). Each supertile covers 8×10 characters (64×80 pixels) and is the building block that app places on playfields.

## Repository layout (target)

Greenfield repo — grow into this structure incrementally:

```
src/
  # Tile editor app (current)
  editor.py              # Tile editor entry: Project + three editor windows
  project.py             # Graphics project state + change notifications
  tileset_editor.py      # Tileset editor window
  metatile_editor.py     # Metatile editor window
  supertile_editor.py    # Supertile editor window
  tile_canvas.py         # 8×8 grid + per-row fg/bg swatch column
  tile_picker.py         # 16×16 picker window for tiles (256 slots)
  metatile_picker.py     # Picker for metatiles (up to 256; used by supertile editor)
  composite.py           # Resolve metatile/supertile preview pixels (shared)
  tile_model.py          # Tile / metatile / supertile structs, validation
  palette.py             # TMS9918 color constants and swatch helpers
  pattern_export.py      # 8×8 bitplane → 8 pattern bytes
  color_export.py        # Per-line fg/bg → 8 color-table bytes
  asm_export.py          # Assembly text rendering
  asm_format_schema.py   # Load export format directories
  binary_export.py       # Raw byte output

  # Map/screen editor app (follow-on — add after tile editor is complete)
  map_editor.py          # Map editor entry: screen + world windows
  map_model.py           # Screen layouts, world grid, connections
  screen_editor.py       # Single-screen playfield editor window
  world_editor.py        # Overworld / screen-link editor window

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
# Tile editor (current app)
python3 src/editor.py

# Map/screen editor (follow-on — after tile editor is complete)
python3 src/map_editor.py

# Run all tests (required before finishing substantive changes)
python3 -m unittest discover -s tests

# Debug logging (convention — define env var when adding diagnostics)
TILE_EDITOR_DEBUG=1 python3 src/editor.py
MAP_EDITOR_DEBUG=1 python3 src/map_editor.py
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
| **Metatile editor** | 16×16 composite preview + 2×2 cell picker | `metatiles[i].flags`, `metatiles[i].cells[4]` |
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

- **One source of truth** — `Project` holds `tiles[256]`, `metatiles[]` (max 256), `supertiles[]` (max 256); editor windows never keep private copies of data they display.
- **Change notifications** — after any mutation, call `project.notify(ChangeEvent)` (e.g. `tile_changed(i)`, `metatile_changed(j)`, `supertile_changed(k)`). Listeners re-render only what they show.
- **Composite resolution** — `composite.py` resolves metatile/supertile pixels by walking tile indices → pattern + line colors. Used by metatile/supertile windows and tile-picker thumbnails.
- **Debouncing optional** — per-pixel tile drawing may batch notifications until mouse-release; color-table and index assignment changes notify immediately.
- **Export panels** — each editor window has its own live ASM/binary panel for its level; all panels update when relevant data changes.

### UI conventions

- **Tileset window:** palette (left), tile canvas + export (center), tile index + **Select Tile…** (sidebar)
- **Metatile window:** metatile list + add/remove/rename (left), **flags/type controls**, 2×2 picker + composite + export (center)
- **Supertile window:** supertile list + add/remove/rename (left), 4×5 picker + composite + export (center)
- **Shared:** status bar per window showing that editor's active slot; **File** menu (New/Load/Save/Exit) on each window or one coordinator — must not desync project state
- **No Mode menu** — replaced by **Window** menu (focus Tileset / Metatile / Supertile)
### Tile editing canvas (tileset mode)

The tile canvas must be **large enough to draw comfortably** — this is the primary workspace and must not feel cramped. Define scale constants in `tile_canvas.py` (or `palette.py` if shared).

| Constant | Value | Notes |
|----------|-------|-------|
| `TILE_PIXEL_SCALE_DEFAULT` | **32** | Screen pixels per pattern pixel (8×8 → **256×256** draw area) |
| `TILE_PIXEL_SCALE_MIN` | **24** | Hard minimum (8×8 → 192×192); never render smaller |
| `TILE_PIXEL_SCALE_MAX` | **48** | Optional zoom-in ceiling |

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

**Sizing rules:**

- At default scale (32×), the pattern grid alone is **256×256 px** — large enough for precise pixel placement with the mouse.
- Fg/bg swatch column: each swatch at least **20×20 px**, row height matched to pattern row height (32 px at default scale).
- Visible **grid lines** between pattern pixels at all supported scales.
- Tileset window minimum size must accommodate the full canvas at `TILE_PIXEL_SCALE_MIN` without clipping (pattern grid + swatch column + palette sidebar).
- Optional **View → Zoom In / Zoom Out** (or +/- keys) adjusts scale in steps between min and max; default restored on new session is fine.
- Do not shrink the draw grid below `TILE_PIXEL_SCALE_MIN` when the window is resized — scroll or clamp window size instead.

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
- **Highlight:** the active edit slot gets a distinct **border** (e.g. 2–3 px accent outline around the cell); inactive cells use a neutral or no border. Optional hover shows index/name (`TIL00`–`TILFF`).
- **Open from:** **Select Tile…** button (tileset mode sidebar) and/or **Tiles → Select Tile…** menu item.
- **Status bar:** always show active tile index and name (e.g. `Tile 42 / TIL2A`).
- **Reuse:** same tile picker when the metatile editor assigns a base-tile index — title differs (`Select Tile for Cell` vs `Select Tile to Edit`).
- **Metatile picker:** separate 16×16 thumbnail grid (or scrollable equivalent) for up to 256 defined metatiles; used when the supertile editor assigns a metatile to a cell.

Thumbnail size should be readable but compact enough that the full 16×16 grid fits without scrolling on a typical display (e.g. 2× or 3× scale per pixel).

## Tile editor — development phases

Build **one phase at a time**. After each phase, stop and report completion before starting the next unless the user says to continue.

### Phase 1: Shell + tileset canvas

- `editor.py` creates shared `Project` and opens the **tileset editor** window (metatile/supertile windows stubbed or hidden until later phases)
- 8×8 drawing canvas at **`TILE_PIXEL_SCALE_DEFAULT` (32×)** with visible grid lines
- Enforce `TILE_PIXEL_SCALE_MIN` — canvas must not be too small to use
- Status bar, menu skeleton (File, Window, Help)
- Single in-memory tile in shared project

**Deliverable:** `python3 src/editor.py` runs and shows a comfortably sized 8×8 grid (256×256 px draw area at default scale).

### Phase 2: Palette + drawing + line colors

- TMS9918 palette sidebar (left) for choosing colors
- Tile canvas: 8×8 grid with **two fg/bg swatch squares per row** on the right, aligned to scanlines
- Click swatch → palette click assigns fg or bg for that row; default all rows to fg=15, bg=1
- Left/right mouse sets pattern bits (1/0); grid renders resolved TMS9918 colors per row
- Undo/redo (≥10 steps), clear tile (resets pattern and optionally line colors)

### Phase 3: Tileset management + tile picker

- 256 fixed tile slots in memory (indices 0–255; default names `TIL00`–`TILFF`)
- **Tile picker window:** 16×16 thumbnail grid; click to switch active edit slot
- Thumbnails live-update when a tile is edited; **accent border** on the active slot in the picker
- Clear tile, duplicate-to-slot (destination chosen via tile picker), optional per-tile rename
- No add/remove — slot count is always 256

### Phase 4: Metatile editor window + live tile cascade

- Open **metatile editor** alongside tileset editor (both visible by default)
- `project.notify` wiring: tile edits refresh metatile composites that reference the changed tile
- 2×2 picker: each cell shows a base-tile preview; click to assign tile index via shared **16×16 tile picker**
- **Flags editor:** checkboxes (or toggles) for solid, hurt, water, door, stairs — writes `metatiles[i].flags`
- Metatile list with add/remove/rename (max 256); show flags summary in list where helpful
- Live 16×16 composite preview

### Phase 5: Supertile editor window + full cascade

- Open **supertile editor** alongside the other two editors
- Tile edits cascade through metatiles into supertiles; metatile edits cascade into supertiles
- 4×5 picker over metatile previews; click cell to assign metatile index via **metatile picker**
- Supertile list with add/remove/rename (max 256)
- Live 64×80 composite preview

### Phase 6: Project I/O + export

- Save/load JSON project (see schema below)
- Assembly export via `formats/` templates (`BYTE >xx,>yy,…`)
- Binary export for raw pattern bytes, color-table bytes, and index tables
- Separate export sections: `PATTERNS`, `COLORS`, `METAS`, `SUPERS`

### Phase 7: Polish

- Keyboard shortcuts, ttk styling
- Bulk line-color tools (copy row colors, fill all rows, apply fg/bg to selection)
- Help → About

**Tile editor complete** when Phase 7 is done. Map/screen editor work starts as a separate follow-on (below).

## Follow-on: map & screen editor

A **second app in this repo**, started only after the tile editor is complete. It consumes the same graphics data (`tiles`, `metatiles`, `supertiles`) and adds level-design authoring.

### Responsibilities

| Editor window | Purpose |
|---------------|---------|
| **Screen editor** | Place supertile indices on a single playfield (one room/area) |
| **World editor** | Grid of screens, north/south/east/west links, screen metadata |

Both windows open simultaneously (same pattern as the tile editor). They read graphics tables from `Project` and live-preview via `composite.py`. Screen/world edits do not modify tile pattern or color data.

### Shared repo benefits

- Reuse `project.py`, `composite.py`, `palette.py`, `binary_export.py`, `formats/`
- One project JSON (version 2) holding graphics **and** map data, or load graphics from a v1 file
- One test suite and export dialect

### Map editor entry point

`python3 src/map_editor.py` — creates or loads a `Project`, opens screen + world editor windows.

### Map data shapes (initial — refine when scoped)

**Screen** — supertile grid for one playfield (dimensions TBD; supertile = 64×80 px):

```asm
SCREEN00
    BYTE >01,>01,>00,>03   ; row 0: supertile indices
    ; ... playfield grid rows ...
```

**World** — screen cells and adjacency (format TBD):

```json
{
  "screens": [
    {"name": "SCREEN00", "cells": [1, 1, 0, 3, ...]}
  ],
  "world": {
    "width": 8,
    "height": 8,
    "cells": [0, 0, 1, ...],
    "links": []
  }
}
```

Export targets: `SCREENS`, `WORLD` (and related connection tables) — templates added under `formats/` when implemented.

### Map editor phases (outline)

Build after tile editor Phase 7 is complete, one phase at a time:

1. **Shell** — `map_editor.py`, load graphics from project, screen editor window stub
2. **Screen editor** — supertile picker, playfield grid, live composite preview
3. **World editor** — screen grid, placement, basic metadata
4. **Screen links** — connect screens (doors, edges, stairs)
5. **Project I/O** — JSON v2 with `screens` + `world`; ASM/binary export for map data
6. **Polish** — shortcuts, validation, referential integrity (invalid supertile indices)

Exact playfield dimensions and link encoding are **TBD** when map editor work begins.

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
      "flags": 1,
      "cells": [0, 0, 0, 0]
    }
  ],
  "supertiles": [
    {
      "name": "ST00",
      "cells": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
  ]
}
```

**Version 1** (tile editor): `tiles`, `metatiles`, `supertiles` only.

**Version 2** (map editor follow-on): add `screens` and `world` keys. Map editor must load v1 graphics-only projects; tile editor ignores unknown keys on load.

- `tiles`: always 256 entries on save (pad with empty tiles if needed)
- `metatiles`: 0–256 entries; reject load if more than 256
- `supertiles`: 0–256 entries; reject load if more than 256
- `pattern`: 8×8 grid of bit values `0` or `1`
- `colors`: **required** per tile — exactly 8 entries of `{fg, bg}` (one per scanline, top to bottom); each value 0–15
- `flags`: metatile header byte (0–255 bitfield); default `0`
- `cells`: indices into the parent level's table (metatile cells: 4; supertile cells: 20)
- On load: pad missing `colors` to 8 rows with default `{fg: 15, bg: 1}`; coerce invalid pattern values to 0/1
- Validate indices on load: metatile cells → tile 0–255; supertile cells → metatile 0..`len(metatiles)-1`

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
    BYTE >01              ; flags
    BYTE >00,>00,>01,>00  ; tiles
    ; ... N metatiles × 5 bytes (N ≤ 256) ...

SUPERS
    BYTE >03,>00,>00,>01
    BYTE >03,>04,>01,>02
    ; ... 5 rows × 4 bytes per supertile ...
    ; ... M supertiles × 20 bytes (M ≤ 256) ...
```

**Binary layout** for a full export:

| Block | Size |
|-------|------|
| Pattern table | 256 × 8 = 2048 bytes |
| Color table | 256 × 8 = 2048 bytes |
| Metatile table | N × 5 bytes (N = metatile count, max 256; 1 flags + 4 tiles each) |
| Supertile table | M × 20 bytes (M = supertile count, max 256) |

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
| Tile picker | `tile_picker.py` | 16×16 thumbnail grid; accent border on active slot |
| Metatile picker | `metatile_picker.py` | Thumbnail grid for defined metatiles (up to 256) |
| Palette | `palette.py` | Color constants, swatch widgets |
| Pattern bytes | `pattern_export.py` | 8×8 bitplane → 8-byte TMS9918 pattern encoding |
| Color bytes | `color_export.py` | 8 `{fg, bg}` rows → 8-byte color-table encoding |
| ASM export | `asm_export.py` | Pure rendering from model dicts |
| Formats | `asm_format_schema.py` | Scan `formats/*/format.json`, load `.tpl` |
| Binary | `binary_export.py` | Raw bytes for patterns and index tables |

### Data invariants

Preserve unless the user explicitly changes product behavior:

1. **Index integrity** — Metatile cells reference valid tile indices (0–255); supertile cells reference valid metatile indices (`0 .. metatile_count-1`). Clearing or overwriting a referenced tile, or deleting a referenced metatile, must warn.
2. **Table sizes** — Tileset = exactly 256 slots; metatile set = 0–256; supertile set = 0–256. Block adds beyond 256.
3. **Fixed geometry** — Base = 8×8; metatile = 2×2 tiles + 1 flags byte; supertile = 4×5. Do not parameterize without user request.
4. **Metatile flags** — Every metatile has exactly one `flags` byte in export (leading byte). JSON stores `flags` as integer 0–255; UI maps to named toggles per bit table above.
5. **Row-major order** — All cell arrays index left-to-right, top-to-bottom.
6. **Pattern encoding** — Bitplane only (0/1 per pixel); MSB-left per row, 8 bytes per tile — must match VDP layout.
7. **Color encoding** — Exactly 8 color bytes per tile; byte `n` = `(fg << 4) | bg` for row `n`; must match Graphics II color-table layout.
8. **Deep copy** — Mutate snapshots via `copy.deepcopy` or dedicated helpers before commit.
9. **Live cascade** — Editor windows read from `Project` only; never stale cached composites after upstream edits. Tests in `test_composite.py` cover invalidation logic without Tk.

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
- Do not change the 256-tile / 256-metatile / 256-supertile limits or 2×2 / 4×5 geometry without user approval.
- Do not replace multi-window editors with a single mode-switching UI unless the user asks.
- Do not let editor windows hold divergent copies of tile/metatile/supertile data.
- Do not reference or depend on code, docs, or conventions from outside this repository in project files unless the user explicitly asks.
- Do not implement map/screen editor features during tile-editor phases unless the user explicitly asks.
- Do not ship a tile draw canvas smaller than `TILE_PIXEL_SCALE_MIN` — pixel editing must remain practical.

## License

MIT — see `LICENSE`.