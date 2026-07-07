# specs/AGENTS.md — Design spec workflow

Loaded progressively when working under `specs/`. See root [`AGENTS.md`](../AGENTS.md) for PR workflow and build rules.

## Spec files

Design specs live in two subdirectories:

- [`complete/`](complete/) — implemented and merged specs
- [`proposed/`](proposed/) — design proposals awaiting implementation

Each spec is the **source of truth** for the feature it describes. When a proposed spec is implemented, move it from `proposed/` to `complete/` and update its status header.

## Authoring rules

**When the maintainer approves a new spec:** immediately write the spec file under `specs/proposed/`, commit, and push to `master`. Do not wait for implementation.

**When the maintainer establishes a new workflow rule:** record it in root [`AGENTS.md`](../AGENTS.md), then commit and push to `master` in the same session.

**Spec dependencies:** when a spec lists prerequisites, implement and merge each prerequisite in its **own PR** before opening PRs for dependent specs.

## Implementation

Source changes for a spec go through a **feature-branch PR** targeting `master`. The spec document itself may land on `master` directly when approved; `src/` and `Makefile` changes never do.

## Updating agent docs after a spec

| What changed | Update |
|--------------|--------|
| Architecture, conventions, constraints | [`src/AGENTS.md`](../src/AGENTS.md) |
| PR workflow, repo policy, context index | root [`AGENTS.md`](../AGENTS.md) |
| Feature behavior and acceptance criteria | the numbered spec file |

## Migration

When a spec is implemented and merged:

1. Move the file from `proposed/` to `complete/`
2. Update its `**Status:**` line to `Complete` (follow existing patterns)
3. Update any cross-references in the moved file (other specs may reference it; update paths as needed)
4. Commit and push to `master`
