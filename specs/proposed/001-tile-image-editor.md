# 001: Tile Image Editor

**Status:** Proposed
**Priority:** High (user priority: title screen)
**Depends on:** Tile editor (complete)

## Context

The tile editor (tileset, metatile, supertile) is complete. The next app is the **tile image editor** — compose large static images from base tile indices for Graphics II display (title screens, logos, static screens). Export produces a self-contained tileset (patterns + colors) and a layout map.

## Problem

The game uses **memory-reduced Graphics II** with a 256-unique-tile budget. A title screen composed of W×H tile placements must dedupe tiles, remap to local indices, and export pattern bytes, color-table bytes, and a layout map — all without exceeding the 256 unique-tile limit.

## Goals

- Compose large images as a grid of references into the project's 256-slot tileset
- Draw on the image canvas; each pixel edit updates the mapped tileset tile
- Configurable grid dimensions (W×H in tiles)
- Live composite reflecting tileset edits
- Enforce ≤256 unique tiles (not 768)
- Export self-contained tileset + layout map (ASM and binary)
- Multiple named images per project (e.g., TITLE, LOGO)

## Non-goals

- Tile picker / manual cell→tile assignment as the primary authoring flow
- Metatile/supertile composition (that's the tile editor's job)
- Map/screen editor features (follow-on)

## Technical design

### Data model

Each tile image is a named rectangle of global tile indices (0–255):

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | e.g., `TITLE`, `LOGO` |
| `width` | int | Grid width in tiles (≥1) |
| `height` | int | Grid height in tiles (≥1) |
| `cells` | int[] | `width × height` entries, row-major; **`width × height` ≤ 256** and **≤256 distinct values** |

### Export contract

| Block | Size | Purpose |
|-------|------|---------|
| `{name}_PATTERNS` | N × 8 bytes | Pattern bytes for each unique tile used |
| `{name}_COLORS` | N × 8 bytes | Color-table bytes for the same N tiles |
| `{name}_MAP` | W × H bytes | Layout map: local tile indices (0–N-1) |

**Local remap:** Collect unique global indices from `cells` in first-appearance row-major order, assign local indices 0..N-1, remap all cells to local indices.

**256-tile limit:** Reject if N > 256. Error message must cite memory-reduced Graphics II (256 unique tiles, not 768).

### UI

| Component | Description |
|-----------|-------------|
| **Tile grid canvas** | Scrollable/zoomable composite. Left-click paints foreground bits, right-click background bits. Each cell maps to a tileset slot; drawing edits that tile's pattern. Shared cells fork to a free slot (copy-on-write) until 256 unique tiles are in use, then further draws mutate the shared definition. |
| **Image list** | Add/remove/rename images; per-image dimensions set at create time |
| **Status bar** | Shows active image name, dimensions, unique tile count (e.g., `Unique tiles: 42 / 256`) |
| **Theme** | `IMAGE_EDITOR_WINDOW_BG` — new tint (not reusing tileset/metatile/supertile colors) |

### Shared modules

- `project.py` — extend with `tile_images[]`, CRUD, `ChangeEvent.TILE_IMAGE_CHANGED`
- `composite.py` — add `resolve_tile_image_pixels(image, tiles)`
- `tile_picker.py` — not used by the image editor (tileset editor only)
- `theme.py` — add `IMAGE_EDITOR_WINDOW_BG` and related style constants
- `project_io.py` — extend to handle `tile_images` in JSON v2

## Phases

### Phase 1: Shell

- `image_editor.py` — app entry point; loads project tileset, opens editor window
- `image_editor_window.py` — editor UI (or inline initially)
- `theme.py` — add `IMAGE_EDITOR_WINDOW_BG` tint
- Minimal working window with menu bar and status bar

### Phase 2: Grid editor

- Configurable W×H image rendered as a live composite of mapped tileset tiles
- Draw on the canvas (left = fg, right = bg) to update the tile definition for that cell
- Copy-on-write: first draw on a shared cell allocates a free tileset slot (until 256 unique)
- If all 256 unique tiles are already used, drawing mutates the shared tile in place
- Show unique-tile counter and current cell → tile mapping in the status bar

### Phase 3: Image list

- Image list panel: add/remove/rename named images
- Per-image dimensions set at create time (`width × height` ≤ 256)
- Validate dimensions on resize (reject >256 cells; warn if shrink would truncate data)
- Active image switch triggers preview refresh

### Phase 4: Project I/O + export

- `project_io.py` — extend JSON v2 with `tile_images` key; backward-compatible (load v1 projects with empty images)
- Export menu: ASM (`{name}_PATTERNS`, `{name}_COLORS`, `{name}_MAP`) and binary
- Preview window before save (reuse `export_preview.py` pattern)
- Dedupe tiles, build local tileset, remap layout indices
- Validate N ≤ 256 unique tiles at export time

### Phase 5: Polish

- Keyboard shortcuts (Help → Keyboard Shortcuts…)
- Live unique-tile counter with 256-limit enforcement
- Copy-on-write stops allocating once 256 unique tiles are in use
- `project.py` — `tile_images[]`, `TILE_IMAGE_CHANGED` event
- Help → About

## Verification

| Check | Method |
|-------|--------|
| `make test` | All 104+ tests pass |
| App launches | `python3 src/image_editor.py` runs without errors |
| Draw canvas | Painting a cell updates the mapped tileset tile |
| Export | Preview shows correct PATTERNS/COLORS/MAP |
| 256-tile limit | Rejects images exceeding budget |
| Live cascade | Tileset edits refresh image preview |
