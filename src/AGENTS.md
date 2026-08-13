# src/AGENTS.md — Architecture and Conventions

## Project description

**burglekutt** — a TI-99/4A Zelda-like game authoring toolchain (Python 3.6+ stdlib, Tkinter). Targets **memory-reduced Graphics II**: per-line color within each 8×8 tile, but **256 unique tiles max** (not the 768-tile full G2 layout). Three apps developed in sequence: tile editor (complete), tile image editor (next), map/screen editor (follow-on).

### Key design decisions

- Fixed 256-slot tileset, 2×2 metatiles, 4×4 supertiles — geometry is not parameterized
- Bitplane pattern encoding (MSB-left, 8 bytes per tile)
- Per-scanline color tables (`(fg << 4) | bg`, 8 bytes per tile)
- Multi-window architecture: all editors share one `Project` instance with live cascade updates
- No pip dependencies — stdlib only (Tkinter, json, unittest, copy, os)
- On-demand export preview (no embedded live export panels)

## Directory structure (`src/`)

```
src/
├── editor.py              # App coordinator: Project + three editor windows
├── project.py            # Graphics project state + change notifications
├── project_io.py         # JSON save/load (version 2, tile_images)
├── tileset_editor.py      # Tileset editor window
├── metatile_editor.py     # Metatile editor window
├── supertile_editor.py    # Supertile editor window
├── tile_canvas.py        # 8×8 grid + per-row fg/bg swatch column
├── tile_picker.py        # 16×16 picker window for tiles (256 slots)
├── metatile_picker.py     # Picker for metatiles (up to 256)
├── composite.py          # Resolve metatile/supertile preview pixels
├── pixel_canvas.py       # PhotoImage rendering for composites/thumbnails
├── tile_model.py         # Tile / metatile / supertile structs, validation
├── palette.py            # TMS9918 color constants, palette popup/panel
├── theme.py              # Per-window backgrounds, namespaced ttk styles
├── undo_stack.py         # Per-tile undo/redo stack
├── line_color_dialogs.py # Fill all rows / copy row colors dialogs
├── shortcuts.py          # Keyboard shortcut bindings + help text
├── export_preview.py     # On-demand export preview window
├── pattern_export.py     # 8×8 bitplane → 8 pattern bytes
├── color_export.py       # Per-line fg/bg → 8 color-table bytes
├── asm_export.py         # Assembly text rendering
├── asm_format_schema.py  # Load export format directories
├── binary_export.py      # Raw byte output
├── image_editor.py       # Tile image editor entry
├── image_editor_window.py # Tile image editor window (Phase 4 I/O + export)
├── image_model.py        # Tile image structs, validation, unique-tile budget
├── image_export.py       # Tile-image dedupe, local remap, patterns/colors/map
├── map_editor.py         # Map/screen editor (follow-on)
├── map_model.py          # (follow-on)
├── screen_editor.py      # (follow-on)
└── world_editor.py       # (follow-on)
```

Keep business logic out of `editor.py` when it can live in pure, testable modules.

## Layering

| Layer | Module | Responsibility |
|-------|--------|----------------|
| App entry | `editor.py` | Create `Project`, open all editor windows, app lifecycle, app-wide shortcuts |
| Shared state | `project.py` | Single project, mutations, `notify()` / listener registry |
| Project I/O | `project_io.py` | JSON save/load, normalization on load |
| Editors | `tileset_editor.py`, `metatile_editor.py`, `supertile_editor.py` | One window each; subscribe to project changes |
| Data model | `tile_model.py` | Structs, validation, deep copy helpers |
| Compositing | `composite.py` | Metatile/supertile/tile-image pixel resolution from tile data |
| Rendering | `pixel_canvas.py` | Fast PhotoImage/PPM grid drawing for previews |
| Canvas | `tile_canvas.py` | 8×8 tile grid + per-row fg/bg column |
| Tile picker | `tile_picker.py` | 16×16 grid at `PICKER_TILE_SCALE_*`; accent border on active slot |
| Metatile picker | `metatile_picker.py` | Thumbnail grid for defined metatiles (up to 256) |
| Theme | `theme.py` | Per-window tints, namespaced ttk styles |
| Palette | `palette.py` | TMS9918 color constants, palette popup/panel |
| Line colors | `line_color_dialogs.py` | Fill-all-rows and copy-row-colors dialogs |
| Shortcuts | `shortcuts.py` | `bind_app_shortcuts`, per-editor bindings, help text |
| Export UI | `export_preview.py` | On-demand assembly/binary preview window |
| Pattern bytes | `pattern_export.py` | 8×8 bitplane → 8-byte TMS9918 pattern encoding |
| Color bytes | `color_export.py` | 8 `{fg, bg}` rows → 8-byte color-table encoding |
| ASM export | `asm_export.py` | Pure rendering from model dicts |
| Formats | `asm_format_schema.py` | Scan `formats/*/format.json` |
| Binary | `binary_export.py` | Raw bytes for patterns and index tables |
| Image export | `image_export.py` | Tile-image dedupe, local remap, patterns/colors/map ASM+binary |
| Undo | `undo_stack.py` | Per-tile undo/redo stack |

## Data invariants

