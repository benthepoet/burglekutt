# AGENTS.md — burglekutt

Guidance for AI agents working on **burglekutt** — a TI-99/4A Zelda-like game authoring toolchain (Python + Tkinter).

## Context index

| Task | Read |
|------|------|
| Project architecture, conventions, code style | [`src/AGENTS.md`](src/AGENTS.md) |
| Writing or implementing a spec | [`specs/AGENTS.md`](specs/AGENTS.md) + numbered spec file |
| Completed specs | [`specs/complete/`](specs/complete/) |
| Proposed specs | [`specs/proposed/`](specs/proposed/) |
| PR workflow, repo rules, build | this file |

## Project overview

**burglekutt** — a desktop authoring toolchain for a TI-99/4A Zelda-like game. Three apps: tile editor (complete), tile image editor (next), map/screen editor (follow-on). Targets memory-reduced Graphics II (256 unique tiles, not 768).

## Repository layout

```
burglekutt/
├── AGENTS.md          # This hub (workflow, build, index)
├── src/               # Source code
│   ├── AGENTS.md      # Architecture, conventions, code style
│   └── *.py            # Source files
├── specs/             # Design specs
│   ├── AGENTS.md      # Spec authoring workflow
│   ├── complete/      # Implemented and merged specs
│   └── proposed/      # Design proposals awaiting implementation
├── tests/              # unittest suite
│   └── test_*.py
├── formats/            # Export format dialects
│   └── ti99_default/
├── LICENSE
└── README.md
```

## Build and verify

```bash
# Run all tests
make test

# Launch apps
python3 src/editor.py
python3 src/image_editor.py
python3 src/map_editor.py
```

Always run `make test` after making source changes.

## Specs

Numbered design specs live in `specs/`. See [`specs/AGENTS.md`](specs/AGENTS.md) for authoring workflow, dependency ordering, and which agent doc to update after a spec lands.

## Making changes safely

1. **All code changes go through a PR.** Work on a feature branch, open a PR targeting `master`, and merge there — never commit source or build changes directly to `master`. Documentation under `specs/` and updates to `AGENTS.md` files may land on `master` directly when the maintainer requests or approves them; everything under `src/` and the `Makefile` requires a PR.
2. **Read [`src/AGENTS.md`](src/AGENTS.md)** before touching unfamiliar areas. It documents architecture conventions, code structure, and the project's design constraints.
3. **Test with `make`** (or the equivalent build command) and review output for warnings, regressions, or unexpected errors.
4. **Avoid drive-by refactors** — keep diffs minimal and focused on the task. Touch only the files the task needs.
5. **Respect the project's constraints.** If the project has a memory/performance/budget limit, document it in `src/AGENTS.md` and guard against violations.
6. **Do not add build dependencies** without strong justification. Prefer standard tooling already present in the environment.
7. **Third-party modules:** If a file is managed externally (vendor code, generated code, or a file the maintainer explicitly says not to touch), note it in `src/AGENTS.md` and leave it alone.
8. **Uncommitted local changes** — If `git status` shows modifications you did not make in the current session, ask the maintainer before reverting or overwriting them. Treat them as intentional work-in-progress unless told otherwise.

### Where to record changes

| Topic | File |
|-------|------|
| Workflow, PR policy, context index | root `AGENTS.md` (this file) |
| Architecture, conventions, constraints | [`src/AGENTS.md`](src/AGENTS.md) |
| Spec process | [`specs/AGENTS.md`](specs/AGENTS.md) |
| Feature behavior | numbered spec under `specs/` |

### Commit conventions

```
type: concise subject line

Optional body.
```

Types: `fix:`, `feat:`, `refactor:`, `docs:`, `chore:`, `spec:`, `test:`, `style:`.

### Branch context

| Branch | Focus |
|--------|-------|
| `master` | Active integration |

Create feature branches from `master`. Use descriptive branch names (e.g. `tile-image-editor`, `fix-metatile-ref`).

### Pull requests (required for code)

Every code change must land on `master` via pull request. After implementing on a feature branch:

1. **Create a new branch** from `master` (never commit code directly on `master`).
2. **Open a PR targeting `master`** — this is the only path for `src/` and `Makefile` changes to reach integration.
3. Commit on the feature branch, push, and open the PR with `gh pr create --base master`.
4. **Keep the PR description current.** Whenever you push new commits that change scope, behavior, or verification steps, update the open PR body to match.

```bash
git checkout -b my-feature
git add ...
git commit -m "type: description"
git push -u origin my-feature
gh pr create --base master --head my-feature --title "..." --body "..."
# After follow-up commits:
gh pr edit <number> --body "..."
```

Use a descriptive branch name for the feature. If `gh` is unavailable, push the branch and provide the compare URL for `--base master`.
