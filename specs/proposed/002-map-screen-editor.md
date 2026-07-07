# 002: Map & Screen Editor

**Status:** Proposed
**Priority:** Medium (follow-on after tile image editor)
**Depends on:** Tile image editor (must be complete first)

## Context

The map/screen editor is the third app in the toolchain. It consumes graphics data from the project (tiles, metatiles, supertiles) and adds level-design authoring — placing supertiles on playfields and linking screens.

## Problem

The game needs a way to author level layouts: place supertile indices on playfield grids, define screen-to-screen transitions (doors, stairs), and export screen data the game can load.

## Goals

- Place supertile indices on a playfield grid (screen editor)
- Define screen connections (world editor)
- Export screen maps and world adjacency data
- Share project state with tile editor (same `Project` instance)
- Live composite preview using `composite.py` (64×64 supertile rendering)

## Non-goals

- Tile/metatile/supertile graphics authoring (that's the tile editor's job)
- Tile image composition (that's the tile image editor's job)
- Game logic, collision detection, or runtime behavior (handled by the game engine)

## Technical design

### Screen data

**Screen** — supertile grid for one playfield:

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | e.g., `SCREEN00` |
| `cells` | int[] | Supertile indices (row-major, dimensions TBD) |

Export label: `{screen_name}` (e.g., `SCREEN00`)

### World data

**World** — screen grid and adjacency:

| Field | Type | Notes |
|-------|------|-------|
| `width` | int | World grid width in screens |
| `height` | int | World grid height in screens |
| `cells` | int[] | Screen indices in world grid |
| `links` | array[] | Connection definitions (doors, stairs, edges) |

Export labels: `WORLD`, `LINKS`

### Link definition

| Field | Type | Notes |
|-------|------|-------|
| `from` | string | Source screen name |
| `to` | string | Destination screen name |
| `type` | string | Door, stairs, or edge |
| `position` | int | Position within source screen |

### UI

| Component | Description |
|-----------|-------------|
| **Screen editor window** | Supertile grid canvas, supertile picker, live composite preview |
| **World editor window** | World grid, screen placement, link management |
| **Shared** | `project.py` with `screens[]` and `world` key in JSON v3 |

### Shared modules

- `project.py` — extend with `screens[]` and `world` dict
- `project_io.py` — JSON v3 support, backward-compatible with v1/v2
- `composite.py` — supertile rendering (already exists)
- `metatile_picker.py` — reuse for supertile picker
- `theme.py` — add `MAP_EDITOR_WINDOW_BG` and `WORLD_EDITOR_WINDOW_BG`

## Phases

### Phase 1: Shell

- `map_editor.py` — app entry; loads project, opens screen + world windows
- `map_model.py` — screen/world data structs, validation
- `theme.py` — new tints for map editor windows
- Minimal windows with menu bar

### Phase 2: Screen editor

- Supertile picker (reuse `metatile_picker.py` pattern)
- Playfield grid with configurable dimensions
- Live composite preview via `composite.py`
- Supertile cell assignment (click cell → supertile picker → select index)

### Phase 3: World editor

- World grid: place screen indices
- Screen list: add/remove/rename screens
- Basic screen metadata (name, dimensions)
- World dimensions (width/height)

### Phase 4: Screen links

- Define connections (doors, stairs, edges)
- Link editor: source → destination → type
- Validate referential integrity (valid screen names)
- Export `LINKS` label

### Phase 5: Project I/O

- JSON v3 with `screens` and `world` keys
- Backward-compatible: map editor loads v1/v2 projects (empty screens/world)
- ASM export for screen grids and link tables
- Binary export for screen/world data

### Phase 6: Polish

- Keyboard shortcuts (Help → Keyboard Shortcuts…)
- Validation: block invalid supertile indices
- Live cascade: tile editor edits refresh supertile previews
- Help → About

## Verification

| Check | Method |
|-------|--------|
| `make test` | All tests pass (new tests for map_model, screen export, world links) |
| App launches | `python3 src/map_editor.py` runs without errors |
| Screen editor | Supertile grid renders live composite |
| World editor | Screen placement and link management work |
| Export | Preview shows SCREEN/WORLD/LINKS sections |
| Live cascade | Tileset changes refresh supertile previews |
