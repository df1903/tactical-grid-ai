# TacticalGrid

2D turn-based tactical game on a grid (sides A and B, one resource carried to the own base), used as an environment for BFS, DFS, UCS, A*, Beam Search, Minimax and alpha-beta pruning.

Project 1 of *Sistemas Inteligentes I* (UCALDAS). Team: Jorge Iván Garcia Torres, Daniel Felipe Franco Rincón. Delivery: 2026-10-21.

## Requirements
- [uv](https://docs.astral.sh/uv/) (it provisions Python 3.14)

## Usage
```bash
uv sync                          # install dependencies
uv run python -m tactical_grid   # run the app
uv run pytest                    # tests
uv run ruff check .              # lint
uv run ruff format --check .     # format check
uv run mypy src                  # types (strict)
```

## Layout
| Path | Content |
|---|---|
| `src/tactical_grid/domain/` | state, actions, successors, costs, game rules |
| `src/tactical_grid/scenario/` | JSON loading and atomic validation |
| `src/tactical_grid/algorithms/` | search, heuristics, Minimax, alpha-beta, utility |
| `src/tactical_grid/gui/` | graphical interface |
| `src/tactical_grid/experiments/` | metrics, verifier, minimal cases |
| `tests/` | automated tests |
| `scenarios/` | JSON scenarios (`apendice_a.json` is the official example) |
| `docs/` | assignment statement (`enunciado.md`), technical report, user manual |

## Status
Phase 0 (setup) done. Next: Phase 1 — model and scenario. See `.context/state/current.md` and `.context/project/roadmap.md`.