1. **Index integrity** — Metatile cells reference valid tile indices (0–255); supertile cells reference valid metatile indices (`0 .. metatile_count-1`). Clearing or overwriting a referenced tile, or deleting a referenced metatile, must warn.
2. **Table sizes** — Tileset = exactly 256 slots; metatile set = 0–256; supertile set = 0–256. Block adds beyond 256.
3. **Fixed geometry** — Base = 8×8; metatile = 2×2 tiles + 1 flags byte; supertile = 4×4. Do not parameterize without user request.
4. **Metatile flags** — Every metatile has exactly one `flags` byte in export (leading byte). JSON stores `flags` as integer 0–255; UI maps to named toggles per bit table.
5. **Row-major order** — All cell arrays index left-to-right, top-to-bottom.
6. **Pattern encoding** — Bitplane only (0/1 per pixel); MSB-left per row, 8 bytes per tile — must match VDP layout.
7. **Color encoding** — Exactly 8 color bytes per tile; byte `n` = `(fg << 4) | bg` for row `n`; must match Graphics II color-table layout.
8. **Deep copy** — Mutate snapshots via `copy.deepcopy` or dedicated helpers before commit.
9. **Live cascade** — Editor windows read from `Project` only; never stale cached composites after upstream edits.
10. **Tile image Graphics II** — Memory-reduced mode: **`width × height` ≤ 256** cells and **≤ 256 unique tiles** per image (not 768). Exported image tilesets always include paired pattern + color-table bytes (8 per tile); layout map uses local indices 0–255 only.

## Coding standards

### Style
- **Language:** Python 3.6+ (stdlib only — no pip dependencies)
- **UI:** Tkinter / ttk
- No linter, formatter, or CI config yet. Match existing style in touched files.

### Naming

| Category | Convention | Example |
|----------|-----------|---------|
| Functions | snake_case | `get_tile(index)` |
| Classes | PascalCase | `TilesetEditorWindow` |
| Modules | snake_case | `tile_model.py` |
| Constants | UPPER_SNAKE | `TILE_COUNT`, `TILE_SIZE` |
| Private | `_` prefix | `_normalize_pattern()` |

### Tk callbacks
Handlers bound to keys/protocols accept `event=None`.

### UI refresh
Mutate via `Project` methods, then `notify()`. Each listener updates list → canvas → status bar. Downstream windows must subscribe, not poll on focus.

### Reuse
Share helpers across modules (`palette.py`, `pattern_export.py`, `color_export.py`, `composite.py`) rather than duplicating logic in editor windows.

## Export formats

ASM output is driven by format directories in `formats/`. Default `ti99_default` emits game-ready blocks:

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
    ; ... 4 rows × 4 bytes per supertile ...
    ; ... M supertiles × 16 bytes (M ≤ 256) ...
```

Binary layout for a full export:

| Block | Size |
|-------|------|
| Pattern table | 256 × 8 = 2048 bytes |
| Color table | 256 × 8 = 2048 bytes |
| Metatile table | N × 5 bytes (N = metatile count, max 256) |
| Supertile table | M × 16 bytes (M = supertile count, max 256) |

Label patterns:

| Resource | Label pattern |
|----------|---------------|
| Pattern table | `PATTERNS` |
| Color table | `COLORS` |
| Metatile block | `METAS` / `METASEND` |
| Supertile block | `SUPERS` / `SUPERSEND` |
| Tile image patterns | `{image_name}_PATTERNS` |
| Tile image colors | `{image_name}_COLORS` |
| Tile image layout map | `{image_name}_MAP` / `{image_name}_MAPEND` |

## TMS9918 palette

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

## What not to do

- Do not add pip/package dependencies without explicit user approval.
- Do not introduce Pygame, Pillow, Qt, or web UI frameworks.
- Do not skip running tests after substantive changes.
- Do not break index references silently on delete — always warn.
- Do not change the 256-tile / 256-metatile / 256-supertile limits or 2×2 / 4×4 geometry without user approval.
- Do not replace multi-window editors with a single mode-switching UI unless the user asks.
- Do not let editor windows hold divergent copies of tile/metatile/supertile data.
- Do not reference or depend on code, docs, or conventions from outside this repository unless the user explicitly asks.
- Do not implement map/screen editor features until tile image editor phases are complete unless the user explicitly reprioritizes.
- Do not implement tile image editor during tile-editor regression fixes unless the user explicitly asks.
- Do not ship a tile draw canvas smaller than `TILE_PIXEL_SCALE_MIN` — pixel editing must remain practical.

## Testing

- Framework: `unittest` (stdlib)
- Tests import from `src/` via `sys.path.insert`
- Headless UI tests: create editor with `create_ui=False`, `root.withdraw()`, destroy in `tearDown`
- Pure logic tests must not require Tk

| Area | Test file |
|------|-----------|
| Pattern byte encoding | `test_pattern_export.py` |
| Color byte encoding | `test_color_export.py` |
| Model validation | `test_tile_model.py` |
| Metatile/supertile composition | `test_composite.py` |
| ASM export | `test_asm_export.py` |
| Format dialect | `test_asm_format.py` |
| Binary export | `test_binary_export.py` |
| Project I/O | `test_project_io.py` |
| Export preview helpers | `test_export_preview.py` |
| Line color batch ops | `test_line_colors.py` |
| Line color dialogs | `test_line_color_dialogs.py` |
| Tile canvas geometry | `test_tile_canvas.py` |
| Tile picker | `test_tile_picker.py` |
| Palette | `test_palette.py` |
| Pixel canvas | `test_pixel_canvas.py` |
| Project mutations | `test_project.py` |
| Theme styles | `test_theme.py` |
| Undo stack | `test_undo_stack.py` |
| Tile image export | `test_image_export.py` |
| Tile image editor geometry | `test_image_editor_window.py` |
| Tile image model | `test_image_model.py` |

## Commands

```bash
# Run all tests
python3 -m unittest discover -s tests

# Launch apps
python3 src/editor.py        # Tile editor (current app)
python3 src/image_editor.py  # Tile image editor (Phase 1 shell)
python3 src/map_editor.py    # Map/screen editor (follow-on)
```
